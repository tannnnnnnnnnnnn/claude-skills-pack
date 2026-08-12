---
name: brainstorm
description: >
  Design-before-code brainstorming (adapted from obra/superpowers
  brainstorming skill). Hard gate: no code, scaffolding, or file changes
  until a written design is approved. Trigger: /brainstorm, "let's
  brainstorm", "help me design", "think through this feature with me",
  or any fuzzy feature idea that needs shaping before implementation.
---

# Brainstorm

Turn a fuzzy idea into an approved written design. **Hard gate: no code,
no scaffolding, no implementation action until the design is approved —
even for asks that look trivial.**

## Process

1. **Explore context first.** Read relevant files, docs, recent commits
   BEFORE asking anything — don't make the user explain what the repo
   already says.
2. **Ask one question at a time.** Clarify purpose, constraints, and
   success criteria. Prefer multiple-choice framing so answers are cheap.
   Never batch a wall of questions.
3. **Check scope early.** If the ask is really multiple subsystems, flag
   the decomposition before drilling into details.
4. **Propose 2-3 approaches** with explicit tradeoffs and a
   recommendation. Include the boring/simple option honestly.
5. **Present the design in sections** — architecture, components, data
   flow, error handling, testing — and get approval section-by-section,
   not one big yes at the end.
6. **Write the approved design to a spec file:**
   `docs/specs/YYYY-MM-DD-<topic>-design.md`.
7. **Self-review the spec** for placeholders, contradictions, and
   unanswered questions before showing it.
8. **Get explicit sign-off** on the written spec.
9. **Hand off cleanly.** Offer next steps (plan → implement, e.g. via the
   `manager` workflow) — but implementation is a separate, user-triggered
   step. This skill never implements.

## Rules

- Visual companion (mockup/diagram) only when genuinely useful, not by
  default.
- If the user answers "just build it" mid-brainstorm, confirm once that
  they're waiving the design gate, then stop the skill and proceed
  normally.
