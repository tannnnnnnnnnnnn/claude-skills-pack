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
   `usage` gives weekly/5h used, ceiling, and remaining (effective tokens).
   `context` gives the current session's context size. If the transcript
   path is unknown, ask the user or estimate context from the visible
   conversation length.

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

4. **Express as % of limits.** total ÷ weekly_remaining and ÷
   weekly_ceiling; same for the 5h window if a 5h ceiling is calibrated.

5. **Report** in this shape, then the key lever:
   ```
   Task: "<desc>"  →  est. <low>–<high> effective tokens
     base work:       ~<base>
     context re-reads: ~<ctx>   (at <current_ctx> ctx × ~<turns> turns) [⚠ if >2× base]
     ≈ <X–Y>% of your weekly remaining · <Z>% of the 5h window
   ```
   If the context term dominates, add the lever:
   `💡 In a fresh session (~30k ctx) this drops to ~<N> — <M>% of weekly.`
   If it's a coding-heavy build, add:
   `💡 Routed through /manager → Codex, it bills to your ChatGPT quota, not this weekly limit.`

## Honesty rules

- Estimates are ranges, not promises — agentic loops are unpredictable.
  The base term is fuzzy; the context term is arithmetic and reliable.
- If the task would exceed weekly_remaining, say so plainly and lead with
  the cheapest path (fresh session / Codex / cheaper model), not a number.
- State the calibration assumption once: ceiling is back-calculated at
  cache_weight=0.1 from the user's last UI checkpoint. If the user gives a
  fresh reading, run `budget.py recalibrate <pct>` to refine it.

## Recalibrate

When the user reports a current UI weekly %:
`python3 ~/.claude/budget/budget.py recalibrate <pct>` updates the ceiling
from live measurement. A second checkpoint at a different usage level makes
every later estimate sharper.
