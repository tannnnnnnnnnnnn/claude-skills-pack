#!/usr/bin/env python3
"""Lifeboat restore + early-save. Runs on UserPromptSubmit AND SessionStart(compact).

Restore: if a .pending marker exists for this session, inject the snapshot
as additionalContext once, then delete the marker.

Early-save (UserPromptSubmit only): read actual token usage from the
transcript's last assistant entry; if the context is ~88%+ full, refresh
the snapshot (no marker) so state survives even if PreCompact never fires
on this surface. Costs zero tokens — pure file reads.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

LIFEBOAT_DIR = Path.home() / ".claude" / "lifeboat"
SAVE = Path.home() / ".claude" / "hooks" / "lifeboat-save.py"
THRESHOLD = 0.88


def last_context_tokens(transcript):
    """Actual context size from the newest usage block in the transcript tail."""
    try:
        size = os.path.getsize(transcript)
        with open(transcript, "rb") as f:
            f.seek(max(0, size - 400_000))
            tail = f.read().decode("utf-8", errors="replace").splitlines()
    except Exception:
        return 0
    for line in reversed(tail):
        try:
            d = json.loads(line)
        except Exception:
            continue
        u = (d.get("message") or {}).get("usage")
        if u:
            return (u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
                    + u.get("cache_creation_input_tokens", 0))
    return 0


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    session = data.get("session_id", "")
    event = data.get("hook_event_name", "UserPromptSubmit")
    transcript = data.get("transcript_path", "")
    marker = LIFEBOAT_DIR / f"{session}.pending"
    snap = LIFEBOAT_DIR / f"{session}.md"

    # Restore path: inject once after compaction, whichever event fires first.
    if session and marker.exists() and snap.exists():
        content = snap.read_text(encoding="utf-8", errors="replace")
        marker.unlink(missing_ok=True)
        ctx = (
            "Context was just compacted. Lifeboat snapshot of in-flight state "
            "taken right before compaction — treat this as authoritative for "
            "what we were doing, then continue the task:\n\n" + content
        )
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": event,
                "additionalContext": ctx,
            }
        }))
        sys.exit(0)

    # Early-save path: only meaningful on prompt submit with a transcript.
    if event == "UserPromptSubmit" and session and transcript and os.path.exists(transcript):
        used = last_context_tokens(transcript)
        if used > 0:
            window = 1_000_000 if used > 210_000 else 200_000
            if used / window >= THRESHOLD:
                try:
                    subprocess.run(
                        ["python3", str(SAVE), "--no-pending"],
                        input=json.dumps(data), text=True, capture_output=True, timeout=15,
                    )
                except Exception:
                    pass
    sys.exit(0)


if __name__ == "__main__":
    main()
