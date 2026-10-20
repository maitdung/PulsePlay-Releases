#!/usr/bin/env python3
"""Prepare release metadata locally; never signs, uploads or handles credentials."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import pathlib
import plistlib
import re
import shutil
import zipfile


def prepare(ipa, repo, tag, body, out, icon, published_at=None):
    spec = importlib.util.spec_from_file_location('privacy', pathlib.Path(__file__).with_name('check_distribution_privacy.py'))
    privacy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(privacy)
    report = privacy.inspect(ipa)
    if not report['passed']:
        raise ValueError('IPA privacy gate failed: ' + ', '.join(sorted({item['kind'] for item in report['issues']})))
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+", repo):
        raise ValueError("Invalid GitHub owner/repo")
    if not re.fullmatch(r"v[0-9.]+-build[0-9]+", tag):
        raise ValueError("Use release tag vVERSION-buildBUILD")
    base = "https://github.com/" + repo
    with zipfile.ZipFile(ipa) as archive:
        infos = [p for p in archive.namelist() if re.fullmatch(r"Payload/[^/]+\.app/Info.plist", p)]
        if len(infos) != 1:
            raise ValueError("IPA must contain one root application")
        info = plistlib.loads(archive.read(infos[0]))
        if archive.testzip() is not None:
            raise ValueError("IPA ZIP checksum failed")
    version, build = info["CFBundleShortVersionString"], info["CFBundleVersion"]
    if not re.fullmatch(r"\d+(\.\d+){0,3}", version) or not re.fullmatch(r"\d+", build):
        raise ValueError("Invalid application version/build")
    if tag != f"v{version}-build{build}":
        raise ValueError("Release tag must match the IPA version/build")
    bundle = info.get("PulsePlayReleaseBundleIdentifier", info["CFBundleIdentifier"])
    if bundle != "com.pulseplay.demo":
        raise ValueError("Only the stable PulsePlay bundle is accepted")
    feed_url = base + "/releases/latest/download/update.json"
    if info.get("PulsePlayUpdateFeedURL") != feed_url:
        raise ValueError("IPA does not contain this repository's permanent update feed")
    size = ipa.stat().st_size
    if not 4 < size <= 512 * 1024 * 1024:
        raise ValueError("IPA exceeds package size limit")
    if len(body) > 6000:
        raise ValueError("Release notes exceed 6000 characters")
    sections = {"highlights": [], "fixes": [], "improvements": []}
    names = {"tính năng mới": "highlights", "new features": "highlights", "sửa lỗi": "fixes",
             "fixes": "fixes", "cải thiện hiệu năng": "improvements", "improvements": "improvements"}
    current = None
    summary = []
    for line in body.splitlines():
        if line.startswith("## "):
            current = names.get(line[3:].strip().lower())
            if current is None:
                summary.append(line)
        elif current and line.startswith(("- ", "* ")):
            sections[current].append(line[2:].strip())
        elif line.strip():
            summary.append(line)
    if any(len(v) > 30 or any(len(line) > 1000 for line in v) for v in sections.values()):
        raise ValueError("Release-note section exceeds app limits")
    notes = "\n".join(summary).strip()
    name = f"PulsePlay-{version}-build{build}.ipa"
    download = base + f"/releases/download/{tag}/{name}"
    digest = hashlib.sha256()
    with ipa.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    checksum = digest.hexdigest()
    date = published_at or datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    minimum = info.get("MinimumOSVersion", "17.0")
    manifest = dict(schemaVersion=1, bundleIdentifier=bundle, version=version, build=build,
                    minimumOSVersion=minimum, releaseURL=base + "/releases/tag/" + tag,
                    downloadURL=download, sha256=checksum, downloadSize=size,
                    publishedAt=date, notes=notes, installation="sidestore", **sections)
    source = dict(name="PulsePlay", identifier=bundle + ".source",
                  sourceURL=base + "/releases/latest/download/altsource.json", tintColor="#7860D9",
                  apps=[dict(name="PulsePlay", bundleIdentifier=bundle, developerName="PulsePlay",
                             localizedDescription="Nhạc, playlist và phối nhạc của bạn.",
                             iconURL=base + f"/releases/download/{tag}/icon.png",
                             versions=[dict(version=version, buildVersion=build, date=date,
                                            localizedDescription=body, downloadURL=download, size=size,
                                            minOSVersion=minimum)],
                             appPermissions=dict(entitlements=[], privacy={k: v for k, v in info.items() if k.endswith("UsageDescription")}))], news=[])
    png = icon.read_bytes()
    if not png.startswith(b"\x89PNG\r\n\x1a\n") or png[12:16] == b"CgBI":
        raise ValueError("A web-compatible original PNG icon is required")
    out.mkdir(parents=True, exist_ok=True)
    for filename, value in [("update.json", manifest), ("altsource.json", source)]:
        (out / filename).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    (out / "SHA256SUMS.txt").write_text(checksum + "  " + name + "\n")
    (out / "icon.png").write_bytes(png)
    if ipa.resolve() != (out / name).resolve():
        shutil.copyfile(ipa, out / name)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ipa", required=True, type=pathlib.Path)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--notes-file", required=True, type=pathlib.Path)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    parser.add_argument("--icon", required=True, type=pathlib.Path)
    args = parser.parse_args()
    manifest = prepare(args.ipa, args.repo, args.tag, args.notes_file.read_text(), args.out, args.icon)
    print(json.dumps({"version": manifest["version"], "build": manifest["build"],
                      "feed": f"https://github.com/{args.repo}/releases/latest/download/update.json",
                      "published": False}, indent=2))


if __name__ == "__main__":
    main()
