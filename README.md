<p align="center"><img src="logo.svg" width="160" alt="snonux F-Droid logo"></p>

# snonux F-Droid repository

My own Android apps, installable and updatable through the
[F-Droid](https://f-droid.org) app, without sideloading APKs by hand.

Repository address: <https://snonux.github.io/fdroid/repo>

## Add it to your phone

**[➕ Add to F-Droid](https://fdroid.link/#https://snonux.github.io/fdroid/repo?fingerprint=04B05FB0565543E058372B867B3D3A699D9D668388CE670478EDD4116D736DF7)**
(tap this on the phone), or scan the QR code with the phone's camera:

<img src="add-repo-qr.png" alt="QR code to add the repo to F-Droid" width="200">

Or add it by hand in F-Droid under *Settings → Repositories → +*:

- Address: `https://snonux.github.io/fdroid/repo`
- Fingerprint: `04B05FB0565543E058372B867B3D3A699D9D668388CE670478EDD4116D736DF7`

The apps then show up in F-Droid like any other, and F-Droid offers updates
when a new version is released.

## Apps

- [Quicklog](https://github.com/snonux/quicklog)
- [TurboNotes](https://github.com/snonux/turbonotes)
- [RESTForge](https://github.com/snonux/restforge)
- [ComicRedr](https://github.com/snonux/comicredr)
- [Player](https://github.com/snonux/player)
- [TurboLaunch](https://github.com/snonux/turbolaunch)
- [Gunrunners](https://github.com/snonux/gunrunners)

More apps may be available than are listed here; [`apps.yml`](apps.yml) is
the complete list.

## How it works

Nothing is built in this repository.

1. Each app repo builds and signs its own APKs and attaches them to a GitHub
   release when a `vX.Y.Z` tag is pushed.
2. The [publish workflow](.github/workflows/publish.yml) here downloads the
   newest two releases of every app in `apps.yml`, together with each app's
   store text and screenshots (fastlane metadata) at that tag
   ([`scripts/sync_apps.py`](scripts/sync_apps.py)).
3. `fdroid update` builds the repository index and signs it with this
   repository's key, and the result is deployed to GitHub Pages.

The workflow runs on every push to `main`, every six hours, and on demand, so
a new app release reaches phones within six hours without any action here.

The APKs are served unchanged and keep their developer signature. So an app
installed from here can also be updated from any other source that ships the
same signed APKs, such as the official F-Droid repository.

## Add a new app

For a Flutter app, follow
[docs/onboarding-flutter-app.md](docs/onboarding-flutter-app.md). In short:

1. The app repo attaches signed APKs to its GitHub releases (a ready-made
   workflow is in [docs/templates/release.yml](docs/templates/release.yml)).
2. Add the app to [`apps.yml`](apps.yml).
3. Add `fdroid/metadata/<applicationId>.yml` with licence and links.
4. Add it to the list above.

## Maintenance

### Refresh the repository now

```fish
gh workflow run publish.yml -R snonux/fdroid
gh run watch -R snonux/fdroid
```

App repos can trigger the same refresh right after a release with a
`repository_dispatch` of type `app-release` (their release workflow does this
when the `FDROID_DISPATCH_TOKEN` secret is set).

### The repository signing key

The key identifies this repository: phones that added it only trust an index
signed with it. If it is lost or replaced, every phone has to remove and
re-add the repository, and the link, the QR code (`add-repo-qr.png`) and the
fingerprint above must be updated. Keep an offline backup.

It lives in two Actions secrets: `FDROID_KEYSTORE` (the base64 PKCS12 file,
key alias `fdroid`) and `FDROID_KEYSTORE_PASS`. This is how it was created,
for reference (only needed again if starting from scratch):

```fish
keytool -genkeypair -storetype PKCS12 -keystore fdroid-repo.p12 \
  -alias fdroid -keyalg RSA -keysize 4096 -validity 10000 \
  -dname "CN=snonux F-Droid, O=snonux"
base64 -w0 fdroid-repo.p12 | gh secret set FDROID_KEYSTORE -R snonux/fdroid
gh secret set FDROID_KEYSTORE_PASS -R snonux/fdroid   # prompts for the password
```

GitHub Pages is set to *Settings → Pages → Source: GitHub Actions*.

### Test locally

```fish
python3 -m venv .venv; and source .venv/bin/activate.fish; and pip install fdroidserver
python3 scripts/sync_apps.py
cp /path/to/fdroid-repo.p12 fdroid/keystore.p12
cd fdroid; and env FDROID_KEYSTORE_PASS=... fdroid update
```

`apksigner` must be on `PATH` or under `$ANDROID_HOME/build-tools`. Use a
throwaway keystore unless you mean to test with the real one
(`fdroid/keystore.p12` is git-ignored).

### Logo

`logo.svg` is the source. `fdroid/repo-icon.png` is its 512 px render, used
as the repository icon in F-Droid. After changing the SVG, re-render it:

```fish
cairosvg logo.svg -o fdroid/repo-icon.png -W 512 -H 512
```

## License

The scripts, workflow and docs in this repository are MIT licensed; see
[LICENSE](LICENSE). The apps it serves keep their own licenses.
