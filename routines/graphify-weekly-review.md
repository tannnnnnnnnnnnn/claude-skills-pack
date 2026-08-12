---
name: graphify-weekly-review
description: Weekly deep re-cluster of AI Brain graph + insight report into vault
---

You are running the weekly "graphify deep review" of the AI Brain knowledge graph. Semantic extraction runs on Codex CLI (ChatGPT subscription quota); only orchestration, labeling, and the report run on Claude.

Vault: ~/Desktop/AI Brain (Obsidian). Graph lives in ~/Desktop/AI Brain/graphify-out/ (graph.json, GRAPH_REPORT.md, graph.html). The graphify CLI is on PATH at ~/.local/bin; the skill is at ~/.claude/skills/graphify/SKILL.md.

## TOKEN BUDGET (hard rules)
- Claude-side target under ~30k tokens per run. Extraction is NOT Claude work anymore — see the extraction rule below.
- Zero-work fast path FIRST: if no vault files changed since last Sunday's run (compare mtimes to graphify-out/.last-weekly, or to graph.json mtime if absent), run Step 2.5's check script (it costs almost nothing and catches a graph left stale by a prior run), write a one-line "no changes this week" log entry, and end. No rebuild, no report.

## EXTRACTION RULE (the one that matters)
- Semantic extraction MUST run via Codex CLI on the ChatGPT subscription — NOT Claude subagents, NOT an API key.
- Preflight: `codex login status` must report logged in. If not, ABORT the run: write one log line ("graphify weekly skipped — codex not authenticated") and a one-line notification, and stop. **Never fall back to dispatching Claude subagents for extraction — that fallback is the failure mode that once burned 1.1M tokens in a single run.**
- **Size-aware chunking (added 2026-08-03 after the first Codex run).** Codex extracts short files well but does NOT scale node count with document length — it caps at ~5-8 nodes per file whether the file is 200 or 20,000 words. The 2026-08-03 run extracted at 4.59 nodes/file overall yet came back with 5 nodes for `index.md` where the graph held 77, and the shrink guard rightly refused the merge (net −116 nodes). So split by size, not just count:
  - **Short files (<~3,000 words):** chunks of ≤10 files as before.
  - **Large files (≥~3,000 words, e.g. index.md, log.md, big wiki hub pages):** 1-2 files per Codex run, and the prompt MUST state an explicit per-file node target scaled to length (roughly 1 node per 250-300 words, and at least the node count the current graph already holds for that file — check with a quick grep of graph.json source_file counts). If a large-file chunk still comes back below its target, retry that chunk once with a stronger model via `-m` (e.g. `-m gpt-5.6-sol-high` or the strongest available); leave short-file chunks on the default model.
- For each chunk, dispatch one headless Codex run (`--skip-git-repo-check` is required — the vault is not a git repo, and without the flag codex exec refuses to run):
  ```bash
  codex exec --skip-git-repo-check --cd "$HOME/Desktop/AI Brain" --sandbox workspace-write "Read the extraction spec at ~/.claude/skills/graphify/references/extraction-spec.md in full and follow it exactly. Extract nodes/edges/hyperedges from these files: <FILE_LIST>. This is chunk <N> of <TOTAL>. <FOR LARGE-FILE CHUNKS: Target at least <K> nodes for <file> — it is a long document; extract at depth, one node per ~250-300 words, not a summary.> Write the result JSON to graphify-out/.graphify_chunk_0<N>.json. Write ONLY that file; no other edits."
  ```
  Chunks may run in parallel (background Bash), but cap at 4 concurrent.
- After each chunk: verify the chunk file exists and parses as JSON with `nodes` and `edges`. Retry a failed chunk once. If more than half the chunks fail after retries, ABORT and report — do not merge a partial extraction, and do not extract the gap yourself on Claude.
- Cap extraction at **90 changed files** per run. If more changed, extract the most recently modified 90 and list the remainder as deferred in the report — next week catches them.
- **Depth guard — per-file, not just aggregate.** After extraction, for every extracted file compare new node count against the count that file currently has in graph.json. Aggregate nodes/file below ~2 → thin, do not merge. Any single file projected to lose more than half its current nodes → treat that file's extraction as thin: pull it from the merge set (quarantine its cache entry), merge the rest, and list it for a deeper retry next week. A shallow re-extraction is subtractive, not merely incomplete — graphify's merge *replaces* every node whose `source_file` appears in the new extraction.
- **Dry-run every merge before writing it.** Count existing nodes whose `source_file` appears in the new extraction, compare against the new node count, and abort on any projected shrink of the overall graph.
- Re-clustering, labeling, and the report are cheap — always fine once extraction passes the depth guard.

