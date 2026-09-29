<p align="center"><img src="logo.svg" width="160" alt="snonux F-Droid logo"></p>

# snonux F-Droid repository

A personal [F-Droid](https://f-droid.org) repository for my own Android apps,
served from GitHub Pages at <https://snonux.github.io/fdroid/repo>.

Nothing is built here. Each app builds and signs its own APKs and attaches them
to a GitHub release; a workflow in this repo downloads them, regenerates the
index with `fdroidserver`, signs the index with this repo's key and deploys the
result to Pages. The APKs keep their developer signature, so an app installed
from here can be updated from any other source that ships the same signed APKs
(the official F-Droid repo included, when it publishes reproducible builds).

## Add the repo on a phone

**[➕ Add to F-Droid](https://fdroid.link/#https://snonux.github.io/fdroid/repo?fingerprint=04B05FB0565543E058372B867B3D3A699D9D668388CE670478EDD4116D736DF7)**
(tap on the phone), or scan this with the phone's camera:

<img src="add-repo-qr.png" alt="QR code to add the repo to F-Droid" width="200">

To add it by hand, go to *Settings → Repositories → +* in the F-Droid app:

- Address: `https://snonux.github.io/fdroid/repo`
- Fingerprint: `04B05FB0565543E058372B867B3D3A699D9D668388CE670478EDD4116D736DF7`

The fingerprint belongs to the repo signing key. If that key is ever replaced,
update the link, the QR code (`add-repo-qr.png`) and the fingerprint here.

## Apps

APKs are published from the GitHub releases of these projects:

- [Quicklog](https://github.com/snonux/quicklog)
- [RESTForge](https://github.com/snonux/restforge)
- [ComicRedr](https://github.com/snonux/comicredr)
- [Player](https://github.com/snonux/player)

This list may be incomplete: the repo can carry more apps than are mentioned
here. [`apps.yml`](apps.yml) is the full list. To add one:

1. Make its release process attach signed APKs to a GitHub release.
2. Add an entry to `apps.yml` (id, GitHub repo, asset regex, fastlane path).
3. Add `fdroid/metadata/<applicationId>.yml` with License, SourceCode etc.
   Name, summary, description, icon, screenshots and changelogs come from the
   app repo's fastlane directory at the release tag.

For a Flutter app, [docs/onboarding-flutter-app.md](docs/onboarding-flutter-app.md)
walks through all of it, including a release workflow template, signing and
the store listing.

The workflow runs on every push, every six hours, on demand
(`gh workflow run publish.yml -R snonux/fdroid`) and on a `repository_dispatch`
of type `app-release`, so a new release shows up in F-Droid within six hours
without doing anything.

## One-time setup

### 1. Repo signing key

The key identifies this repository. Phones that added the repo only trust
indexes signed with it, so if it is lost, every phone has to remove and re-add
the repo. Keep an offline backup.

```sh
keytool -genkeypair -storetype PKCS12 -keystore fdroid-repo.p12 \
  -alias fdroid -keyalg RSA -keysize 4096 -validity 10000 \
  -dname "CN=snonux F-Droid, O=snonux"
```

`keytool` asks for a password; use the same one for the key if asked. Then store
both as Actions secrets:

```sh
base64 -w0 fdroid-repo.p12 | gh secret set FDROID_KEYSTORE -R snonux/fdroid
gh secret set FDROID_KEYSTORE_PASS -R snonux/fdroid   # prompts for the password
```

The alias must stay `fdroid` (see `repo_keyalias` in `fdroid/config.yml`).

### 2. GitHub Pages

*Settings → Pages → Build and deployment → Source: GitHub Actions.*

Then run the workflow once (`gh workflow run publish.yml -R snonux/fdroid`).

## Local run

```sh
python3 -m venv .venv && . .venv/bin/activate && pip install fdroidserver
python3 scripts/sync_apps.py
cp /path/to/fdroid-repo.p12 fdroid/keystore.p12
cd fdroid && FDROID_KEYSTORE_PASS=... fdroid update
```

`apksigner` must be on `PATH` or under `$ANDROID_HOME/build-tools`.

## Logo

`logo.svg` is the source. `fdroid/repo-icon.png` is its 512 px render used as
the repo icon in the F-Droid app (`repo_icon` in `fdroid/config.yml`); after
changing the SVG, re-render it, e.g. `cairosvg logo.svg -o fdroid/repo-icon.png -W 512 -H 512`.
