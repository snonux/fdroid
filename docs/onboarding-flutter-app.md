# Onboarding a Flutter app

How to publish another of Paul's Android Flutter apps through this
repository, the same way as Quicklog, ComicRedr, RESTForge and Player. Written
for Paul and for coding agents.

**Nothing is built in this repo.** The app repo builds and signs its own APKs
and attaches them to a GitHub release. This repo only downloads them and
publishes them. So most of the work happens in the app repo.

## Overview

| Step | Where | Who |
| --- | --- | --- |
| [1. Look at the app](#1-look-at-the-app-first) | app repo | agent |
| [2. Pick the version-code scheme](#2-pick-the-version-code-scheme) | app repo | agent |
| [3. Signing key](#3-the-signing-key) | Paul's machine | Paul (or agent with his OK) |
| [4. Release workflow](#4-the-release-workflow) | app repo | agent |
| [5. Store listing](#5-store-listing-fastlane) | app repo | agent |
| [6. Enable workflow, set secrets, first release](#6-hand-over-to-paul) | app repo | Paul |
| [7. Register the app](#7-register-the-app-here) | this repo | agent |
| [8. Check it](#8-check-it) | phone | Paul |

## What an agent can and cannot do

- An agent's GitHub token cannot write under `.github/workflows/`. Put the
  release workflow at `ci/workflows/release.yml` in the app repo; Paul moves
  it (step 6).
- Signing keys and secrets live on Paul's machine. An agent never overwrites
  or commits a key, never prints a password, and only creates a new key
  after Paul says yes.
- Give Paul shell commands in **fish** syntax.

## 1. Look at the app first

In the app repo, find:

- **applicationId**: `applicationId` in `android/app/build.gradle.kts`.
- **Where the Flutter project lives**: the directory with `pubspec.yaml`
  (the repo root, or e.g. `flutter/` in a monorepo). Called `APP_DIR` below.
- **Release signing**: whether `android/app/build.gradle.kts` reads
  `android/key.properties`. Quicklog, ComicRedr and RESTForge do, and fall back to the
  debug key without it. If the app has no such block, add the standard one
  (see Quicklog's `android/app/build.gradle.kts`).
- **An existing release key**: `android/key.properties` on Paul's machine, and
  the keystore it points at. If none exists, every build so far was
  debug-signed (`CN=Android Debug`).
- **How it was released so far**: GitHub releases with APKs or not, split
  per ABI or not, and whether the app is on Paul's phone already.
- **The licence**, for the metadata file.

## 2. Pick the version-code scheme

F-Droid serves the highest `versionCode` a phone can install, so codes must
grow with every release and must never drop below what is installed.

| Scheme | Used by | When |
| --- | --- | --- |
| Flutter's default for `--split-per-abi`: `abi * 1000 + build` (armeabi-v7a 1, arm64-v8a 2, x86_64 4) | RESTForge | Default for a new app. Nothing to configure. |
| `build * 10 + abi` via an `applicationVariants` block | Quicklog | The app is also submitted to official F-Droid, which asked for this scheme. |
| Plain build number, single ABI, no split | ComicRedr | The app already shipped a single APK and should stay that way. |

Do not switch an app that is already installed to a scheme that yields lower
codes, or the phone cannot update.

## 3. The signing key

The key is the app's identity: an APK signed with another key cannot update
the installed app, and a lost key means users must uninstall and reinstall.

- **A key exists**: use it as it is.
- **No key exists** (typical: all builds so far were debug-signed): with
  Paul's OK, create one outside the repo, e.g.
  ```fish
  mkdir -p ~/.config/<app>
  set pw (openssl rand -hex 16)
  keytool -genkeypair -noprompt -keystore ~/.config/<app>/release.jks -storetype PKCS12 \
    -alias <app> -keyalg RSA -keysize 4096 -validity 36500 \
    -dname "CN=<App name>" -storepass $pw -keypass $pw
  printf 'storeFile=%s\nstorePassword=%s\nkeyAlias=<app>\nkeyPassword=%s\n' \
    ~/.config/<app>/release.jks $pw $pw > <APP_DIR>/android/key.properties
  chmod 600 ~/.config/<app>/release.jks <APP_DIR>/android/key.properties
  ```
  A debug-signed copy on the phone then has to be uninstalled once (it loses
  its data) before the F-Droid version installs. Say so to Paul.
- **Back up** the keystore and `key.properties` in `~/.foostore-export/`,
  next to Quicklog's key.
- Check that `.gitignore` covers `key.properties`, `*.jks` and `*.keystore`.

## 4. The release workflow

Copy [`templates/release.yml`](templates/release.yml) to
`ci/workflows/release.yml` in the app repo and fill in `APP_NAME`,
`APP_DIR` and `FLUTTER_VERSION` (or add a `.flutter-version` file to
`APP_DIR`). On a `vX.Y.Z` tag it:

1. checks the tag against `version:` in `pubspec.yaml`,
2. restores the key from secrets into `android/key.properties`,
3. runs `flutter build apk --release --split-per-abi`,
4. fails if an APK is debug-signed,
5. uploads `<APP_NAME>-vX.Y.Z-<abi>.apk` to the release (creating it with
   generated notes if Paul has not written one),
6. pings this repo when `FDROID_DISPATCH_TOKEN` is set.

Adapt the build step if the app keeps a single APK (ComicRedr runs its
`make apk`) or needs a reproducible build for official F-Droid (Quicklog
builds from `/tmp/build` against `/opt/android-sdk`; see its AGENTS.md).
Check the result with `actionlint`.

## 5. Store listing (fastlane)

In `<APP_DIR>/fastlane/metadata/android/en-US/`:

| File | Content |
| --- | --- |
| `title.txt` | App name |
| `short_description.txt` | At most 80 characters, no trailing period |
| `full_description.txt` | Plain text, `*` bullets are fine |
| `images/icon.png` | 512x512 PNG |
| `images/phoneScreenshots/1.png`, `2.png`, ... | PNG or JPEG only (fdroidserver 2.4.5 ignores WebP) |
| `changelogs/<versionCode>.txt` or `changelogs/default.txt` | "What's new", at most 500 characters |

F-Droid reads the changelog named after the APK's versionCode, falling back
to `default.txt`. With per-ABI splits that is one file per ABI code (Quicklog
writes three), so for the Flutter default scheme `default.txt`, rewritten
before each tag, is simpler (RESTForge does this).

Document the release steps in the app's README or AGENTS.md: bump the
version, write the changelog, tag, push, and the secrets list.

## 6. Hand over to Paul

Open a PR in the app repo with the workflow, fastlane and docs. After it is
merged, Paul runs in the app checkout (fish):

```fish
git checkout main; and git pull
mkdir -p .github/workflows; and git mv ci/workflows/release.yml .github/workflows/
git commit -m "Enable release workflow"; and git push

function get; sed -n "s/^$argv[1]=//p" <APP_DIR>/android/key.properties; end
base64 -w0 (get storeFile) | gh secret set ANDROID_KEYSTORE
gh secret set ANDROID_KEY_ALIAS --body (get keyAlias)
gh secret set ANDROID_KEYSTORE_PASSWORD --body (get storePassword)
gh secret set ANDROID_KEY_PASSWORD --body (get keyPassword)
gh secret list
```

(A relative `storeFile` resolves against `<APP_DIR>/android/app/`.)
Optionally, `gh secret set FDROID_DISPATCH_TOKEN` with a fine-grained token
that has *Contents: read and write* on snonux/fdroid, so a release shows up
at once instead of within six hours.

Then the first release: bump `version:` in `pubspec.yaml` (semver and the
`+N` build number), write the changelog, commit, `git tag vX.Y.Z; and git
push; and git push --tags`, then `gh run watch` to follow the build.

## 7. Register the app here

In this repo, push to main (it is safe before the first release: an app with
no matching release is skipped with a warning):

`apps.yml`:
```yaml
  - id: <applicationId>
    github: snonux/<repo>
    assets: '^<APP_NAME>-.*\.apk$'
    fastlane: <APP_DIR>/fastlane/metadata/android   # without "./" at the root
```

`fdroid/metadata/<applicationId>.yml`:
```yaml
# Store text, icon, screenshots and changelogs come from the app repo's
# fastlane/ dir, synced into metadata/<applicationId>/ by scripts/sync_apps.py.
Categories:
  - <an F-Droid category, e.g. Development, Internet, Reading, Writing>
License: <SPDX id, e.g. MIT or Apache-2.0>
AuthorName: Paul Buetow
AuthorWebSite: https://foo.zone
SourceCode: https://github.com/snonux/<repo>
IssueTracker: https://github.com/snonux/<repo>/issues
Changelog: https://github.com/snonux/<repo>/releases

AutoName: <App name>
```

Also add the app to the list under "Apps" in the README.

## 8. Check it

- After the app's release run: `gh release view vX.Y.Z -R snonux/<repo>`
  lists the APKs.
- `gh workflow run publish.yml -R snonux/fdroid`, then `gh run watch`. The
  "Fetch APKs" step logs `downloading ...` for the app, not `skipping`.
- Before pushing, a dry run works locally: `python scripts/sync_apps.py`,
  then `fdroid update` in `fdroid/` with a throwaway `keystore.p12` (see
  "Local run" in the README).
- On the phone: refresh the repo in F-Droid and install.
