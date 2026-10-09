# Working on this repo

A binary-only F-Droid repository: app repos build and sign their own APKs and
attach them to GitHub releases; `scripts/sync_apps.py` pulls them in and
`.github/workflows/publish.yml` builds and signs the index and deploys it to
GitHub Pages. See README.md.

This file is an index; the detail is in `docs/`. Read the guide for the task
before starting it.

## Tasks

- **Adding an app**: [docs/onboarding-flutter-app.md](docs/onboarding-flutter-app.md).
  Covers the app repo's release workflow ([docs/templates/release.yml](docs/templates/release.yml)),
  signing, fastlane store text, and the `apps.yml` and `fdroid/metadata/` entries here.
- **Checking versions, tagging a missing release, verifying the published
  index, keeping the README's app list complete**:
  [docs/release-check.md](docs/release-check.md). It starts with pulling this
  repo and every app repo from GitHub; never check against a stale checkout.
- **Refreshing the repo, testing locally, the logo**: README.md, "Maintenance".

## Rules

Short form; the reasons are in [docs/agent-rules.md](docs/agent-rules.md).

- **Workflows**: an agent's GitHub token cannot write under `.github/workflows/`,
  here or in app repos. Stage workflow files elsewhere and give Paul the
  command to move them.
- **Keys**: never commit, print or regenerate a signing key (this repo's
  index key or an app's release key).
- **Releases**: only tag a version that is already in an app's code; never
  bump a version to have something to tag.
- Give Paul shell commands in fish syntax.
