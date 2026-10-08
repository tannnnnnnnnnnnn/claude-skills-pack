#!/usr/bin/env bash
# Sync the live Claude Code setup into this repo and push to GitHub.
# Safe to run anytime: commits only when something actually changed.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="${CLAUDE_DIR:-$HOME/.claude}"
cd "$REPO_DIR"

# Skills tracked by this pack (personal/third-party-installed ones stay out)
SKILLS="backup-version brainstorm codex-orchestrate debug dream estimate fable graph-loop lifeboat manager plan-big-execute-small stop-slop ultracode ultrathink worktree"

for s in $SKILLS; do
  if [ -d "$CLAUDE_DIR/skills/$s" ]; then
    rsync -a --delete --exclude '.dream-config' "$CLAUDE_DIR/skills/$s/" "skills/$s/"
  fi
done

for h in safety-net lifeboat-save lifeboat-restore; do
  cp "$CLAUDE_DIR/hooks/$h.py" "hooks/$h.py" 2>/dev/null || true
done
cp "$CLAUDE_DIR/budget/budget.py" budget/budget.py 2>/dev/null || true
mkdir -p bin
cp "$HOME/.local/bin/agent-reach" bin/agent-reach 2>/dev/null && chmod +x bin/agent-reach || true
# routines/ is NOT synced. The live scheduled tasks under
# $CLAUDE_DIR/scheduled-tasks name real people, employers and vault content;
# this repo is public. routines/*.md are hand-maintained sanitized templates.

# Privacy gate: never publish credentials or personal identifiers.
if git grep -EIn 'sk-ant-|ghp_|github_pat_|AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|/Users/[a-z]' -- . ':!sync.sh' | grep -v 'example\.com' | grep -v '/Users/you'; then
  echo "Refusing to sync: the matches above look private. Scrub them first." >&2
  exit 1
fi

if git status --porcelain | grep -q .; then
  git add -A
  git commit -m "sync: $(date +%Y-%m-%d) setup snapshot"
  git push origin HEAD
  echo "Synced and pushed: $(git log -1 --oneline)"
else
  echo "No changes since last sync."
fi
