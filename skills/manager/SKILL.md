---
name: manager
description: >
  Manager mode — combines codex-orchestrate and plan-big-execute-small,
  biased to spend as little Claude/Anthropic quota as possible. Fable 5
  plans and reviews only; almost all execution AND reading goes to Codex
  (GPT, cheap Sol tier by default) on the separate ChatGPT quota, with
  cheap Claude subagents as fallback. Trigger: /manager, "manager mode",
  "orchestrate", "mixed fleet", or any large multi-part task.
---

# Manager Mode (GPT-first Hybrid Orchestration)

You are the **manager**. Your Anthropic weekly limit is the scarce resource;
the ChatGPT/Codex quota is separate and effectively free by comparison.
**Default to offloading work to Codex/GPT.** Keep your own (Claude) turns
few, short, and low-context. Only distilled results enter your context.

## Routing — GPT-first, cheapest tier that meets the standard

| Worker | Route via | Use for | Quota |
|--------|-----------|---------|-------|
| **Codex — GPT Sol (cheap)** | `/codex:rescue` (model: gpt sol) | DEFAULT for most execution: implementation, edits, refactors, test writing/fixing, and even bulk reading/extraction where a script or Codex can do it | ChatGPT (separate) |
| **Codex — GPT 5.6 high** | `/codex:rescue` (model: gpt 5.6 sol high) | only the hard executor work Sol can't handle: deep root-cause, tricky multi-file refactors, subtle logic | ChatGPT (separate) |
| **haiku subagent** | `Agent` model: haiku | fallback for mechanical reading/extraction when Codex isn't a fit | Anthropic (cheap) |
| **sonnet subagent** | `Agent` model: sonnet | fallback for reading needing light judgment | Anthropic |
| **You (Fable 5)** | — | planning, decomposition, routing, final review, frontier judgment ONLY. Never do bulk execution or reading yourself. | Anthropic (scarce) |

**Bias order for every sub-task:** Codex Sol → Codex 5.6 high → haiku →
sonnet → (last resort) yourself. Escalate a tier only when the cheaper one
genuinely can't meet the standard, and say why.

## Loop

1. **Plan (you, silently, low-context).** Decompose into focused,
   *independent* sub-tasks. Fix each acceptance standard up front (tests to
   pass, files in scope, evidence to quote). Keep planning terse — planning
   is the one thing that must be you, so spend little context on it.

2. **Route GPT-first.** For each sub-task pick the cheapest worker per the
   bias order:
   - Almost everything → Codex Sol via `/codex:rescue`. One concern per
     handoff, narrow self-contained brief. Bundle related work into a single
     Codex session rather than many Claude turns.
   - Only escalate to Codex 5.6 high when Sol's output fails the standard.
   - Reading/extraction Codex can't reach → haiku/sonnet fan-out, **one
     message, multiple Agent calls** (parallel). Big fan-outs → `Workflow`
     with `agent(..., {model: 'haiku'})`.
   - Frontier judgment on raw material → you, briefly.

3. **Inspect (you, cheaply).** Verify each result: read the diff summary,
   run tests, check scope. No blind trust of Codex OR Claude workers. Prefer
   reading a distilled diff over re-reading whole files (keeps your context
   small). Failed worker → re-brief and re-dispatch, don't absorb it.

4. **Final review (you).** Assemble, flag conflicts (never resolve
   silently), one final review, done.

## Token discipline (this is the point)

- **Your context is the cost.** Every Claude turn re-reads the whole
  conversation. Keep the manager session short and low-context: push detail
  into Codex sessions and subagent contexts, pull back only summaries.
- **Prefer one Codex session doing five things over five Claude turns doing
  one each.** Batching work onto Codex moves both the compute AND the
  context cost off your Anthropic quota.
- **Never read large raw material into your own context** — dispatch it.
- If your session context climbs past ~300k mid-task, checkpoint
  (`/lifeboat`) and continue in a fresh window.

## When NOT to orchestrate

- Trivial one-liner → just do it (delegation has a floor cost).
- Single small edit → one Codex handoff still usually wins on quota; a
  truly trivial edit you can do directly.

## Rules

- Match rigor: same standard whoever does the work.
- Distilled in, not raw in — raw material never crosses your context.
- Prefer Codex Sol; escalate tiers only when forced, and say why.
- Verify everything before accepting. You sign off on the final result.
- Surgical changes only — every changed line traces to the request.

Related: `codex-orchestrate`, `plan-big-execute-small`, `estimate`
(pre-flight cost), `lifeboat` (checkpoint before a fresh window).
