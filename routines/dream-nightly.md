---
name: dream-nightly
description: Nightly memory consolidation + AI Brain graph refresh + morning brief
---

You are running the nightly "dream" routine — memory consolidation plus knowledge-graph refresh for Tanmay's AI Brain. Everything is local; nothing leaves the machine.

## TOKEN BUDGET (hard rules)
- Target under ~25k output tokens per run. This is nightly hygiene, not analysis.
- Zero-work fast path FIRST: if ~/.claude/projects/*/memory/.last-dream is under 20 hours old, AND no transcripts changed since it, report "already consolidated, nothing new" in one line and end the run.
- Transcript scanning is grep-only with small context windows (grep -n plus ~5 surrounding lines). NEVER read a full transcript file. Scan only transcripts modified SINCE THE LAST DREAM (compare mtime to .last-dream), not a blanket 7 days. Cap: 20 files, ~50 match-context reads. Beyond that, note "partial scan, continues tomorrow".
- Note: the daily-brain-harvest task (9pm) already extracts durable knowledge into the vault wiki. Dream's job is ONLY the ~/.claude memory system (corrections, preferences, workflow feedback) — do not duplicate harvest's wiki work.
- Graph refresh cap: count changed files first. If more than 10 non-code files changed in the vault, do only the free structural/AST update and defer semantic re-extraction to the Sunday graphify-weekly-review — say so in the brief. 10 or fewer: proceed (cached files cost nothing).
- If the budget is clearly going to blow, stop gracefully, write the timestamp for what WAS completed, and list deferred work in the brief. Never push through.

## Step 1 — Dream (memory consolidation)
Invoke the `dream` skill (~/.claude/skills/dream/SKILL.md) phases, under the caps above:
1. ORIENT: read ~/.claude/projects/*/memory/MEMORY.md indexes (indexes first; open individual memory files only when a finding touches them).
2. GATHER SIGNAL: grep transcripts-since-last-dream for corrections ("actually", "no,", "wrong", "stop doing"), preferences ("I prefer", "always use", "from now on", "default to"), decisions ("let's go with", "we're using", "switch to"), recurring patterns.
3. CONSOLIDATE: merge findings into memory files — never duplicate (update existing), absolute dates only, replace contradicted facts with "(updated YYYY-MM-DD, previously: X)", one fact per file with YAML frontmatter matching existing conventions.
4. PRUNE & INDEX: each MEMORY.md stays a one-line-per-memory index under 200 lines; archive entries 90+ days stale. Never delete without replacement.
After a real run: `date +%s > <project>/memory/.last-dream` and `rm -f ~/.claude/.dream-pending`.

## Step 2 — Refresh the AI Brain knowledge graph (capped per budget rules)
```bash
cd "$HOME/Desktop/AI Brain" && export PATH="$HOME/.local/bin:$PATH"
```
Follow the graphify skill's incremental update flow (~/.claude/skills/graphify/SKILL.md, references/update.md) against `.` — only new/changed files re-extract; cache hits are free. Apply the >10-changed-files deferral rule above. If graphify or the vault is missing, skip silently. Never ask for an API key.

## Step 3 — Morning brief
Append a short dated entry to ~/Desktop/AI Brain/log.md matching its existing format. End the run with a concise brief (becomes the notification):
- Memory: N facts added/updated/archived, contradictions resolved.
- Graph: files changed, nodes/edges delta, or "deferred to weekly".
- Top 3 things worth attention today (open TODO.md items, unanswered Questions.md items, new AMBIGUOUS/surprising connections).
- Tokens: rough self-estimate of run size; note anything deferred for budget.
If nothing changed overnight, one line only — do not pad.

Constraints: write in concise, proper English — full grammatical sentences, no filler. Never delete memory without replacement. Back up any memory directory before its first-ever consolidation. Do not modify the vault's hand-curated wiki/ folder.