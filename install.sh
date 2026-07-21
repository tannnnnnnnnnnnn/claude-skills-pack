#!/usr/bin/env bash
# claude-skills-pack installer
# Copies skills + safety-net hook into ~/.claude and wires the hooks.
# Idempotent: safe to re-run. Nothing here phones home.
set -euo pipefail

CLAUDE_DIR="${CLAUDE_DIR:-$HOME/.claude}"
PACK_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing claude-skills-pack into $CLAUDE_DIR"

# 1. Skills
mkdir -p "$CLAUDE_DIR/skills"
for d in "$PACK_DIR"/skills/*/; do
  name=$(basename "$d")
  if [ -d "$CLAUDE_DIR/skills/$name" ]; then
    echo "  skill $name: already exists, skipping (delete it first to reinstall)"
  else
    cp -R "$d" "$CLAUDE_DIR/skills/$name"
    echo "  skill $name: installed"
  fi
done
chmod +x "$CLAUDE_DIR/skills/dream/should-dream.sh" 2>/dev/null || true
printf 'DREAM_MEMORY_TYPE=native\nDREAM_MEMORY_PATH=~/.claude/projects\n' > "$CLAUDE_DIR/skills/dream/.dream-config"

# 2. Hook scripts
mkdir -p "$CLAUDE_DIR/hooks"
for h in safety-net.py lifeboat-save.py lifeboat-restore.py; do
  cp "$PACK_DIR/hooks/$h" "$CLAUDE_DIR/hooks/$h"
  echo "  hook $h: installed"
done

# 2b. Budget tooling for /estimate
mkdir -p "$CLAUDE_DIR/budget"
cp "$PACK_DIR/budget/budget.py" "$CLAUDE_DIR/budget/budget.py"
[ -f "$CLAUDE_DIR/budget/calibration.json" ] || cp "$PACK_DIR/budget/calibration.example.json" "$CLAUDE_DIR/budget/calibration.json"
echo "  budget: budget.py + calibration installed"

# 3. Wire hooks into settings.json (merge, never clobber)
python3 - "$CLAUDE_DIR" <<'PY'
import json, sys, os
claude_dir = sys.argv[1]
path = os.path.join(claude_dir, "settings.json")
s = {}
if os.path.exists(path):
    with open(path) as f:
        s = json.load(f)
hooks = s.setdefault("hooks", {})

pre = hooks.setdefault("PreToolUse", [])
safety_cmd = f"python3 {claude_dir}/hooks/safety-net.py"
if not any(safety_cmd in h.get("command", "") for m in pre for h in m.get("hooks", [])):
    pre.append({"matcher": "Bash", "hooks": [{"type": "command", "command": safety_cmd}]})
    print("  settings: safety-net PreToolUse hook added")
else:
    print("  settings: safety-net hook already present")

prec = hooks.setdefault("PreCompact", [])
save_cmd = f"python3 {claude_dir}/hooks/lifeboat-save.py"
if not any("lifeboat-save" in h.get("command", "") for m in prec for h in m.get("hooks", [])):
    prec.append({"hooks": [{"type": "command", "command": save_cmd}]})
    print("  settings: lifeboat PreCompact hook added")

ups = hooks.setdefault("UserPromptSubmit", [])
restore_cmd = f"python3 {claude_dir}/hooks/lifeboat-restore.py"
if not any("lifeboat-restore" in h.get("command", "") for m in ups for h in m.get("hooks", [])):
    ups.append({"hooks": [{"type": "command", "command": restore_cmd}]})
    print("  settings: lifeboat UserPromptSubmit hook added")

ss = hooks.setdefault("SessionStart", [])
if not any("lifeboat-restore" in h.get("command", "") for m in ss for h in m.get("hooks", [])):
    ss.append({"matcher": "compact", "hooks": [{"type": "command", "command": restore_cmd}]})
    print("  settings: lifeboat SessionStart(compact) hook added")

stop = hooks.setdefault("Stop", [])
dream_cmd = 'bash $HOME/.claude/skills/dream/should-dream.sh >/dev/null 2>&1 && touch $HOME/.claude/.dream-pending; exit 0'
if not any("should-dream" in h.get("command", "") for m in stop for h in m.get("hooks", [])):
    stop.append({"hooks": [{"type": "command", "command": dream_cmd}]})
    print("  settings: dream Stop hook added")
else:
    print("  settings: dream hook already present")

with open(path, "w") as f:
    json.dump(s, f, indent=2)
    f.write("\n")
PY

# 4. Auto-dream trigger in global CLAUDE.md
CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"
if ! grep -q "Auto Dream" "$CLAUDE_MD" 2>/dev/null; then
  cat >> "$CLAUDE_MD" <<'EOF'

## Auto Dream
If `~/.claude/.dream-pending` exists at session start, run `/dream` as a background subagent, then delete the flag (`rm ~/.claude/.dream-pending`). Memory consolidation, auto-runs every 24h via Stop hook.
EOF
  echo "  CLAUDE.md: Auto Dream section added"
else
  echo "  CLAUDE.md: Auto Dream already present"
fi

echo ""
echo "Done. Restart Claude Code to arm the hooks."
echo ""
echo "Optional extras (installed from their official sources, not bundled):"
echo "  Codex plugin (needed by /fable, /manager, /codex-orchestrate):"
echo "    in Claude Code: /plugin marketplace add openai/codex-plugin-cc && /plugin install codex"
echo "    then: npm install -g @openai/codex && codex login"
echo "  Graphify knowledge graphs (/graphify):"
echo "    uv tool install graphifyy && graphify install   (or: pipx install graphifyy)"
echo "  claude-mem auto session memory:"
echo "    npx claude-mem install   (privacy: export CLAUDE_MEM_TELEMETRY=0)"
echo "  Caveman token-saving suite:"
echo "    https://github.com/JuliusBrussee/caveman"
echo "  Routines: see routines/*.md — ask Claude to schedule them (edit vault paths first)."
