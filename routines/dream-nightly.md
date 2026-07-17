---
name: dream-nightly
description: Nightly memory consolidation + AI Brain graph refresh + morning brief
---

You are running the nightly "dream" routine — memory consolidation plus knowledge-graph refresh for Tanmay's AI Brain. Everything is local; nothing leaves the machine.

## Step 1 — Dream (memory consolidation)
Invoke the `dream` skill (~/.claude/skills/dream/SKILL.md) and follow its phases exactly:
1. ORIENT: read ~/.claude/projects/*/memory/MEMORY.md indexes and memory files.
2. GATHER SIGNAL: grep the last 7 days of session transcripts (~/.claude/projects/*/*.jsonl) for corrections ("actually", "no,", "wrong", "stop doing"), preferences ("I prefer", "always use", "from now on", "default to"), decisions ("let's go with", "we're using", "switch to"), and recurring patterns. Read only match context, never full transcripts.
3. CONSOLIDATE: merge findings into memory files — never duplicate (update existing), absolute dates only, replace contradicted facts with a note "(updated YYYY-MM-DD, previously: X)", one fact per file with YAML frontmatter matching existing conventions.
4. PRUNE & INDEX: keep each MEMORY.md as a one-line-per-memory index under 200 lines; archive entries 90+ days stale. Never delete without replacement (superseded or archived only).
Idempotency: if ~/.claude/projects/*/memory/.last-dream shows a run within the last 20 hours, skip Steps 1 and note "already consolidated today". After a real run: `date +%s > <project>/memory/.last-dream` and `rm -f ~/.claude/.dream-pending`.

## Step 2 — Refresh the AI Brain knowledge graph
```bash
cd "$HOME/Desktop/AI Brain" && export PATH="$HOME/.local/bin:$PATH"
```
Follow the graphify skill's incremental update flow (~/.claude/skills/graphify/SKILL.md, references/update.md) against `.` — only new/changed files are re-extracted; unchanged files hit the cache for free. If graphify or the vault is missing, skip silently and note it. If semantic re-extraction is needed for changed docs, do it inline (you are the LLM — never ask for an API key).

## Step 3 — Morning brief
Write a short dated entry appended to ~/Desktop/AI Brain/log.md following the vault's existing log format (read the file first, match conventions from the vault's CLAUDE.md). Then end your run with a concise brief (this becomes the completion notification):
- Memory: N facts added/updated/archived, any contradictions resolved.
- Graph: files changed since last run, new nodes/edges.
- Top 3 things worth attention today: open items from ~/Desktop/AI Brain/TODO.md, unanswered items in Questions.md, and any new AMBIGUOUS or surprising connections the graph update surfaced.
If absolutely nothing changed overnight, say exactly that in one line — do not pad.

Constraints: user prefers terse caveman-style output (drop filler, keep technical substance). Never delete memory without replacement. Back up any memory directory before its first-ever consolidation. Do not modify the vault's hand-curated wiki/ folder.