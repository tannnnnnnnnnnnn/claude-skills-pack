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


def newest_snapshot_for_cwd(cwd, max_age=24 * 3600):
    """Most recent snapshot .md whose recorded cwd matches, within max_age.

    Deliberately does NOT exclude the current session: /clear and /resume
    both preserve session_id (only a brand-new window gets a new one), so
    excluding "self" would hide a snapshot the same session just wrote
    moments ago via /lifeboat right before /clear.
    """
    if not cwd:
        return None
    best, best_ts = None, 0
    now = __import__("time").time()
    for meta in LIFEBOAT_DIR.glob("*.meta"):
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

    # Cross-session / cross-clear handoff: works identically for a brand-new
    # chat window (new session_id) and for /clear or /resume in the same
    # window (session_id typically persists across those) — either way we
    # look for the newest snapshot in this cwd and inject it if it's newer
    # than the last one this session_id already saw.
    if event == "SessionStart" and data.get("source") in ("startup", "clear", "resume"):
        picked = newest_snapshot_for_cwd(data.get("cwd", ""))
        if picked:
            picked_ts = picked.stat().st_mtime
            offers = LIFEBOAT_DIR / ".session-offers.json"
            try:
                seen = json.loads(offers.read_text()) if offers.exists() else {}
            except Exception:
                seen = {}
            if seen.get(session, 0) < picked_ts:
                seen[session] = picked_ts
                try:
                    LIFEBOAT_DIR.mkdir(parents=True, exist_ok=True)
                    offers.write_text(json.dumps(seen))
                except Exception:
                    pass
                content = picked.read_text(encoding="utf-8", errors="replace")
                print(json.dumps({"hookSpecificOutput": {
                    "hookEventName": event,
                    "additionalContext": (
                        "This project has a recent lifeboat snapshot (from this chat "
                        "before /clear, or from an earlier chat in the same folder). "
                        "Continue from where that work left off:\n\n" + content
                    ),
                }}))
                sys.exit(0)
        # Nothing new to offer via cwd-lookup — still check this session's own
        # pending compaction marker below (e.g. a /resume of a session that
        # compacted right before the app closed).

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
