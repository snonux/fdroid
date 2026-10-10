# Rules for agents

The reasoning behind the short rules in [AGENTS.md](../AGENTS.md). They
apply to this repo and to every app repo it serves.

## Workflow files

An agent's GitHub token cannot write under `.github/workflows/`, here or in
app repos: a push that touches that directory is rejected. Write the workflow
file somewhere else in the repo (the onboarding guide uses
`docs/templates/`), commit that, and give Paul the command to move it into
place and push.

## Signing keys

Never commit, print or regenerate a signing key. There are two kinds:

- **This repo's index key** (Actions secrets `FDROID_KEYSTORE` and
  `FDROID_KEYSTORE_PASS`). Phones that added the repo trust only an index
  signed with it. Its fingerprint is in the README; replacing it forces every
  phone to remove and re-add the repo. `fdroid/keystore.p12` is git-ignored
  for local tests and must stay that way.
- **Each app's release key** (the `ANDROID_KEYSTORE*` secrets in the app
  repo). Android refuses to update an installed app with an APK signed by a
  different key, so a regenerated key strands every existing install.

Setting or rotating these secrets is Paul's job; an agent hands over the
commands and does not run them with real key material.

## Releases

Pushing a `vX.Y.Z` tag to an app repo publishes that version to phones.
An agent's git proxy refuses tag pushes, so an agent releases by starting
the app's release workflow with the new tag, which creates it
([releasing-apps.md](releasing-apps.md#auto-release-tagging)). Only
tag a version that is already in the app's code, as described in
[release-check.md](release-check.md); bumping a version is Paul's decision.

## Shell commands

Paul's shell is fish. Commands given to Paul, and commands written into the
docs here, use fish syntax (`set x (cmd)`, `; and`, `env VAR=... cmd`), not
bash.
