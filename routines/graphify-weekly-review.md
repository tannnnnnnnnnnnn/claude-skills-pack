---
name: graphify-weekly-review
description: Weekly deep re-cluster of AI Brain graph + insight report into vault
---

You are running the weekly "graphify deep review" of Tanmay's AI Brain knowledge graph. Everything is local; nothing leaves the machine.

Vault: ~/Desktop/AI Brain (Obsidian). Graph lives in ~/Desktop/AI Brain/graphify-out/ (graph.json, GRAPH_REPORT.md, graph.html). The graphify CLI is on PATH at ~/.local/bin; the skill is at ~/.claude/skills/graphify/SKILL.md.

## TOKEN BUDGET (hard rules)
- Target under ~120k tokens per run — this is the week's ONE deep pass, it may work, but not unboundedly.
- Zero-work fast path FIRST: if no vault files changed since last Sunday's run (compare mtimes to graphify-out/.last-weekly, or to graph.json mtime if absent), write a one-line "no changes this week" log entry and end. No rebuild, no report.
- Semantic extraction cap: at most **90 changed files**, chunked at **8-10 files per subagent** (so ~9-11 chunks, not 3). If more files changed, extract the chunks covering the most recently modified files and list the remainder as deferred in the report — next week catches them.
- **Never exceed 10 files per chunk.** On 2026-07-20 a run at 26 files/chunk averaged 1.5 nodes/file against the good build's 3.3, and because graphify's merge *replaces* every node whose `source_file` appears in the new extraction, the thin result would have deleted 165 net curated nodes. A shallow re-extraction is subtractive, not merely incomplete.
- **Dry-run every merge before writing it.** Count existing nodes whose `source_file` appears in the new extraction, compare against the new node count, and abort on any projected shrink. Keep files contiguous within a chunk (same directory where possible) so cross-file edges survive.
- Use a mid-tier model (sonnet) for extraction, not the cheapest available — depth is the failure mode here, and haiku at any chunk size has not yet been shown to clear the bar.
- Re-clustering, labeling, and the report are cheap — always fine once extraction is within cap.

## Step 1 — Snapshot last week
Copy graphify-out/GRAPH_REPORT.md aside and note node/edge/community counts from graph.json for the diff.

## Step 2 — Refresh + re-cluster (within cap)
```bash
cd "$HOME/Desktop/AI Brain" && export PATH="$HOME/.local/bin:$PATH"
```
Run the graphify skill's `--update` flow (incremental; cached files free; never ask for an API key), then `--cluster-only` (references/update.md) to re-run community detection. Re-label new/changed communities with 2-5 word names. Regenerate GRAPH_REPORT.md, run `graphify export html`, run the health-check diagnostics and note warnings. Touch graphify-out/.last-weekly when done.

## Step 3 — Weekly Brain Report
Diff against the Step 1 snapshot; write ~/Desktop/AI Brain/Briefs/Weekly Brain Report YYYY-MM-DD.md (create Briefs/ if missing). Concise, proper English — full grammatical sentences, no filler:
- Delta: nodes/edges/communities vs last week; which areas grew.
- New surprising connections not in last week's report.
- Knowledge gaps: AMBIGUOUS edges + weakly-connected nodes, each phrased as a 2-minute question Tanmay could answer to strengthen the brain.
- Stale zones: communities untouched 14+ days that cover time-sensitive topics (FDE course, engagements, POCs).
- 3 suggested questions the graph can uniquely answer this week.
- Anything deferred for budget (files not yet extracted).
Append one line to ~/Desktop/AI Brain/log.md matching its format.

## Step 4 — Notification summary
Max 5 lines: delta, best new connection, biggest gap, one recommended action, deferred count. If nothing changed all week: one line.

Constraints: never modify the vault's hand-curated wiki/, People/, or Meetings/ content — write only to Briefs/, log.md, and graphify-out/. Honor graphify's shrink-guard: if the rebuild would shrink graph.json, stop and report rather than forcing.