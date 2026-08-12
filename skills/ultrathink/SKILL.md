---
name: ultrathink
description: >
  Deep-reasoning discipline layer on top of Claude Code's native
  ultrathink keyword. Use for hard architecture decisions, subtle bugs,
  risky refactors, or any problem where the first answer is probably
  wrong. Trigger: /ultrathink, "think deeper", "think hard about this",
  "craft this carefully".
---

# Ultrathink

ultrathink

The word above fires Claude Code's native deep-reasoning budget for this
turn. This skill adds the discipline that raw thinking budget doesn't:

## Method

1. **Frame before solving.** State 2-3 competing interpretations of the
   problem or candidate approaches. Do not silently commit to the first.
2. **Surface assumptions.** List the assumptions each approach rests on
   and the unstated tradeoffs. If an assumption is load-bearing and
   unverified, verify it (read the code, check the docs) before deciding.
3. **Stress-test.** For each serious candidate: failure modes, edge cases,
   and reversibility cost — how expensive is it to back out if wrong?
4. **Simplicity check.** Prefer the simplest approach that satisfies the
   real constraints. Explicitly flag over-engineering risk in your own
   proposal before the user has to.
5. **Commit.** End with one explicit recommendation and a one-line
   rationale — not an open-ended analysis dump. If genuinely torn,
   say which way you'd lean and what single fact would flip it.

## Rules

- Reasoning depth is for the decision, not the prose — keep the final
  answer tight; the deliberation happens in thinking.
- If the problem turns out to be trivial, say so and answer directly —
  don't perform depth that isn't needed.
