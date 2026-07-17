---
name: worktree
description: >
  Isolated-workspace lifecycle (adapted from obra/superpowers
  using-git-worktrees + finishing-a-development-branch). Start feature
  work in an isolated worktree with a clean test baseline; finish with a
  structured merge/PR/keep/discard decision. Trigger: /worktree to
  start, /worktree done to finish, "work on this in isolation",
  "parallel branch work".
---

# Worktree (Start + Finish)

## /worktree — start isolated work

1. **Detect existing isolation first.** Compare `git rev-parse
   --git-dir` vs `--git-common-dir` (resolved paths). Different (and not
   a submodule — check `git rev-parse --show-superproject-working-tree`)
   → already in a worktree; skip creation, go to setup. Never nest.
2. **Prefer native tools.** This harness has `EnterWorktree` — use it.
   Manual `git worktree add` when a native tool exists creates phantom
   state the harness can't manage. Fallback only if no native tool:
   - Directory priority: user's stated preference > existing
     `.worktrees/` > existing `worktrees/` > default `.worktrees/`.
   - MUST verify the directory is git-ignored (`git check-ignore`)
     before creating; add to .gitignore + commit if not.
   - `git worktree add "$path" -b "$branch"`.
3. **Setup.** Auto-detect and run install (npm install / cargo build /
   pip install -r / go mod download).
4. **Verify clean baseline.** Run the test suite. Failing baseline →
   report and ask before proceeding (otherwise new bugs are
   indistinguishable from pre-existing ones). Passing → report ready.

## /worktree done — finish the branch

1. **Tests must pass first.** Failing → show failures, stop. No merge/PR
   options until green.
2. **Present exactly these options** (no extra prose):
   1. Merge back to <base-branch> locally
   2. Push and create a Pull Request
   3. Keep the branch as-is
   4. Discard this work
3. **Execute:**
   - **Merge:** cd to main repo root, checkout base, pull, merge, re-run
     tests on merged result. Only after success: remove worktree, then
     `git branch -d`.
   - **PR:** push -u origin; KEEP the worktree (needed for review
     iteration).
   - **Keep:** report branch + worktree path, touch nothing.
   - **Discard:** list branch/commits/worktree to be deleted, require
     typed "discard" confirmation, then cleanup + `git branch -D`.
4. **Cleanup rules:** only remove worktrees under `.worktrees/` or
   `worktrees/` (ones this skill created); harness-owned workspaces get
   `ExitWorktree` or are left alone. Always `cd` to main repo root
   before `git worktree remove`; `git worktree prune` after.

## Never

Nest worktrees · bypass native tools · skip ignore-check · merge with
failing tests · delete work without typed confirmation · force-push
without explicit request · remove the worktree before merge succeeds.
