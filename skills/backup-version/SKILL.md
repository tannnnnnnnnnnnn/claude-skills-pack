---
name: backup-version
description: >
  Cut a known-good, revertible version snapshot of a working project — an
  annotated git tag plus a self-contained backup folder (code archive, config,
  secrets, README) whose restore path has been verified by actually running it.
  Use when the user says "make a backup", "back this up", "save this version",
  "tag this", "checkpoint this version", "backup 2/3/N", or reaches a milestone
  worth being able to revert to. NOT for saving in-flight task state — that is
  /lifeboat.
---

# Version backup

Produces two artifacts that work independently:

1. **An annotated git tag** — the normal revert path, lives in the repo.
2. **A backup folder outside the repo** — disaster recovery for when the repo
   or tag is lost, and the only place secrets are kept.

Either alone is insufficient. The tag has no `.env`; the folder has no history.

## Preconditions — check before tagging anything

A backup means "this state is known good." Establish that; do not assume it.

- Run the test suite. Record the exact count. If tests fail, stop and tell the
  user — do not tag a red tree and call it a revert point.
- `git status` — know what is uncommitted. Ask whether pending changes belong
  in the tag before committing anything on the user's behalf.
- Confirm what actually works, from live evidence where the project has a
  running component (logs, status CLI, real output), not from what the code
  looks like it should do.

## 1. Name it

`v<N>.<M>-<what-works>` — the suffix names the capability, not the date.
`v2.0-three-pair-5x-g2b-armed`, not `v2.0-backup` or `v2.0-2026-07-27`.
A future reader picks a revert point by what it does; dates are already in git.

Check existing tags (`git tag -l`) and prior backup folders to continue the
series rather than starting a parallel one.

## 2. Annotated tag

```bash
git tag -a <tag> -F - <<'EOF'
<tag> — <Nth> known-good revert point

Supersedes <prior tag>. <Prior tag> is still valid; THIS is the one to revert
to for current behaviour, because <what materially differs>.

WHAT WORKS AT THIS TAG
  - <capability, with concrete numbers from live evidence>
  - <N> tests pass.

WHAT CHANGED SINCE <prior tag>
  - <change, with commit sha where useful>

KNOWN LIMITATIONS AT THIS TAG (carried, not bugs to re-diagnose)
  - <thing that looks broken but is understood, and why>
EOF
```

The limitations section is the highest-value part. It is what stops a future
session burning hours re-diagnosing a known quirk. Write down anything that
looks like a bug but isn't, with the reason.

## 3. Backup folder

Location: `~/Desktop/Backups/<project>-backups/<tag>/`

```bash
SRC=<repo path>
DST=~/Desktop/Backups/<project>-backups/<tag>
mkdir -p "$DST"
cd "$SRC"
git archive --format=tar.gz -o "$DST/code-<vN>.tar.gz" <tag>
cp config.yaml "$DST/config.yaml"      # or whatever the project's config is
cp .env "$DST/env.backup"              # secrets: cp only, NEVER cat
chmod 700 "$DST" && chmod 600 "$DST"/*
```

Include: code archive, config, secrets, README.
Exclude: databases, ledgers, accumulated history — those are data, not "the
project". Say in the README that they were excluded and how to back them up.

## 4. Verify the restore path by running it

Do not write restore instructions you have not executed. Extract to a throwaway
directory, copy in the secrets and config exactly as the README tells the user
to, run the tests there, then delete the throwaway.

```bash
TMP=<scratchpad>/restore-test
rm -rf "$TMP" && mkdir -p "$TMP"
tar -xzf "$DST/code-<vN>.tar.gz" -C "$TMP"
cp "$DST/env.backup" "$TMP/.env"
cp "$DST/config.yaml" "$TMP/config.yaml"
cd "$TMP" && <test command>          # must match the count from step 0
rm -rf "$TMP"
```

Report the verified count. "226 passed from a clean extract" is the claim worth
making; "should work" is not.

## 5. README.txt in the folder

Sections, in order:

- Tag name, creation date, commit sha, repo path, what it supersedes.
- **WHAT'S HERE** — every file, one line each, and for the secrets file an
  explicit list of which credential names it holds plus "never commit this".
- **WHY THIS BACKUP EXISTS** — the milestone in concrete terms, and the
  verified test count.
- **STATE OF THE CONFIG** — the handful of settings that define behaviour at
  this version, so a reader sees the difference from the prior tag at a glance.
- **KNOWN LIMITATIONS** — copied from the tag message. Repeat it here; the
  folder must stand alone when the repo is gone.
- **TO REVERT** / **TO SEE WHAT CHANGED** / **TO FULLY RESTORE** — exact
  commands, the ones you just ran.
- **NOT INCLUDED** — and how to back those up separately.

## Rules

- **Never print secrets.** `cp` them; never `cat`, `head`, or echo a `.env`.
  To show what a secrets file contains, print key names only:
  `cut -d= -f1 env.backup`.
- **Check the live secrets file's permissions** and tell the user if they are
  looser than 600. The backup copy being locked down does not help if the
  original is world-readable.
- **`git archive` includes every TRACKED file**, including runtime junk like
  pid files, logs, and state json if the project tracks them. Check the archive
  contents; if stale runtime files are in there, say so in the README and tell
  the user to delete them before launching a restored tree. Suggest gitignoring
  them going forward.
- **Never delete or overwrite a prior version's backup folder.** Versions
  accumulate. The old one stays valid.
- Verify claims about the running system against live evidence before writing
  them into a tag message that will be trusted for months.
