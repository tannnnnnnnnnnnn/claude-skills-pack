#!/usr/bin/env python3
"""Lifeboat UserPromptSubmit hook: inject the pre-compaction snapshot once.

If a .pending marker exists for this session, emit the snapshot as
additionalContext on the next user prompt, then delete the marker so it
never injects twice. Costs nothing when there is no pending snapshot.
"""
import json
import sys
from pathlib import Path

LIFEBOAT_DIR = Path.home() / ".claude" / "lifeboat"


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    session = data.get("session_id", "")
    marker = LIFEBOAT_DIR / f"{session}.pending"
    snap = LIFEBOAT_DIR / f"{session}.md"
    if not (session and marker.exists() and snap.exists()):
        sys.exit(0)

    content = snap.read_text(encoding="utf-8", errors="replace")
    marker.unlink(missing_ok=True)

    ctx = (
        "Context was just compacted. Lifeboat snapshot of in-flight state "
        "taken right before compaction — treat this as authoritative for what "
        "we were doing, then continue the task:\n\n" + content
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": ctx,
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
