#!/usr/bin/env python3
"""Lifeboat save: snapshot in-flight task state. Deterministic, no LLM, no tokens.

Called by the PreCompact hook (writes snapshot + .pending marker) and by
lifeboat-restore.py's early-save path with --no-pending (snapshot only).
Writes ~/.claude/lifeboat/<session_id>.md.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

LIFEBOAT_DIR = Path.home() / ".claude" / "lifeboat"
MAX_USER_MSGS = 8
MAX_FILES = 20
JUNK_PREFIXES = (
    "<system-reminder", "[SYSTEM", "<task-notification", "<command-",
    "<local-command", "Stop hook feedback", "[Request interrupted",
    "Base directory for this skill", "Caveat:", "Tool loaded",
)


def clean_user_text(txt):
    txt = txt.strip()
    if not txt or txt.startswith(JUNK_PREFIXES):
        return None
    return txt[:250]


def tail_transcript(path):
    user_msgs, edited, last_assistant = [], [], ""
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return user_msgs, edited, last_assistant
    for line in lines:
        try:
            d = json.loads(line)
        except Exception:
            continue
        t = d.get("type")
        msg = d.get("message") or {}
        content = msg.get("content")
        if t == "user" and isinstance(content, str):
            c = clean_user_text(content)
            if c:
                user_msgs.append(c)
        elif t == "user" and isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get("type") == "text":
                    cl = clean_user_text(c.get("text", ""))
                    if cl:
                        user_msgs.append(cl)
        elif t == "assistant" and isinstance(content, list):
            for c in content:
                if isinstance(c, dict):
                    if c.get("type") == "text" and c.get("text", "").strip():
                        last_assistant = c["text"].strip()[-600:]
                    elif c.get("type") == "tool_use" and c.get("name") in ("Edit", "Write", "NotebookEdit"):
                        fp = (c.get("input") or {}).get("file_path")
                        if fp and fp not in edited:
                            edited.append(fp)
    return user_msgs[-MAX_USER_MSGS:], edited[-MAX_FILES:], last_assistant


def git_state(cwd):
    try:
        r = subprocess.run(["git", "-C", cwd, "status", "--short", "--branch"],
                           capture_output=True, text=True, timeout=5)
        out = r.stdout.strip()
        return "\n".join(out.splitlines()[:15]) if out else ""
    except Exception:
        return ""


def main():
    no_pending = "--no-pending" in sys.argv
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    session = data.get("session_id", "unknown")
    transcript = data.get("transcript_path", "")
    cwd = data.get("cwd", os.getcwd())
    trigger = data.get("trigger", "auto")
    label = "early-save" if no_pending else f"{trigger} compaction"

    users, edited, assistant = tail_transcript(transcript)
    git = git_state(cwd)

    stamp = time.strftime("%Y-%m-%d %H:%M")
    parts = [f"# Lifeboat snapshot — {stamp} ({label})", ""]
    parts.append("## Recent user intent (oldest → newest)")
    parts += [f"- {m}" for m in users] or ["- (none captured)"]
    if edited:
        parts += ["", "## Files edited this session"] + [f"- {f}" for f in edited]
    if assistant:
        parts += ["", "## Last assistant status", assistant]
    if git:
        parts += ["", "## Git state", "```", git, "```"]

    LIFEBOAT_DIR.mkdir(parents=True, exist_ok=True)
    (LIFEBOAT_DIR / f"{session}.md").write_text("\n".join(parts), encoding="utf-8")
    if not no_pending:
        (LIFEBOAT_DIR / f"{session}.pending").write_text(stamp, encoding="utf-8")

    cutoff = time.time() - 7 * 86400
    for f in LIFEBOAT_DIR.glob("*.md"):
        if f.stat().st_mtime < cutoff:
            f.unlink(missing_ok=True)
            (LIFEBOAT_DIR / f"{f.stem}.pending").unlink(missing_ok=True)
    sys.exit(0)


if __name__ == "__main__":
    main()
