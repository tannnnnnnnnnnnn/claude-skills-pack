---
name: debug
description: >
  Systematic root-cause debugging (adapted from obra/superpowers
  systematic-debugging). Four gated phases — investigate, pattern-match,
  hypothesize, fix — no fix proposals before investigation completes.
  Trigger: /debug, any bug, test failure, unexpected behavior, "why is
  this broken", especially under time pressure or after failed fixes.
---

# Debug (Systematic Root-Cause)

**Iron law: NO FIXES WITHOUT ROOT-CAUSE INVESTIGATION FIRST.**
Symptom patches are failures. Applies even when the bug "looks simple"
or the user is in a hurry — systematic is faster than thrashing.

## Phase 1 — Root cause investigation

1. Read the FULL error message and stack trace. Line numbers, paths,
   codes. The answer is often already there.
2. Reproduce reliably. Not reproducible → gather more data, don't guess.
3. Check recent changes: git diff, recent commits, new deps, config,
   environment differences.
4. Multi-component systems (CI → build → deploy, API → service → DB):
   add logging at EACH component boundary (data in, data out, env/config
   propagation), run once, find WHICH layer breaks — then investigate
   that layer only.
5. Trace bad values backward up the call stack to their origin. Fix at
   the source, not where the error surfaced.

## Phase 2 — Pattern analysis

- Find similar WORKING code in the same codebase; list every difference
  from the broken code, however small — don't assume "that can't matter".
- If implementing a reference pattern, read the reference completely
  before adapting it.

## Phase 3 — Hypothesis

- State ONE specific hypothesis: "X is the root cause because Y."
- Test with the SMALLEST possible change. One variable at a time.
- Failed → new hypothesis. Do NOT stack more fixes on top.
- Don't understand something? Say so and investigate — never pretend.

## Phase 4 — Fix

1. Write a failing test that reproduces the bug FIRST (script if no
   test framework).
2. One fix, addressing the root cause. No "while I'm here" changes.
3. Verify: new test passes, no other tests broken.
4. **3+ failed fix attempts = wrong architecture, not bad luck.** STOP.
   Question the pattern with the user instead of attempting fix #4 —
   especially if each fix reveals a new problem somewhere else.

## Red flags — stop and return to Phase 1

"Quick fix for now" · "just try changing X" · "it's probably X" ·
"skip the test, I'll verify manually" · proposing fixes before tracing
data flow · multiple changes at once · "one more attempt" after 2 fails.

## If truly no root cause

Genuinely environmental/timing/external (rare — 95% of "no root cause"
is incomplete investigation): document what was ruled out, add
appropriate handling (retry/timeout/clear error), add logging for next
time.
