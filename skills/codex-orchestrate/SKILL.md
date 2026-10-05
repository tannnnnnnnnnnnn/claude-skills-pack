---
name: codex-orchestrate
description: >
  Orchestrator workflow — plan/review with Opus 5.5, delegate heavy
  coding to codex-rescue (strongest Codex tier), verify Codex output before
  accepting. Trigger: /codex-orchestrate, "use the codex workflow", or any
  multi-step coding task with heavy implementation.
---

# Codex Orchestrate

You are the **orchestrator**. Split every substantial task into a planning/review
brain (Opus 5.5) and an execution engine (Codex via codex-rescue).

## Roles

| Role | Who | Handles |
|------|-----|---------|
| Plan + review | **Opus 5.5** | repo understanding, architecture decisions, task decomposition, final review |
| Execute | **codex-rescue** (`/codex:rescue`) | heavy implementation, debugging, test fixing, refactoring, multi-file edits |

If the main session is not already Opus 5.5, spawn Opus 5.5 sub-agents
(`Agent` with `model: opus`) for the planning and review roles.

## Loop

1. **Plan (Opus 5.5).** Understand the repo, decide architecture, decompose
   into focused, specific tasks. Do not hand vague work to Codex.
2. **Delegate (Codex).** For each heavy task, call `/codex:rescue` with a
   narrow, self-contained brief. Prefer the **strongest Codex tier**. One
   concern per handoff — don't bundle unrelated changes.
3. **Inspect (yourself).** After Codex finishes, read the diff/output
   yourself. Do **not** blindly trust it. Check correctness, scope creep,
   and that it did only what was asked.
4. **Review (Opus 5.5).** Final review of the assembled result before
   declaring done.

## Rules

- Keep Codex tasks focused and specific — scoped to a single concern.
- Always verify Codex output before accepting. No blind trust.
- Surgical changes only — every changed line traces to the request.
