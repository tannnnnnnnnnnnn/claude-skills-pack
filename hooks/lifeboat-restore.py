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


def newest_snapshot_for_cwd(cwd, exclude="", max_age=24 * 3600):
    """Most recent snapshot .md whose recorded cwd matches, within max_age."""
    if not cwd:
        return None
    best, best_ts = None, 0
    now = __import__("time").time()
    for meta in LIFEBOAT_DIR.glob("*.meta"):
        if meta.stem == exclude:
            continue
        try:
            m = json.loads(meta.read_text())
        except Exception:
            continue
        if m.get("cwd") != cwd:
            continue
        ts = m.get("ts", 0)
        if now - ts > max_age:
            continue
        md = LIFEBOAT_DIR / f"{meta.stem}.md"
        if md.exists() and ts > best_ts:
            best, best_ts = md, ts
    return best


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

    # New-window handoff: a fresh session in a project auto-loads the most
    # recent snapshot from that SAME project (different prior session, <24h).
    if event == "SessionStart" and data.get("source") in ("startup", "clear", "resume"):
        picked = newest_snapshot_for_cwd(data.get("cwd", ""), exclude=session)
        if picked:
            offered = LIFEBOAT_DIR / f"{session}.offered"
            if not offered.exists():
                offered.write_text("1")
                content = picked.read_text(encoding="utf-8", errors="replace")
                print(json.dumps({"hookSpecificOutput": {
                    "hookEventName": event,
                    "additionalContext": (
                        "New session in a project with a recent lifeboat snapshot from "
                        "an earlier chat. Continue from where that work left off:\n\n" + content
                    ),
                }}))
        sys.exit(0)

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

    # Early-save + context-cost warning: prompt submit with a transcript.
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
            # Context-cost nudge: fire once per threshold band crossed.
            warn = context_warning(session, used)
            if warn:
                print(json.dumps({
                    "hookSpecificOutput": {
                        "hookEventName": event,
                        "additionalContext": warn,
                    }
                }))
    sys.exit(0)


WARN_STATE = LIFEBOAT_DIR / ".warned"
BANDS = [(600_000, "600k"), (350_000, "350k")]


def context_warning(session, used):
    """Return a one-line nudge the first time this session crosses a band."""
    band = next((tok for tok, _ in BANDS if used >= tok), 0)
    if not band:
        return None
    try:
        seen = json.loads(WARN_STATE.read_text()) if WARN_STATE.exists() else {}
    except Exception:
        seen = {}
    if seen.get(session, 0) >= band:
        return None
    seen[session] = band
    try:
        LIFEBOAT_DIR.mkdir(parents=True, exist_ok=True)
        WARN_STATE.write_text(json.dumps(seen))
    except Exception:
        pass
    label = dict(BANDS)[band]
    eff = int(used * 0.1)
    return (
        f"[budget nudge] This session is at ~{label} context — every message now "
        f"re-reads it (~{eff:,} effective tokens/turn against the weekly limit). "
        "For heavy work from here, consider /clear to start fresh (lifeboat preserves "
        "state), or route coding-heavy work through /manager → Codex (separate quota). "
        "Surface this to the user briefly."
    )


if __name__ == "__main__":
    main()
