#!/usr/bin/env python3
"""GitHub runner helper: an IPA drop creates a release without publishing app source."""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import plistlib
import re
import subprocess
import tempfile
import zipfile


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def inspect(path):
    with zipfile.ZipFile(path) as archive:
        roots = [n for n in archive.namelist() if re.fullmatch(r"Payload/[^/]+\.app/Info.plist", n)]
        if len(roots) != 1:
            raise ValueError("IPA must contain one app")
        # Source and debug archives are not release artifacts.
        if any(n.lower().endswith((".swift", ".m", ".mm", ".h", ".p12", ".pem", ".key")) or ".dsym/" in n.lower()
               for n in archive.namelist()):
            raise ValueError("Refusing a package containing source/debug/private-key files")
        info = plistlib.loads(archive.read(roots[0]))
    version, build = info["CFBundleShortVersionString"], info["CFBundleVersion"]
    if info["CFBundleIdentifier"] != "com.pulseplay.demo":
        raise ValueError("Use the stable distribution IPA")
    if not re.fullmatch(r"\d+(\.\d+){0,3}", version) or not re.fullmatch(r"\d+", build):
        raise ValueError("Invalid version/build")
    version_key = tuple(map(int, version.split(".")))
    return info, (version_key + (0,) * (4 - len(version_key)), int(build))


def choose(folder):
    paths = sorted(folder.glob("*.ipa"))
    if not paths:
        raise ValueError("Upload an IPA into incoming/")
    candidates = [(inspect(p)[1], p) for p in paths]
    best = max(key for key, _ in candidates)
    newest = [p for key, p in candidates if key == best]
    if len({digest(p) for p in newest}) != 1:
        raise ValueError("Different IPA files have the same version/build; increase the build")
    return newest[0]


class GitHub:
    def __init__(self, repo):
        self.repo = repo

    def run(self, *args):
        result = subprocess.run(["gh", *args], text=True, capture_output=True)
        if result.returncode:
            raise RuntimeError(result.stderr[:1500])
        return result.stdout

    def api(self, endpoint, missing=False):
        try:
            return json.loads(self.run("api", f"repos/{self.repo}/{endpoint}"))
        except RuntimeError as error:
            if missing and "HTTP 404" in str(error):
                return None
            raise

    def icon(self, release, destination):
        icons = [a for a in release["assets"] if a["name"] == "icon.png"]
        if not icons:
            raise ValueError("The current release must have icon.png")
        asset_id = int(icons[0]["id"])
        with destination.open("wb") as stream:
            subprocess.run(["gh", "api", f"repos/{self.repo}/releases/assets/{asset_id}",
                            "-H", "Accept: application/octet-stream"], stdout=stream, check=True)


def publish(folder, repo, client, dry_run=False):
    if not re.fullmatch(r"[A-Za-z0-9-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError("Invalid repository")
    ipa = choose(folder)
    info, key = inspect(ipa)
    version, build = info["CFBundleShortVersionString"], info["CFBundleVersion"]
    tag = f"v{version}-build{build}"
    sha = digest(ipa)
    latest = client.api("releases/latest")
    existing = client.api("releases/tags/" + tag, missing=True)
    name = f"PulsePlay-{version}-build{build}.ipa"
    if existing:
        binaries = [a for a in existing["assets"] if a["name"] == name]
        if binaries and binaries[0].get("digest") != "sha256:" + sha:
            raise ValueError("This build already exists with different or unverifiable contents; increase the build")
        metadata = {a["name"] for a in existing["assets"]}
        if binaries and not existing["draft"] and {"update.json", "altsource.json", "icon.png", "SHA256SUMS.txt"} <= metadata:
            return {"status": "already-published", "tag": tag}
    match = re.fullmatch(r"v(\d+(?:\.\d+){0,3})-build(\d+)", latest["tag_name"])
    if not match:
        raise ValueError("Current release tag is invalid")
    parts = tuple(map(int, match[1].split(".")))
    previous = (parts + (0,) * (4 - len(parts)), int(match[2]))
    if key <= previous:
        raise ValueError("Use a version/build newer than the current release")
    notes_file = folder / (tag + ".md")
    body = notes_file.read_text() if notes_file.exists() else (
        f"PulsePlay {version} · Build {build}\n\nBản cập nhật mới. Bản phát hành này chưa có ghi chú thay đổi chi tiết.")
    spec = importlib.util.spec_from_file_location('privacy', pathlib.Path(__file__).with_name('check_distribution_privacy.py'))
    privacy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(privacy)
    report = privacy.inspect(ipa)
    if not report['passed']:
        raise ValueError('IPA privacy gate failed: ' + ', '.join(sorted({item['kind'] for item in report['issues']})))
    if dry_run:
        return {"status": "ready", "tag": tag, "ipa": ipa.name, "notes": notes_file.name if notes_file.exists() else None}
    spec = importlib.util.spec_from_file_location("feed", pathlib.Path(__file__).with_name("github_release_feed.py"))
    feed = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(feed)
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        icon = root / "icon.png"
        client.icon(latest, icon)
        output = root / "release"
        feed.prepare(ipa, repo, tag, body, output, icon)
        notes = root / "notes.md"
        notes.write_text(body)
        if existing is None:
            client.run("release", "create", tag, "--repo", repo, "--draft", "--target", "main",
                       "--title", f"PulsePlay {version} · Build {build}", "--notes-file", str(notes))
        else:
            client.run("release", "edit", tag, "--repo", repo, "--notes-file", str(notes))
        assets = [str(output / n) for n in [name, "update.json", "altsource.json", "icon.png", "SHA256SUMS.txt"]]
        client.run("release", "upload", tag, *assets, "--repo", repo, "--clobber")
        client.run("release", "edit", tag, "--repo", repo, "--draft=false", "--latest")
    actual = client.api("releases/latest")
    if actual["tag_name"] != tag or actual["draft"]:
        raise ValueError("Release did not become the published latest version")
    return {"status": "published", "tag": tag, "url": actual.get("html_url")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--folder", type=pathlib.Path, default=pathlib.Path("incoming"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(publish(args.folder, args.repo, GitHub(args.repo), args.dry_run), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
