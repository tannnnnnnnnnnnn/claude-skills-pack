#!/usr/bin/env python3
"""Budget backbone for the /estimate skill and the context-cost warning.

Measures token usage since the weekly reset (and the rolling 5h window) from
local transcripts — zero API cost — and reports it against the calibrated
ceiling. Also reports the current session's live context size.

The plan enforces more than one weekly meter: an all-models pool plus a
tighter per-family pool (Fable). They are independent, so the binding one is
whichever sits highest — not the pooled total.

Usage:
  budget.py usage                 -> JSON: per-meter used, ceiling, pct, remaining
  budget.py context <transcript>  -> JSON: current context tokens for that session
  budget.py recalibrate <all_pct> [fable_pct]  -> update ceilings from a fresh UI reading
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


# Each meter is a substring matched against the message's model id. "all"
# matches every model. Adding a meter here plus a ceiling in calibration.json
# is all a new plan-side limit needs.
METERS = {"all": "", "fable": "fable"}


def meters_for(model):
    return [name for name, needle in METERS.items() if not needle or needle in model]


def measure(cw):
    """Per-meter effective tokens for the week and the rolling 5h window."""
    now = float(subprocess.run(["date", "+%s"], capture_output=True, text=True).stdout or time.time())
    wk_start = last_weekly_reset(now)
    h5_start = now - 5 * 3600
    wk = {name: 0.0 for name in METERS}
    h5 = {name: 0.0 for name in METERS}
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
            m = d.get("message") or {}
            u = m.get("usage")
            if not u:
                continue
            e = epoch_utc(d.get("timestamp", "")) or os.path.getmtime(f)
            val = weighted(u, cw)
            names = meters_for(m.get("model") or "")
            for name in names:
                if e >= wk_start:
                    wk[name] += val
                if e >= h5_start:
                    h5[name] += val
    return wk, h5


def ceilings(c):
    """Per-meter weekly ceilings, honouring the pre-meter config key."""
    stored = dict(c.get("ceilings_weekly_effective") or {})
    if "all" not in stored and c.get("ceiling_weekly_effective"):
        stored["all"] = c["ceiling_weekly_effective"]
    return stored


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
        ceils = ceilings(c)
        meters = {}
        for name, used in wk.items():
            ceil = ceils.get(name)
            if not ceil:
                continue
            meters[name] = {
                "used": round(used),
                "ceiling": ceil,
                "pct": round(100 * used / ceil, 1),
                "remaining": round(ceil - used),
            }
        # Independent limits: the binding one is whichever is furthest along,
        # and it alone decides what is still affordable.
        binding = max(meters, key=lambda n: meters[n]["pct"], default="all")
        alln = meters.get("all", {})
        out = {
            "cache_weight": cw,
            "meters": meters,
            "binding": binding,
            "binding_pct": meters.get(binding, {}).get("pct"),
            "binding_remaining": meters.get(binding, {}).get("remaining"),
            "weekly_used": alln.get("used", round(wk["all"])),
            "weekly_ceiling": alln.get("ceiling"),
            "weekly_pct": alln.get("pct"),
            "weekly_remaining": alln.get("remaining"),
            "fivehour_used": round(h5["all"]),
        }
        ceil_5h = c.get("ceiling_5h_effective")
        if ceil_5h:
            out["fivehour_pct"] = round(100 * h5["all"] / ceil_5h, 1)
            out["fivehour_remaining"] = round(ceil_5h - h5["all"])
        print(json.dumps(out, indent=2))

    elif cmd == "context":
        t = sys.argv[2] if len(sys.argv) > 2 else ""
        print(json.dumps({"context_tokens": context_tokens(t)}))

    elif cmd == "recalibrate":
        pcts = {"all": float(sys.argv[2])}
        if len(sys.argv) > 3:
            pcts["fable"] = float(sys.argv[3])
        wk, h5 = measure(cw)
        stored = ceilings(c)
        checkpoint = {"date": time.strftime("%Y-%m-%d")}
        for name, pct in pcts.items():
            stored[name] = round(wk[name] / (pct / 100))
            checkpoint[f"weekly_{name}_pct"] = pct
            checkpoint[f"measured_{name}"] = round(wk[name])
        c["ceilings_weekly_effective"] = stored
        c.pop("ceiling_weekly_effective", None)
        c.setdefault("checkpoints", []).append(checkpoint)
        with open(CFG, "w") as f:
            json.dump(c, f, indent=2)
        for name in pcts:
            print(f"recalibrated: {name} ceiling = {stored[name]:,}")


if __name__ == "__main__":
    main()
