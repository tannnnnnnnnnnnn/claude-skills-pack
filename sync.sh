#!/usr/bin/env bash
# Sync the live Claude Code setup into this repo and push to GitHub.
# Safe to run anytime: commits only when something actually changed.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="${CLAUDE_DIR:-$HOME/.claude}"
cd "$REPO_DIR"

# Skills tracked by this pack (personal/third-party-installed ones stay out)
SKILLS="brainstorm codex-orchestrate debug dream fable manager plan-big-execute-small stop-slop ultracode ultrathink worktree"

for s in $SKILLS; do
  if [ -d "$CLAUDE_DIR/skills/$s" ]; then
    rsync -a --delete --exclude '.dream-config' "$CLAUDE_DIR/skills/$s/" "skills/$s/"
  fi
done

cp "$CLAUDE_DIR/hooks/safety-net.py" hooks/safety-net.py 2>/dev/null || true
cp "$CLAUDE_DIR/scheduled-tasks/dream-nightly/SKILL.md" routines/dream-nightly.md 2>/dev/null || true
cp "$CLAUDE_DIR/scheduled-tasks/graphify-weekly-review/SKILL.md" routines/graphify-weekly-review.md 2>/dev/null || true

if git status --porcelain | grep -q .; then
  git add -A
  git commit -m "sync: $(date +%Y-%m-%d) setup snapshot"
  git push origin HEAD
  echo "Synced and pushed: $(git log -1 --oneline)"
else
  echo "No changes since last sync."
fi
