# Working on this repo

A binary-only F-Droid repository: app repos build and sign their own APKs and
attach them to GitHub releases; `scripts/sync_apps.py` pulls them in and
`.github/workflows/publish.yml` builds and signs the index and deploys it to
GitHub Pages. See README.md.

- **Adding an app**: follow [docs/onboarding-flutter-app.md](docs/onboarding-flutter-app.md).
  It covers the app repo's release workflow ([docs/templates/release.yml](docs/templates/release.yml)),
  signing, fastlane store text, and the `apps.yml` and `fdroid/metadata/` entries here.
- **Workflows**: an agent's GitHub token cannot write under `.github/workflows/`,
  here or in app repos. Stage workflow files elsewhere and give Paul the
  command to move them.
- **Keys**: never commit, print or regenerate a signing key (this repo's
  index key or an app's release key). The index key's fingerprint is in the
  README; replacing it forces every phone to re-add the repo.
- Give Paul shell commands in fish syntax.
