#!/usr/bin/env python3
"""Safety-net PreToolUse hook: blocks destructive Bash commands.

Locally authored (inspired by kenryu42/claude-code-safety-net).
Exit 2 = block (stderr shown to Claude); exit 0 = allow.
Override: run the command yourself, or explicitly tell Claude to
bypass and have it ask you to run it manually.
"""
import json
import re
import sys

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)  # unparseable input -> don't break the session

if data.get("tool_name") != "Bash":
    sys.exit(0)

cmd = (data.get("tool_input") or {}).get("command", "")

DANGEROUS_RM_TARGETS = {
    "/", "/*", "~", "~/", "~/*", "$HOME", "$HOME/", "$HOME/*",
    ".", "./", "./*", "..", "../", "../*", "*",
}


def rm_check(command):
    """True if any rm invocation has both -r and -f and a catastrophic target."""
    for part in re.split(r"[;&|]+", command):
        tokens = part.strip().split()
        if not tokens or tokens[0] != "rm":
            continue
        flags = "".join(t.lstrip("-") for t in tokens[1:] if t.startswith("-"))
        args = [t for t in tokens[1:] if not t.startswith("-")]
        recursive = "r" in flags or "R" in flags or "--recursive" in tokens
        force = "f" in flags or "--force" in tokens
        if recursive and force and any(a in DANGEROUS_RM_TARGETS for a in args):
            return True
    return False


RULES = [
    # force push (allow --force-with-lease)
    (r"\bgit\s+push\b(?!.*--force-with-lease).*(\s--force\b|\s-f\b)",
     "git push --force (use --force-with-lease instead)"),
    (r"\bgit\s+reset\s+--hard\b", "git reset --hard discards uncommitted work"),
    (r"\bgit\s+clean\s+-[a-zA-Z]*f", "git clean -f permanently deletes untracked files"),
    (r"\bgit\s+checkout\s+(--\s+)?\.(\s|$)", "git checkout . discards all working-tree changes"),
    (r"\bgit\s+restore\s+(?!--staged)\.(\s|$)", "git restore . discards all working-tree changes"),
    (r"\bgit\s+branch\s+-D\b", "git branch -D force-deletes without merge check"),
    (r"\bgit\s+stash\s+(clear|drop)\b", "git stash clear/drop permanently deletes stashed work"),
    (r"\bgit\s+worktree\s+remove\s+.*--force", "git worktree remove --force discards changes"),
]

if rm_check(cmd):
    sys.stderr.write(
        "BLOCKED by safety-net hook: rm -rf on root/home/cwd/glob target.\n"
        f"Command: {cmd}\n"
        "If this is genuinely intended, explain why to the user and ask "
        "them to run it manually or explicitly approve a safer variant."
    )
    sys.exit(2)

for pattern, reason in RULES:
    if re.search(pattern, cmd):
        sys.stderr.write(
            f"BLOCKED by safety-net hook: {reason}.\n"
            f"Command: {cmd}\n"
            "If this is genuinely intended, explain why to the user and ask "
            "them to run it manually or explicitly approve a safer variant."
        )
        sys.exit(2)

sys.exit(0)