## Step 1 — Snapshot last week
Copy graphify-out/GRAPH_REPORT.md aside and note node/edge/community counts from graph.json for the diff.

## Step 2 — Refresh + re-cluster (within cap)
```bash
cd "$HOME/Desktop/AI Brain" && export PATH="$HOME/.local/bin:$PATH"
```
Run the graphify skill's `--update` flow (incremental; cached files free; never ask for an API key) — but wherever the skill would dispatch semantic-extraction subagents (Part B), use the Codex dispatch from the extraction rule above instead, then continue with the skill's own collect/cache/merge steps (B3 onward) unchanged. Then `--cluster-only` (references/update.md) to re-run community detection. Re-label new/changed communities with 2-5 word names. Regenerate GRAPH_REPORT.md, run `graphify export html`, run the health-check diagnostics and note warnings. Touch graphify-out/.last-weekly when done.

Note: the 2026-08-03 run quarantined 78 thin cache entries to `graphify-out/cache/semantic-thin-20260803/` and did not save the manifest, so those files will correctly re-extract from scratch.

**Community indices are reassigned on every re-cluster, so hand-written labels land on the wrong groups after any graph edit.** Batch all node/edge surgery (Step 2.5) FIRST, then re-cluster and label once. On 2026-07-26 three small merges done one at a time moved the count 204 → 213 → 207 → 215 and forced 107 label rewrites, nearly all of it churn. After writing labels, also write the matching signature sidecar (`graphify-out/.graphify_labels.json.sig`, via `graphify.cluster.community_member_sigs`) or the next `cluster-only` discards the curated names and renames every community after its hub node.

## Step 2.5 — Reconcile AMBIGUOUS edges the vault has already settled

```bash
python3 ~/.claude/scheduled-tasks/graphify-weekly-review/check_settled_ambiguity.py
```

Extraction never revisits a page once its content hash is cached, so an answer you give on one wiki page never reaches AMBIGUOUS edges extracted from other pages. Nothing else surfaces the mismatch. One real run found three identity questions that had been confirmed in the wiki five days earlier and were still sitting AMBIGUOUS in the graph.

The script reports each AMBIGUOUS edge whose two endpoints are both named inside a vault confirmation note (`**Disambiguation (confirmed by ...)**` or "confirmed by" in prose). It reports; it does not edit. For each finding:

- **Same person or thing** → merge the duplicate node into the canonical one: retarget its edges, drop self-loops and duplicate `(source, target, relation)` triples, promote retargeted AMBIGUOUS edges to EXTRACTED 1.0, then delete the merged node.
- **Different things** → delete the false edge.
- Back up `graph.json` first (`graph.json.bak-<topic>-YYYYMMDD`) and re-run `graphify diagnose multigraph` after.

Leave two classes of node alone. Nodes whose label reproduces a page's own wording (a name written as `Nickname (Fullname)` because the source page writes it that way) keep the source layer faithful. Nodes recording that a past report saw an open gap (`Unnamed Founder Gap`) describe what that report said, not a separate entity; merging them rewrites the history of the graph's own reasoning.

If the script finds nothing, say so in one line in the report and move on. Expect that to be the normal case.

## Step 3 — Weekly Brain Report
Diff against the Step 1 snapshot; write ~/Desktop/AI Brain/Briefs/Weekly Brain Report YYYY-MM-DD.md (create Briefs/ if missing). Concise, proper English — full grammatical sentences, no filler:
- Delta: nodes/edges/communities vs last week; which areas grew.
- New surprising connections not in last week's report.
- Knowledge gaps: AMBIGUOUS edges + weakly-connected nodes, each phrased as a 2-minute question you could answer to strengthen the brain. Report what Step 2.5 reconciled separately from what is still genuinely open — an edge the vault already settled is a sync lag, not a gap, and asking again wastes your time.
- Stale zones: communities untouched 14+ days that cover time-sensitive topics (courses, engagements, POCs).
- 3 suggested questions the graph can uniquely answer this week.
- Anything deferred for budget (files not yet extracted).
- One line: extraction ran on Codex (chunk count, failures/retries, large-file chunks and their node targets), Claude tokens ≈ this session.
Append one line to ~/Desktop/AI Brain/log.md matching its format.

## Step 4 — Notification summary
Max 5 lines: delta, best new connection, biggest gap, one recommended action, deferred count. Mention Step 2.5 only when it found something. If nothing changed all week: one line.

Constraints: never modify the vault's hand-curated wiki/, People/, or Meetings/ content — write only to Briefs/, log.md, and graphify-out/. Step 2.5 edits graph.json only; if a finding implies a wiki page should change (a page titled with an ambiguous nickname, say), report it as a recommendation rather than editing. Honor graphify's shrink-guard: if the rebuild would shrink graph.json, stop and report rather than forcing.