---
name: dream
description: >
  Memory consolidation routine (adapted from grandamenium/dream-skill,
  aligned to native Claude Code auto-memory). Scans recent session
  transcripts for corrections, decisions, preferences, and patterns,
  merges findings into persistent memory, prunes stale entries, rebuilds
  the index. Auto-triggers via Stop hook every 24h. Trigger: /dream,
  "consolidate memory", or the ~/.claude/.dream-pending flag at session
  start.
---

# Dream — Memory Consolidation

Four sequential phases. Do not skip phases.

```
ORIENT --> GATHER SIGNAL --> CONSOLIDATE --> PRUNE & INDEX
```

Memory system: **native Claude Code auto-memory** —
`~/.claude/projects/<project>/memory/` (MEMORY.md index + one fact per
file with YAML frontmatter). Transcripts:
`~/.claude/projects/<project>/*.jsonl`.

## Phase 1 — ORIENT

Read each project's `memory/MEMORY.md` index and its memory files. Note:
topic coverage, file sizes, last-modified dates, entries that look stale
or contradictory, relative dates lacking an absolute anchor.

**First run against a project: back up first**
(`cp -r memory/ memory-backup-YYYYMMDD/`), and do a DRY RUN — report
what would change, get user confirmation before writing.

## Phase 2 — GATHER SIGNAL

Find transcripts from the last 7 days (`find ... -name "*.jsonl"
-mtime -7`). Targeted grep, never full reads:

- **Corrections** (highest priority): "actually", "no,", "wrong",
  "stop doing", "I meant", "that's not"
- **Preferences:** "I prefer", "always use", "never use", "from now on",
  "remember that", "default to"
- **Decisions:** "let's go with", "we're using", "switch to", "decided"
- **Recurring patterns:** "again", "every time", "keep forgetting",
  "same as before"

For each match, read only surrounding context (user message + immediate
reply). Extract: the fact, the date (from file mtime, converted to
absolute), confidence (explicit instruction = high, implied = medium),
and any contradiction with existing memory.

## Phase 3 — CONSOLIDATE

1. **Never duplicate** — update the existing memory file rather than
   creating a parallel one.
2. **Absolute dates only** — "yesterday" from a March 15 session becomes
   2026-03-14. Never store relative dates.
3. **Contradicted facts get replaced**, with a note:
   `(updated YYYY-MM-DD, previously: X)`.
4. **Attribute sources:** `(from session YYYY-MM-DD)`.
5. **Native format:** one fact per file with frontmatter
   (`name`, `description`, `metadata.type`: user/feedback/project/
   reference), `[[links]]` between related memories, one-line pointer
   per file in MEMORY.md. Follow the existing files' conventions.
6. Read before editing, always.

## Phase 4 — PRUNE & INDEX

- MEMORY.md is an INDEX, not a content store: one line per memory file,
  no full entries, under 200 lines. Overflow → move content into memory
  files, demote oldest to `archive.md`.
- Prune: entries 90+ days old with no recent references, contradicted
  entries, entries about projects that no longer exist.
- **Never delete without replacement** — removed entries were either
  contradicted (superseded) or moved (archived). Never just dropped.

## Phase 5 — REFRESH KNOWLEDGE GRAPH

After memory consolidation, incrementally refresh the AI Brain vault
graph (only new/changed notes are re-extracted — cached files are free):

```bash
cd "$HOME/Desktop/AI Brain" && export PATH="$HOME/.local/bin:$PATH"
```

Then follow the graphify skill's `--update` flow
(`~/.claude/skills/graphify/references/update.md`) against `.`. If
nothing changed since last run, this is a no-op. Skip silently if the
vault or `graphify-out/` no longer exists.

Finish by writing the timestamp and clearing the trigger flag:

```bash
date +%s > ~/.claude/projects/<project>/memory/.last-dream
rm -f ~/.claude/.dream-pending
```

## Verify

MEMORY.md under 200 lines · no duplicate entries · no relative dates ·
every indexed file exists · print summary (added/updated/archived/
contradictions resolved).

## Related

Native `consolidate-memory` skill does a one-shot version of Phases
3-4; dream adds transcript signal-mining (Phase 2) and the 24h
auto-trigger. Auto-trigger flow: Stop hook runs `should-dream.sh`
(24h+ elapsed → creates `~/.claude/.dream-pending`); next session start
sees the flag and runs /dream in the background.
