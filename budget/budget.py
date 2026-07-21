#!/usr/bin/env python3
"""Budget backbone for the /estimate skill and the context-cost warning.

Measures token usage since the weekly reset (and the rolling 5h window) from
local transcripts — zero API cost — and reports it against the calibrated
ceiling. Also reports the current session's live context size.

Usage:
  budget.py usage                 -> JSON: weekly/5h used, ceiling, pct, remaining
  budget.py context <transcript>  -> JSON: current context tokens for that session
  budget.py recalibrate <weekly_pct>  -> update ceiling from a fresh UI reading
"""
import calendar
import glob
import json
import os
import subprocess
import sys
import time

CFG = os.path.expanduser("~/.claude/budget/calibration.json")
PROJECTS = os.path.expanduser("~/.claude/projects/*/*.jsonl")


def cfg():
    with open(CFG) as f:
        return json.load(f)


def epoch_utc(ts):
    try:
        return calendar.timegm(time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S"))
    except Exception:
        return None


def last_weekly_reset(now):
    """Most recent Saturday 03:29 local, as a UTC epoch."""
    lt = time.localtime(now)
    days_since_sat = (lt.tm_wday - 5) % 7
    reset = time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, 3, 29, 0, 0, 0, -1)) - days_since_sat * 86400
    if reset > now:
        reset -= 7 * 86400
    return reset


def weighted(u, cw):
    fresh = u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("output_tokens", 0)
    return fresh + u.get("cache_read_input_tokens", 0) * cw


def measure(cw):
    now = float(subprocess.run(["date", "+%s"], capture_output=True, text=True).stdout or time.time())
    wk_start = last_weekly_reset(now)
    h5_start = now - 5 * 3600
    wk = h5 = 0.0
    for f in glob.glob(PROJECTS):
        if os.path.getmtime(f) < wk_start:
            continue
        try:
            lines = open(f, encoding="utf-8", errors="replace").read().splitlines()
        except Exception:
            continue
        for line in lines:
            try:
                d = json.loads(line)
            except Exception:
                continue
            u = (d.get("message") or {}).get("usage")
            if not u:
                continue
            e = epoch_utc(d.get("timestamp", "")) or os.path.getmtime(f)
            val = weighted(u, cw)
            if e >= wk_start:
                wk += val
            if e >= h5_start:
                h5 += val
    return wk, h5


def context_tokens(transcript):
    try:
        size = os.path.getsize(transcript)
        with open(transcript, "rb") as fh:
            fh.seek(max(0, size - 400_000))
            tail = fh.read().decode("utf-8", errors="replace").splitlines()
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
    if len(sys.argv) < 2:
        print("usage: budget.py {usage|context <transcript>|recalibrate <pct>}")
        return
    cmd = sys.argv[1]
    c = cfg()
    cw = c.get("cache_weight", 0.1)

    if cmd == "usage":
        wk, h5 = measure(cw)
        ceil_wk = c.get("ceiling_weekly_effective") or 1
        # 5h ceiling implied by the weekly checkpoint pair, else derive from a stored 5h ceiling
        ceil_5h = c.get("ceiling_5h_effective")
        out = {
            "cache_weight": cw,
            "weekly_used": round(wk),
            "weekly_ceiling": ceil_wk,
            "weekly_pct": round(100 * wk / ceil_wk, 1),
            "weekly_remaining": round(ceil_wk - wk),
            "fivehour_used": round(h5),
        }
        if ceil_5h:
            out["fivehour_pct"] = round(100 * h5 / ceil_5h, 1)
            out["fivehour_remaining"] = round(ceil_5h - h5)
        print(json.dumps(out, indent=2))

    elif cmd == "context":
        t = sys.argv[2] if len(sys.argv) > 2 else ""
        print(json.dumps({"context_tokens": context_tokens(t)}))

    elif cmd == "recalibrate":
        pct = float(sys.argv[2])
        wk, h5 = measure(cw)
        c["ceiling_weekly_effective"] = round(wk / (pct / 100))
        c.setdefault("checkpoints", []).append({
            "date": time.strftime("%Y-%m-%d"), "weekly_all_pct": pct,
            "measured_weekly": round(wk),
        })
        with open(CFG, "w") as f:
            json.dump(c, f, indent=2)
        print(f"recalibrated: ceiling_weekly_effective = {c['ceiling_weekly_effective']:,}")


if __name__ == "__main__":
    main()
