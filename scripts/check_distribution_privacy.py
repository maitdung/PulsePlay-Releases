#!/usr/bin/env python3
"""Fail closed on accidental source/debug/key packaging. Not anti-decompilation."""
import argparse
import json
import pathlib
import re
import struct
import zipfile

DENIED_SUFFIXES = {'.swift', '.m', '.mm', '.h', '.c', '.cpp', '.cc', '.hpp', '.pch',
                   '.swiftinterface', '.swiftmodule', '.swiftdoc', '.swiftsourceinfo',
                   '.o', '.a', '.d', '.map', '.p12', '.pfx', '.pem', '.key', '.xcconfig',
                   '.pbxproj', '.xcuserstate', '.log'}
DENIED_PARTS = {'.git', '.svn', '.ds_store', 'xcuserdata', 'headers', 'privateheaders',
                'modules', 'deriveddata', '__macosx'}
SECRETS = [
    ('private-key', re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----')),
    ('github-token', re.compile(rb'\bgh[pousr]_[A-Za-z0-9_]{36,}\b')),
    ('github-fine-grained-token', re.compile(rb'\bgithub_pat_[A-Za-z0-9_]{50,}\b')),
    ('aws-access-id', re.compile(rb'\bAKIA[A-Z0-9]{16}\b')),
]

def symbols(archive, info):
    with archive.open(info) as stream:
        header = stream.read(32)
        if header[:4] != b'\xcf\xfa\xed\xfe':
            return None
        count, size = struct.unpack_from('<II', header, 16)
        if size > 16 * 1024 * 1024 or size + 32 > info.file_size:
            raise ValueError('Invalid Mach-O commands')
        commands = stream.read(size)
        offset, table, dwarf = 0, None, False
        for _ in range(count):
            command, length = struct.unpack_from('<II', commands, offset)
            if length < 8 or offset + length > len(commands):
                raise ValueError('Invalid Mach-O load command')
            if command == 2:
                table = struct.unpack_from('<4I', commands, offset + 8)
            if command == 0x19 and commands[offset + 8:offset + 24].rstrip(b'\0') == b'__DWARF':
                dwarf = True
            offset += length
        debug, local, markers = 0, 0, 0
        if table:
            position, total, strings_at, strings_size = table
            if position + total * 16 > info.file_size or strings_at + strings_size > info.file_size or strings_size > 32 * 1024 * 1024:
                raise ValueError('Invalid symbol table')
            stream.seek(strings_at)
            strings = stream.read(strings_size)
            stream.seek(position)
            for _ in range(total):
                entry = stream.read(16)
                kind = entry[4]
                if kind & 0xe0:
                    name_index = struct.unpack_from('<I', entry)[0]
                    name = strings[name_index:].split(b'\0', 1)[0]
                    # Apple strip inserts this fixed N_OPT placeholder, not
                    # source/debug data (also documented by MobSF issue 1917).
                    if kind == 0x3c and name == b'radr://5614542' and struct.unpack_from('<Q', entry, 8)[0] == 0x5614542:
                        markers += 1
                    else:
                        debug += 1
                elif kind & 0x0e == 0x0e and not kind & 1:
                    local += 1
        return {'path': info.filename, 'debugSymbols': debug, 'localDefinedSymbols': local, 'dwarfSection': dwarf, 'appleStripMarkers': markers}

def inspect(ipa):
    issues, scripts, binaries = [], [], []
    with zipfile.ZipFile(ipa) as archive:
        if archive.testzip() is not None:
            raise ValueError('Invalid ZIP checksum')
        for info in archive.infolist():
            if info.is_dir():
                continue
            path = pathlib.PurePosixPath(info.filename)
            parts = [p.lower() for p in path.parts]
            if (path.suffix.lower() in DENIED_SUFFIXES or any(p in DENIED_PARTS or p.endswith('.dsym') for p in parts)
                    or path.name.lower() == '.env' or path.name.lower().startswith('.env.')):
                issues.append({'path': info.filename, 'kind': 'source-debug-or-private-material'})
            if path.suffix.lower() == '.js':
                scripts.append(info.filename)
            binary = symbols(archive, info)
            if binary:
                binaries.append(binary)
                if binary['debugSymbols'] or binary['localDefinedSymbols'] or binary['dwarfSection']:
                    issues.append({'path': info.filename, 'kind': 'unstripped-debug-or-local-symbols'})
            # Streaming scan covers executables as well as text resources. Never
            # print matching bytes or credentials into CI logs.
            with archive.open(info) as stream:
                tail = b''
                found = set()
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    block = tail + chunk
                    for name, pattern in SECRETS:
                        if name not in found and pattern.search(block):
                            issues.append({'path': info.filename, 'kind': name})
                            found.add(name)
                    tail = block[-1024:]
    return {'passed': not issues, 'issues': issues, 'binaries': binaries, 'runtimeScriptResources': scripts,
            'scope': 'Packaging checks only; compiled code and runtime resources remain extractable.'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ipa', type=pathlib.Path)
    args = parser.parse_args()
    report = inspect(args.ipa)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report['passed'] else 1)

if __name__ == '__main__':
    main()
