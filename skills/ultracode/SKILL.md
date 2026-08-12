---
name: ultracode
description: >
  Guardrailed entry to Claude Code's native multi-agent Workflow
  orchestration. Use for repo-scale work — "audit every", "migrate all",
  "sweep the whole codebase", comprehensive reviews. Trigger: /ultracode
  or explicit orchestration requests. Invoking this skill is the user's
  opt-in to call the Workflow tool.
---

# Ultracode

This skill opts the task into multi-agent Workflow orchestration
(fan-out subagents, cross-check, merge — intermediate state stays out of
the main context). Run it with these guardrails:

## Before launching

1. **Scope it.** Scout inline first (list files, grep targets) so the
   workflow gets a concrete work-list, not a vague sweep.
2. **Estimate.** State expected agent count and rough token cost. If it
   exceeds ~25 agents or the scope is ambiguous, confirm with the user
   before committing.
3. **Right-size.** Default to a scoped sweep (the changed area, one
   subsystem). Full-repo only when the user explicitly asked for it.

## While building the script

- **Pipeline over barriers** — only synchronize stages when a stage truly
  needs all prior results (dedup, early-exit).
- **Route cheap stages cheap.** Mechanical read/extract stages get
  `model: 'haiku'`; reserve the session model for judge/verify stages.
- **Adversarial cross-check.** For audit/review workflows, add an
  independent verify stage that tries to REFUTE each finding; drop what
  doesn't survive.
- **No silent caps.** If coverage is bounded (top-N, sampling), log what
  was dropped.

## After

- Report confirmed results with evidence, coverage achieved, and what was
  skipped. If the workflow shape is repeatable, save the script and name
  it clearly.
- Verify a sample of findings yourself before presenting — orchestration
  scale is not a substitute for the final inspection.
