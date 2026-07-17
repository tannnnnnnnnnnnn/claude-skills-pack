#!/usr/bin/env python3
"""Lifeboat PreCompact hook: snapshot in-flight task state before compaction.

Deterministic — no LLM calls, no tokens, runs in milliseconds.
Writes ~/.claude/lifeboat/<session_id>.md + a .pending marker that the
UserPromptSubmit hook (lifeboat-restore.py) injects once, then clears.
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


def tail_transcript(path, session_id):
    """Extract user intent trail, edited files, and last assistant text."""
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
        if t == "user" and isinstance(content, str) and content.strip():
            if not content.startswith(("<system-reminder", "[SYSTEM", "<task-notification")):
                user_msgs.append(content.strip()[:250])
        elif t == "user" and isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get("type") == "text":
                    txt = c.get("text", "").strip()
                    if txt and not txt.startswith(("<system-reminder", "[SYSTEM", "<task-notification")):
                        user_msgs.append(txt[:250])
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
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    session = data.get("session_id", "unknown")
    transcript = data.get("transcript_path", "")
    cwd = data.get("cwd", os.getcwd())
    trigger = data.get("trigger", "auto")

    users, edited, assistant = tail_transcript(transcript, session)
    git = git_state(cwd)

    stamp = time.strftime("%Y-%m-%d %H:%M")
    parts = [f"# Lifeboat snapshot — {stamp} ({trigger} compaction)", ""]
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
    (LIFEBOAT_DIR / f"{session}.pending").write_text(stamp, encoding="utf-8")

    # prune snapshots older than 7 days
    cutoff = time.time() - 7 * 86400
    for f in LIFEBOAT_DIR.glob("*.md"):
        if f.stat().st_mtime < cutoff:
            f.unlink(missing_ok=True)
            (LIFEBOAT_DIR / f"{f.stem}.pending").unlink(missing_ok=True)
    sys.exit(0)


if __name__ == "__main__":
    main()
