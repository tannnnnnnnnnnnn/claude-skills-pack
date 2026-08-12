---
name: estimate
description: >
  Pre-task token estimator. Before running a heavy task, estimate its
  token cost and what % of the weekly + 5-hour Max-plan limit it will
  consume — factoring the dominant cost, context re-reads. Trigger:
  /estimate <task description>, "how much will this cost", "can I afford
  to run this", or before kicking off any large build/sweep/research job.
---

# Estimate (pre-task token cost)

Answer "can I afford to run this?" **before** spending the tokens. The
headline lesson this skill exists to teach: in a long session, the cost is
dominated by **context re-reads**, not the work itself.

## Steps

1. **Get live budget + context.** Run:
   ```bash
   python3 ~/.claude/budget/budget.py usage
   python3 ~/.claude/budget/budget.py context "<this session's transcript_path>"
   ```
   `usage` gives per-meter used/ceiling/pct/remaining plus `binding` — the
   meter furthest along. The plan enforces several **independent** weekly
   limits (all-models, and a tighter Fable pool); the binding one alone
   decides what is affordable. Never quote the pooled all-models figure as
   "your weekly usage" when another meter is higher.
   `context` gives the current session's context size — pass the transcript
   path bare and quoted, with no trailing text, or it silently returns 0. If
   the path is unknown, ask the user or estimate from conversation length.

2. **Classify the task** into one archetype and read its baseline from
   `~/.claude/budget/calibration.json` → `baselines_effective_tokens`:
   single_file_edit · multi_file_feature · debug_investigation ·
   research_fanout · big_build · repo_sweep_ultracode. Pick the closest;
   note if it straddles two.

3. **Compute the estimate** (all in *effective* tokens — cache reads
   weighted by `cache_weight`, default 0.1):
   - **base** = the archetype's base range.
   - **context term** = `current_context × cache_weight × estimated_turns`
     (turns from the archetype range). THIS is usually the biggest term
     and the one the user can control.
   - **total** = base + context term, as a low–high range.

4. **Express as % of limits.** Charge the estimate to the meter the work
   will actually run on: Fable-model work hits both the `fable` meter and
   `all`; everything else hits `all` only. Divide by that meter's
   `remaining`. Also report the `binding` meter if it differs, since it caps
   the session regardless.

5. **Report** in this shape, then the key lever:
   ```
   Task: "<desc>"  →  est. <low>–<high> effective tokens
     base work:       ~<base>
     context re-reads: ~<ctx>   (at <current_ctx> ctx × ~<turns> turns) [⚠ if >2× base]
     ≈ <X–Y>% of <meter> remaining · binding meter is <binding> at <pct>%
   ```
   If the context term dominates, add the lever:
   `💡 In a fresh session (~30k ctx) this drops to ~<N> — <M>% of that meter.`
   If it's a coding-heavy build, add:
   `💡 Routed through /manager → Codex, it bills to your ChatGPT quota, not this weekly limit.`
   If the binding meter is a model family rather than the pool, name the
   escape: running on a different model family sidesteps it entirely.

## Honesty rules

- Estimates are ranges, not promises — agentic loops are unpredictable.
  The base term is fuzzy; the context term is arithmetic and reliable.
- If the task would exceed weekly_remaining, say so plainly and lead with
  the cheapest path (fresh session / Codex / cheaper model), not a number.
- State the calibration assumption once: ceilings are back-calculated at
  cache_weight=0.1 from the user's last UI checkpoint. If the user gives a
  fresh reading, run `budget.py recalibrate <all_pct> [fable_pct]`.
- `cache_weight=0.1` is an unverified guess, and cache reads outnumber fresh
  tokens ~16:1, so it dominates every figure. Ceilings back-calculated from
  a checkpoint absorb the error only while the model mix holds. When a fresh
  reading disagrees sharply with the estimate, suspect the weight or a
  missing meter before suspecting hidden usage.

## Recalibrate

When the user reports current UI percentages:
`python3 ~/.claude/budget/budget.py recalibrate <all_pct> [fable_pct]`
updates each meter's ceiling from live measurement. Recalibrate whenever a
reading is available — the ceilings drift as the model mix changes.

## Adding a meter

If the plan gains another limit, add one entry to `METERS` in `budget.py`
(name → substring matched against the model id) and one ceiling under
`ceilings_weekly_effective` in `calibration.json`. Nothing else changes.
