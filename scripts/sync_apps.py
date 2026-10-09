#!/usr/bin/env python3
"""Fill fdroid/repo and fdroid/metadata from the apps listed in apps.yml.

For every app, the newest `keep` published GitHub releases that carry matching
APK assets are downloaded into fdroid/repo/, and the fastlane store metadata at
the newest of those tags is copied to fdroid/metadata/<id>/. APKs in
fdroid/repo/ that no longer belong to a kept release are deleted, so running
`fdroid update` afterwards yields exactly the wanted set.

Uses GITHUB_TOKEN (or GH_TOKEN) when set, which is required for private app
repos and avoids the anonymous API rate limit.
"""

import io
import json
import os
import re
import shutil
import tarfile
import urllib.error
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REPO_DIR = ROOT / "fdroid" / "repo"
METADATA_DIR = ROOT / "fdroid" / "metadata"
API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


def request(url, accept="application/vnd.github+json"):
    headers = {"Accept": accept, "X-GitHub-Api-Version": "2022-11-28"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers))


def api_json(path):
    with request(f"{API}{path}") as resp:
        return json.load(resp)


def download(url, dest, accept):
    tmp = dest.with_suffix(dest.suffix + ".part")
    with request(url, accept) as resp, open(tmp, "wb") as out:
        shutil.copyfileobj(resp, out)
    tmp.rename(dest)


def wanted_releases(app, keep):
    pattern = re.compile(app["assets"])
    releases = api_json(f"/repos/{app['github']}/releases?per_page=30")
    picked = []
    for rel in releases:
        if rel["draft"] or rel["prerelease"]:
            continue
        assets = [a for a in rel["assets"] if pattern.search(a["name"])]
        if assets:
            picked.append((rel["tag_name"], assets))
        if len(picked) == keep:
            break
    return picked


def sync_apks(app, releases):
    """Download missing APKs; return the set of file names that should exist."""
    wanted = set()
    for tag, assets in releases:
        for asset in assets:
            name = f"{app['id']}_{tag}_{asset['name']}"
            wanted.add(name)
            dest = REPO_DIR / name
            if dest.exists() and dest.stat().st_size == asset["size"]:
                continue
            print(f"  downloading {tag}/{asset['name']}")
            download(asset["url"], dest, "application/octet-stream")
    return wanted


def sync_fastlane(app, tag):
    """Copy <fastlane>/<locale>/... at `tag` to fdroid/metadata/<id>/<locale>/."""
    prefix = app["fastlane"].strip("/") + "/"
    target = METADATA_DIR / app["id"]
    with request(f"{API}/repos/{app['github']}/tarball/{tag}") as resp:
        data = io.BytesIO(resp.read())
    shutil.rmtree(target, ignore_errors=True)
    copied = 0
    with tarfile.open(fileobj=data, mode="r:gz") as tar:
        for member in tar.getmembers():
            # Tarball entries are "<owner>-<repo>-<sha>/<path>".
            _, _, path = member.name.partition("/")
            if not member.isfile() or not path.startswith(prefix):
                continue
            rel = Path(path[len(prefix):])
            if ".." in rel.parts:
                continue
            dest = target / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            with tar.extractfile(member) as src, open(dest, "wb") as out:
                shutil.copyfileobj(src, out)
            copied += 1
    print(f"  metadata: {copied} files from {tag}:{prefix}")


def main():
    config = yaml.safe_load((ROOT / "apps.yml").read_text())
    default_keep = int(config.get("keep_releases", 2))
    REPO_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    wanted = set()
    for app in config["apps"]:
        print(f"{app['id']} <- {app['github']}")
        try:
            releases = wanted_releases(app, int(app.get("keep", default_keep)))
        except urllib.error.HTTPError as err:
            # A repo this token cannot read (private, renamed, deleted): keep
            # what is already published for the app and update the others.
            print(f"::warning::{app['github']}: releases not readable "
                  f"(HTTP {err.code}); keeping its published APKs")
            wanted |= {apk.name for apk in REPO_DIR.glob(f"{app['id']}_*.apk")}
            continue
        if not releases:
            # A newly listed app before its first release with APKs: skip it
            # rather than hold back every other app's update.
            print(f"  warning: no release of {app['github']} has assets "
                  f"matching {app['assets']!r}; skipping")
            continue
        print(f"  releases: {', '.join(tag for tag, _ in releases)}")
        wanted |= sync_apks(app, releases)
        if app.get("fastlane"):
            sync_fastlane(app, releases[0][0])

    for apk in REPO_DIR.glob("*.apk"):
        if apk.name not in wanted:
            print(f"removing {apk.name}")
            apk.unlink()


if __name__ == "__main__":
    main()
