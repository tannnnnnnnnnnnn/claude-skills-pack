---
name: graphify-weekly-review
description: Weekly deep re-cluster of AI Brain graph + insight report into vault
---

You are running the weekly "graphify deep review" of Tanmay's AI Brain knowledge graph. Everything is local; nothing leaves the machine.

Vault: ~/Desktop/AI Brain (Obsidian). Graph lives in ~/Desktop/AI Brain/graphify-out/ (graph.json, GRAPH_REPORT.md, graph.html). The graphify CLI is on PATH at ~/.local/bin; the skill is at ~/.claude/skills/graphify/SKILL.md.

## Step 1 — Snapshot last week
Copy graphify-out/GRAPH_REPORT.md to a temp location and note current node/edge/community counts from graph.json, so you can diff after the rebuild.

## Step 2 — Full refresh + re-cluster
```bash
cd "$HOME/Desktop/AI Brain" && export PATH="$HOME/.local/bin:$PATH"
```
Run the graphify skill's `--update` flow first (incremental re-extraction of changed files; you are the LLM for any semantic extraction — never ask for an API key), then the `--cluster-only` flow (references/update.md) to re-run community detection on the full graph. Re-label any new or changed communities with 2-5 word plain-language names. Regenerate GRAPH_REPORT.md and run `graphify export html`. Run the graph health check (diagnostics) and note any warnings.

## Step 3 — Weekly Brain Report
Compare against the Step 1 snapshot and write ~/Desktop/AI Brain/Briefs/Weekly Brain Report YYYY-MM-DD.md (create Briefs/ if missing; use the actual date). Contents, terse caveman style:
- Delta: nodes/edges/communities vs last week; which areas grew.
- New surprising connections (from GRAPH_REPORT.md "Surprising Connections") that were not in last week's report.
- Knowledge gaps: AMBIGUOUS edges and weakly-connected nodes worth resolving — phrase each as a concrete question Tanmay could answer in 2 minutes to strengthen the brain.
- Stale zones: communities with no file changes in 14+ days that reference time-sensitive topics (job search, engagements, POCs).
- 3 suggested questions the graph is uniquely positioned to answer this week.
Also append a one-line entry to ~/Desktop/AI Brain/log.md matching its existing format.

## Step 4 — Notification summary
End with a 5-line max summary: delta, best new connection, biggest gap, one recommended action. If the vault didn't change all week, say exactly that in one line.

Constraints: never modify the vault's hand-curated wiki/, People/, or Meetings/ content — you only write to Briefs/, log.md, and graphify-out/. Honor graphify's shrink-guard: if the rebuild would shrink graph.json, stop and report rather than forcing.