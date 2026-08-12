---
name: fable
description: >
  Fable review loop via Codex — adversarial cross-model review. Fable 5
  produces a plan or diff, Codex (GPT 5.6 sol high, read-only) reviews
  it, Fable revises, same Codex session re-checks, until APPROVED or
  5 rounds. Trigger: /fable, "fable review loop", "codex review loop",
  "have codex review this", or before merging any high-stakes change.
---

# Fable Review Loop via Codex

Cross-model review: a differently-trained reviewer doesn't share the
writer's blind spots. Fable 5 writes, Codex reviews, loop until clean.

## Loop

1. **Capture.** Write the artifact under review (plan text or `git diff`)
   to a session-scoped file in the scratchpad directory — unique filename
   per run so concurrent loops don't collide.
2. **Submit to Codex.** Use the codex plugin (`/codex:rescue` /
   codex-rescue agent) with a review-only brief: model GPT 5.6 (sol
   high), read-only — Codex must NOT edit files. Brief asks for:
   concrete defects with file:line, severity, and a final verdict line —
   exactly `VERDICT: APPROVED` or `VERDICT: REVISE`.
3. **Parse verdict.**
   - `APPROVED` → done, report clean.
   - `REVISE` → address **each** specific concern with real changes —
     don't re-summarize or argue past them. If a concern is wrong, say
     why with evidence in the next submission.
   - Unclear → treat as REVISE, ask Codex to restate as a verdict.
4. **Re-submit to the SAME Codex session** (resume, don't start fresh)
   so the reviewer keeps context on what it already flagged.
5. **Repeat** steps 2-4, hard cap **5 rounds**.

## Exit honestly

- On APPROVED: report rounds taken and what changed.
- On round cap: report the unresolved concerns plainly. Never pretend
  approval that didn't happen.
- Fable makes the final call on genuine disagreement — Codex is the
  reviewer, not the authority. Flag the disagreement to the user.

## Rules

- Reviewed scope only — no drive-by changes while revising.
- Clean up session temp files when the loop ends.
- Cheap sanity first: tests/typecheck pass BEFORE round 1; don't spend
  Codex rounds on what a linter catches.
