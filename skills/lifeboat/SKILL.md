---
name: lifeboat
description: >
  Manual save of in-flight task state — a richer version of the automatic
  pre-compaction snapshot. Use before closing a session mid-task, before a
  risky long operation, or anytime the user says "save our state",
  "/lifeboat", "checkpoint this", "don't lose where we are".
---

# Lifeboat (manual checkpoint)

The lifeboat hooks already auto-snapshot before every context compaction.
This skill is the manual, richer version — you (the model) write the state
file yourself, so it captures intent, not just mechanics.

## On invoke

### 1. Pick the filename

Snapshots share one global directory across every project, so the name must
carry project identity:

- **Preferred:** `~/.claude/lifeboat/<session_id>.md`, deriving `session_id`
  from the transcript path. Session ids are unique, and this basename is the
  one the restore hook's `.pending` path looks for.
- **Fallback** (session id not derivable):
  `~/.claude/lifeboat/manual-<cwd-slug>-<YYYY-MM-DD-HHMM>.md`, where
  `cwd-slug` is the basename of the current working directory, lowercased,
  with every run of non-alphanumeric characters collapsed to `-`.
  Working in `/Users/you/Desktop/Quill` → `manual-quill-2026-07-27-1515.md`.

A bare `manual-<timestamp>.md` is never acceptable. A timestamp alone cannot
distinguish two projects checkpointing in the same minute, and it gives a
future session no way to tell whose snapshot it is short of reading the body.

### 2. Write the snapshot

The `.md` contains:

1. **Goal** — what the user ultimately wants, one sentence.
2. **Plan & phase** — the current plan and which step we're on.
3. **Done so far** — completed steps with file paths.
4. **Decisions made** — each with its one-line why.
5. **Failed attempts** — what was tried and didn't work (saves the next
   session from repeating them).
6. **Next steps** — exactly what to do when work resumes.
7. **Open questions** — anything waiting on the user.

### 3. Write the `.meta` sidecar — always

Alongside the `.md`, write `<same-basename>.meta`:

```json
{"cwd": "/absolute/path/to/cwd", "ts": 1784756715.7, "label": "manual /lifeboat"}
```

`ts` is epoch seconds. This is not optional bookkeeping: it is the only
thing that makes the snapshot restorable. `lifeboat-restore.py`'s
cross-session handoff finds candidates by iterating `*.meta` and matching
`cwd`, so a snapshot without one is invisible to it and will never be
offered to a future session in this folder.

### 4. Write the `.pending` marker — only when the basename is the session id

`.pending` is looked up as `<session_id>.pending`. It does something only
when the snapshot is named after the session. On a `manual-<slug>-<time>`
fallback name, skip it; the `.meta` written above is what makes that
snapshot restorable.

Confirm to the user in one line: where it saved and what it covers.

## Rules

- Facts only — no padding. The reader is a future session with zero
  context.
- Never include secrets, tokens, or credential values in the snapshot.
- **Never overwrite a snapshot belonging to another project.** Before
  writing over any existing file, read its `.meta` and confirm the `cwd`
  matches the current one. If there is no `.meta`, read the body and
  identify the project before touching it. Snapshots from every project
  share this one directory, and the filename alone is not proof of
  ownership.
- If a snapshot for this session, or an older one for this same cwd,
  already exists, overwrite it — newest state wins.
