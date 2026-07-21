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

## The fork/model gate — apply BEFORE picking a worker

Before routing a sub-task to any worker, answer two questions. This decides
whether to isolate it (no conversation history) and which model tier it
needs — independent of the routing table above:

| Needs this conversation's context? | Needs frontier reasoning? | What to do |
|---|---|---|
| No  | No  | **Isolate + cheap.** Dispatch via `Agent` (already isolated by default — no inherited history) with `model: haiku`. If this exact sub-task pattern recurs, define it as a real skill with `context: fork` + `agent: general-purpose` (or `Explore` for pure search) so it's reusable, not re-typed. |
| Yes | No  | **Stay in-thread, downshift model.** Don't dispatch — delegating would either lose the needed context or cost just as much to paste it in. Instead do this turn yourself at a cheap tier (session `/model` or a per-skill `model:` override), keeping the thread intact. |
| No  | Yes | **Isolate, keep the model strong.** Dispatch via `Agent`/a `context: fork` skill, but do NOT downgrade the model — pass `model: sonnet`/`fable` or let the chosen `agent:` type's own model stand. |
| Yes | Yes | **Main-thread work, no delegation.** This is your job (the manager/Fable). Frontier judgment on live context can't be forked away. |

Key fact this table relies on: an `Agent` tool dispatch is **already
isolated** by default — no inherited conversation, prompt must be
self-contained. So "isolate" is usually free; the real decision per
sub-task is just **which model tier**, and whether the sub-task can be
isolated at all without losing context it actually needs.

## Loop

1. **Plan (you, silently, low-context).** Decompose into focused,
   *independent* sub-tasks. Fix each acceptance standard up front (tests to
   pass, files in scope, evidence to quote). Keep planning terse — planning
   is the one thing that must be you, so spend little context on it.

2. **Gate, then route GPT-first.** For each sub-task, run it through the
   fork/model gate above, then pick the cheapest worker that clears it:
   - Almost everything (no-context, no-frontier) → Codex Sol via
     `/codex:rescue`. One concern per handoff, narrow self-contained brief.
     Bundle related work into a single Codex session rather than many
     Claude turns.
   - Only escalate to Codex 5.6 high when Sol's output fails the standard.
   - Reading/extraction Codex can't reach, no-context/no-frontier → haiku/
     sonnet fan-out, **one message, multiple Agent calls** (parallel). Big
     fan-outs → `Workflow` with `agent(..., {model: 'haiku'})`.
   - Needs-context/no-frontier → don't delegate; do it yourself at a cheap
     model tier for that turn.
   - Frontier judgment on raw material (needs-context/needs-frontier) →
     you, briefly, at full capability.

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

## Defining a `context: fork` skill for a recurring sub-task

When the same no-context sub-task keeps recurring (e.g. "explore this repo
for X", "run the test suite and summarize failures"), don't keep re-typing
an `Agent` dispatch — write it once as a skill:

```yaml
---
name: some-recurring-check
description: What it does and when to use it
context: fork
agent: Explore        # or general-purpose, Plan, or a custom subagent
model: haiku           # only if the agent type's default model isn't cheap enough
disable-model-invocation: true   # if it should only run when explicitly called
---

The task, written as direct instructions — this body becomes the
subagent's entire prompt. It gets no conversation history, so it must be
fully self-contained.
```

`context: fork` runs the skill body as the subagent's task with **no
access to conversation history** — confirmed current behavior
(code.claude.com/docs/en/skills, "Run skills in a subagent"). The `agent:`
field's own model/tools apply unless overridden.

Related: `codex-orchestrate`, `plan-big-execute-small`, `estimate`
(pre-flight cost), `lifeboat` (checkpoint before a fresh window).
