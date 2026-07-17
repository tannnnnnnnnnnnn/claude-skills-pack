---
name: plan-big-execute-small
description: >
  Coordinator pattern for token-heavy work: the big model plans and
  synthesizes while cheap subagents do the reading in parallel. Use for
  coverage/read-heavy tasks — verify N facts against sources, research
  across many pages, review/sweep many files, extract from many docs,
  triage logs. Trigger: /plan-big-execute-small, "fan out", "coordinator
  pattern", "delegate the reading", or any task that is mostly mechanical
  reading over many items. Skip for narrow questions or work needing
  frontier judgment on the raw material itself.
---

# Plan Big, Execute Small (Coordinator Pattern)

Split the two jobs inside a heavy task: a small amount of planning/judgment,
and a large amount of mechanical reading. Keep the reading off your own
context and off the frontier rate.

**You are the coordinator.** You plan and synthesize. You do NOT read the raw
material yourself — cheap subagents do, in their own context windows, and
report back distilled findings. Only their final summaries enter your context.

## When this pays

Use it when the reading is **mandatory and bulky**: coverage tasks (verify 20
facts against 20 sources), multi-source research, codebase sweeps, document
review, log triage. The tell: the answer can't come from memory, so the only
question is what rate the reading bills at and whether it happens in parallel.

## When it does NOT pay — check before delegating

- **Too little reading.** Narrow question = nothing to arbitrage. Just answer.
- **Answerable from your own knowledge.** If no reading is needed, delegating
  is pure overhead. Spawn nothing.
- **Needs frontier judgment on the raw material.** Subtle analysis of the
  source text itself (not fact-finding) — a cheap reader summarizes away
  exactly what mattered. Read it yourself.
- **Delegation has a floor cost.** Each subagent has fixed setup overhead.
  Over-splitting into many tiny briefs costs MORE, not less. Find the coarsest
  decomposition where sub-tasks are still independent.

## How to run it

1. **Plan (you, silently).** Decompose the task into focused, *independent*
   sub-tasks — one per worker. Fix the standard up front (e.g. "verify each
   fact against the official source, quote the evidence"). If the decomposition
   itself could be wrong (wrong list of items, wrong premise), spend one worker
   verifying that first.

2. **Fan out cheap workers in parallel.** Spawn subagents with the `Agent`
   tool, **one message, multiple calls** so they run concurrently. Give each a
   cheap `model` override:
   - `haiku` — pure reading, extraction, lookup, fact-check. Cheapest.
   - `sonnet` — reading that needs light judgment or careful cross-checking.
   - Keep you (the session model) as coordinator; never downgrade yourself.

   Each brief must tell the worker: its one sub-task, the standard to meet, and
   to **return only distilled findings** (the answer + evidence/URLs/quotes),
   never raw page dumps. For big fan-outs (many items, multi-stage), use a
   `Workflow` with `agent(..., {model: 'haiku'})` instead of hand-spawning.

3. **Synthesize (you).** Combine the workers' findings into the final answer.
   If a worker returned an infrastructure error instead of findings, re-assign
   that one sub-task to a fresh worker. If findings conflict, flag it — don't
   resolve silently.

## Rules that keep the win real

- **Match rigor.** The cost/speed win only counts if the standard is fixed. A
  cheap solo pass that reads one source per fact is a *different, weaker*
  product — not the same work cheaper.
- **Distilled in, not raw in.** The entire saving is that raw material never
  crosses your context. If a worker pastes back a whole page, the brief was
  wrong — ask for the answer + evidence only.
- **The standard only covers what you put in it.** Workers verify facts, not
  your decomposition. If the premise matters, verify it too.

## Why it works

On the source cookbook's runs, the split team came out ~2.5x cheaper and ~3x
faster than one frontier agent held to the same standard, with 84-98% of input
tokens billed at the cheap worker rate. Native subagents reproduce all three
levers — cheap model reads, workers run in parallel, raw tokens stay out of the
coordinator's context. Origin:
`~/Desktop/repos/claude-cookbooks/managed_agents/CMA_plan_big_execute_small.ipynb`
(that notebook is the API-metered version; this skill is the on-plan version).
