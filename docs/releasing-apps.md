# Releasing apps

How a new version of any app in [`apps.yml`](../apps.yml) gets from the app
repo to phones, and how its release tag is made, by Paul or by an agent.
Adding a new app is a separate job:
[onboarding-flutter-app.md](onboarding-flutter-app.md).

## The pipeline

1. **Version bump** in the app repo, committed to `main`: the version file
   (see the table below) and the "What's new" changelog in the app's fastlane
   directory.
2. **A `vX.Y.Z` tag** on that commit. Paul can push it, or the app's Release
   workflow creates it when started by hand ([Auto release
   tagging](#auto-release-tagging)).
3. **The app's Release workflow** checks the tag against the version file,
   builds the APKs with the app's release key, refuses debug-signed ones and
   attaches them to the GitHub release of the tag (creating the release with
   generated notes unless Paul wrote one).
4. **This repo's publish workflow** downloads the newest releases whose asset
   names match the app's `assets:` regex, plus the fastlane metadata at that
   tag, signs the index and deploys it. It runs every six hours, on every
   push here, on `gh workflow run publish.yml -R snonux/fdroid`, and right
   after a release when the app repo has the `FDROID_DISPATCH_TOKEN` secret.

A pushed or created tag is a release: it cannot be taken back cleanly once
phones have seen the version. Only tag a version that is already in the code
(see [agent-rules.md](agent-rules.md#releases)).

## The apps

| App | Repo | Version file | Tag | Release workflow |
| --- | --- | --- | --- | --- |
| Quicklog | snonux/quicklog | `pubspec.yaml` | `vX.Y.Z` | `release.yml`, reproducible build for official F-Droid |
| TurboNotes | snonux/turbonotes | `pubspec.yaml` | `vX.Y.Z` | `release.yml` |
| TurboLaunch | snonux/turbolaunch | `pubspec.yaml` | `vX.Y.Z` | `release.yml` |
| ComicRedr | snonux/comicredr | `pubspec.yaml` | `vX.Y.Z` | `release.yml` |
| RESTForge | snonux/restforge | `flutter/pubspec.yaml` | `vX.Y.Z` | `release.yml` |
| Player | snonux/player | `player-android/pubspec.yaml` | `vX.Y.Z` | `release.yml` |
| GunRunners | snonux/gunrunners | `CMakeLists.txt`, `project(Gunrunners VERSION X.Y.Z)` | `vX.Y.Z` | `release.yml`, not Flutter, one APK |
| File Browser | snonux/filebrowser | `filebrowser-android/pubspec.yaml` | `android-vX.Y.Z` | `android-release.yml` |

For a pubspec, the version is the part of `version:` before `+`; the build
number after `+` must grow with every release, or phones see no update.
Where the changelog goes and how it is named differs per app (per-ABI
version codes, or `default.txt`); the app's AGENTS.md or README says which.

File Browser's server is released by GoReleaser with `vX.Y.Z` tags in the
same repo, so the Android app uses `android-vX.Y.Z` and its workflow is
`android-release.yml`; use those names wherever this guide says `vX.Y.Z` and
`release.yml`. The F-Droid sync ignores server releases because their assets
do not match.

## Auto release tagging

Agent sessions (Claude Code in the cloud) can push commits to `main` but
their git proxy refuses tag pushes (HTTP 403), and their GitHub tools cannot
create tags. They can start workflows. So the Release workflow's manual run
creates the tag itself:

- `workflow_dispatch` takes a `tag` input, e.g. `v1.2.3` (`android-v1.2.3`
  for File Browser).
- **The tag exists**: the run rebuilds it, as before (e.g. after fixing a
  secret). It never moves a tag.
- **The tag does not exist**: the first step reads the version file at the
  commit the run was started on (the head of the chosen branch), stops with
  an error if it does not match the tag, and otherwise creates a lightweight
  tag on that commit with the workflow's own token (`contents: write`). The
  rest of the run builds and attaches the APKs as for a pushed tag.
- A tag created with the workflow's token does not start the tag-push
  trigger again, so there is exactly one build.

The step is called "Create the tag if it does not exist yet" and is in
[`templates/release.yml`](templates/release.yml). To check whether an app has
it (fish):

```fish
gh api repos/snonux/<repo>/contents/.github/workflows/release.yml -H 'Accept: application/vnd.github.raw' | grep -c 'Create the tag if it does not exist yet'
```

### Releasing as an agent

1. When Paul asks for a release (bumping is his call), bump the version
   file and write the changelog on an up-to-date `main`,
   run the app's own tests and analyzer, commit and push to `main`.
2. Start the Release workflow on `main` with the new tag: with the GitHub
   MCP `actions_run_trigger` (method `run_workflow`, workflow `release.yml`,
   ref `main`, inputs `{"tag": "vX.Y.Z"}`), or
   `gh workflow run release.yml -R snonux/<repo> --ref main -f tag=vX.Y.Z`.
3. Follow the run and confirm the APKs are on the release (commands in
   [release-check.md](release-check.md#2-tag-what-is-missing)).
4. To publish at once instead of within six hours, start
   `publish.yml` in snonux/fdroid the same way.

Start the run only after the bump commit is on `main`: the tag goes on the
branch head at the moment the run starts. If the app has no tag step yet,
the run fails at checkout ("couldn't find remote ref") without creating
anything; then Paul tags it (below).

### Releasing as Paul

Either the same command as step 2 above, or the classic way in the app
checkout (fish):

```fish
git tag vX.Y.Z; and git push; and git push origin vX.Y.Z
gh run watch
```

## When a release run fails

- **"Tag vX.Y.Z does not match version ..."**: on a manual run for a new
  tag, nothing was created; fix the version file or the tag name and start
  again. For a pushed tag, fix the version file, delete the tag locally and
  on GitHub, and tag again.
- **"The ANDROID_* signing secrets are not all set"**: Paul sets them from
  the app's `android/key.properties` (onboarding guide, step 6). Never print
  or commit key material.
- **Rebuild a tag after a fix**: start the workflow again with the same
  `tag`; it rebuilds and replaces the APKs.
