# Release check: versions, missing tags, published index

How to answer "is every app released and published at its latest version?"
and fix it when the answer is no. Pull everything first, then: compare each
app's version in code with its newest tag, tag what is missing, confirm the
published index serves the newest tag of every app, and check that the README
lists every app.

The app list is [`apps.yml`](../apps.yml); the app repos are checked out
under `~/git/<repo>`. Commands are fish.

## 0. Pull the latest state from GitHub

Always do this first. A stale checkout shows an old `apps.yml` here (apps get
added by pull request) or an old version and missing tags in an app repo, and
every later step then gives a wrong answer.

```fish
git -C ~/git/fdroid pull --ff-only
for r in quicklog turbonotes comicredr restforge player turbolaunch turbomon gunrunners
    git -C ~/git/$r fetch --quiet --tags --prune origin
    git -C ~/git/$r pull --quiet --ff-only; or echo "$r: not fast-forwarded (dirty, diverged or on a feature branch)"
end
```

The repo names in the loop are the `github:` values in the freshly pulled
`apps.yml`; add any app that is new there (clone it to `~/git/<repo>` if it is
not checked out yet).

An app checkout that cannot be fast-forwarded is not a problem and not to be
"fixed": it holds Paul's uncommitted work or a feature branch. The `fetch`
has still updated `origin/main` and the tags, which is all the steps below
read.

## 1. Compare the version in code with the newest tag

Where each app keeps its version:

| App repo | Version lives in |
|---|---|
| quicklog, turbonotes, comicredr, turbolaunch, turbomon | `pubspec.yaml` (`version: X.Y.Z+N`) |
| restforge | `flutter/pubspec.yaml` |
| player | `player-android/pubspec.yaml` |
| gunrunners | `CMakeLists.txt` (`project(Gunrunners VERSION X.Y.Z ...)`) |

For a Flutter app the pubspec sits next to the `fastlane:` dir named in
`apps.yml`. Add a row here when onboarding an app that keeps it elsewhere.

Always read `origin/main`, not the working tree and not `origin/HEAD`: a
checkout can be dirty or on a feature branch, and a repo's default branch is
not always `main` (gunrunners' is a leftover `claude/...` branch).

```fish
for r in quicklog turbonotes comicredr restforge player turbolaunch turbomon gunrunners
    set tag (git -C ~/git/$r tag --sort=-v:refname | head -1)
    set code (git -C ~/git/$r grep -hE '^version:|^project\(.* VERSION ' origin/main -- \
        pubspec.yaml flutter/pubspec.yaml player-android/pubspec.yaml CMakeLists.txt)
    echo "$r: tag $tag, "(git -C ~/git/$r rev-list --count $tag..origin/main)" commits since; code: $code"
end
```

Read the result like this:

- **Code version equals the newest tag**: nothing to tag, even if there are
  commits since the tag. Those are unreleased work; releasing them needs a
  version bump first, which is Paul's call, not a missing tag.
- **Code version is higher than the newest tag**: a tag is missing (step 2).
- **Code version is lower than the newest tag**: something is wrong; stop and
  ask.

## 2. Tag what is missing

Tag the commit on `origin/main` that carries the bumped version (normally its
head; check with `git log -3 origin/main -- <version file>` that nothing
unrelated was pushed after the bump that should not ship). The existing tags
are lightweight `vX.Y.Z` tags, so keep to that:

```fish
git -C ~/git/<repo> tag vX.Y.Z <sha>
git -C ~/git/<repo> push origin vX.Y.Z
```

An agent cannot push tags. When the version bump is the head of
`origin/main`, it starts the release workflow instead, which creates the tag
on that head ([Auto release tagging](releasing-apps.md#auto-release-tagging)):

```fish
gh workflow run release.yml -R snonux/<repo> --ref main -f tag=vX.Y.Z
```

If commits that should not ship came after the bump, the workflow cannot
tag the older commit; ask Paul to tag `<sha>` by hand.

Creating the tag is the release: every app repo's `release.yml` builds the
signed APKs for a new `v*` tag and attaches them to the GitHub release. It
cannot be taken back cleanly once phones have seen the version, so only tag a
version that is already in the code; never bump a version just to have
something to tag.

Watch the build and confirm the APKs are attached:

```fish
gh run watch -R snonux/<repo> (gh run list -R snonux/<repo> --workflow release.yml --limit 1 --json databaseId --jq '.[0].databaseId')
gh release view vX.Y.Z -R snonux/<repo> --json assets --jq '.assets[].name'
```

The asset names must match the app's `assets:` regex in `apps.yml`, or the
sync skips the release without failing.

## 3. Confirm the index serves the newest tag

The publish workflow runs every six hours. An app repo triggers it right
after a release only if it has the `FDROID_DISPATCH_TOKEN` secret, so after
tagging, trigger it by hand rather than wait:

```fish
gh workflow run publish.yml -R snonux/fdroid
gh run watch -R snonux/fdroid (gh run list -R snonux/fdroid --workflow publish.yml --limit 1 --json databaseId --jq '.[0].databaseId')
```

Then list what the live index actually serves, newest first per app:

```fish
curl -sL https://snonux.github.io/fdroid/repo/index-v2.json | jq -r '
  .packages | to_entries[] | .key as $id
  | .value.versions | [.[] | .manifest.versionName] | unique
  | sort_by(split(".") | map(tonumber)) | reverse
  | "\($id): \(join(", "))"'
```

Every app in `apps.yml` must appear, and its first version must equal the
newest tag from step 1. `keep_releases` older versions next to it are
expected. If an app is missing or behind:

- Read the "Fetch APKs and store metadata" step of the publish run
  (`gh run view <id> -R snonux/fdroid --log`): it prints the releases it
  picked per app, and a warning when none of a release's assets match.
- A release that is a draft or prerelease is skipped by design.
- GitHub Pages can lag a minute behind a finished deploy; re-run the `curl`
  before digging further.

## 4. Keep the README's app list complete

The "Apps" list in [README.md](../README.md) must name every app in
`apps.yml`, no more and no fewer. This prints the repos that are in one but
not the other; no output means the list is complete (run it in this repo's
root):

```fish
set wanted (grep -oP '^\s+github: snonux/\K\S+' apps.yml)
set listed (sed -n '/^## Apps/,/^## /p' README.md | grep -oP 'github\.com/snonux/\K[^)]+')
for r in $wanted; contains $r $listed; or echo "missing in README: $r"; end
for r in $listed; contains $r $wanted; or echo "in README but not in apps.yml: $r"; end
```

Add a missing app as `- [<App name>](https://github.com/snonux/<repo>)`,
using the `AutoName` from its `fdroid/metadata/<applicationId>.yml`, and
remove an entry whose app is gone from `apps.yml`.
