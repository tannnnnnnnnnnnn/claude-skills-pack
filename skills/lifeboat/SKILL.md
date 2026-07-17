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

Write `~/.claude/lifeboat/<session_id>.md` (session_id: derive from the
transcript path if known, else use `manual-YYYY-MM-DD-HHMM`) containing:

1. **Goal** — what the user ultimately wants, one sentence.
2. **Plan & phase** — the current plan and which step we're on.
3. **Done so far** — completed steps with file paths.
4. **Decisions made** — each with its one-line why.
5. **Failed attempts** — what was tried and didn't work (saves the next
   session from repeating them).
6. **Next steps** — exactly what to do when work resumes.
7. **Open questions** — anything waiting on the user.

Then create the matching `.pending` marker file (same basename) so the
restore hook injects this snapshot on the next prompt after a compaction
or the user can point a fresh session at it.

Confirm to the user in one line: where it saved and what it covers.

## Rules

- Facts only — no padding. The reader is a future session with zero
  context.
- Never include secrets, tokens, or credential values in the snapshot.
- If a snapshot for this session already exists, overwrite it — newest
  state wins.
