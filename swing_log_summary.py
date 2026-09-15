"""Summarize what swing-pullback mode did in each tester run, from the tester agent logs.

Usage: python swing_log_summary.py HH:MM [HH:MM] [YYYYMMDD]
  runs that started in this real-time window on that day (default: today's log files)

MT5 can switch to another local agent mid-session (e.g. when one agent's log grows very large), so
every Agent-*/logs/<day>.log is read. Per run with InpEntryMode=1: bias checks and their outcome,
orders placed / kept / filled / cancelled (with reasons), every skip reason, and sample placements.
"""
import glob
import os
import re
import sys
from collections import Counter
from datetime import datetime

TESTER_DIR = r"C:\Users\Benja\AppData\Roaming\MetaQuotes\Tester\53785E099C927DB68A545C249CDBCE06"

SKIPS = {
    "no swing within": "swing too far",
    "no usable swing": "no usable swing",
    "Swing: skip, reward": "reward < min R:R",
    "Swing: skip, free margin": "free margin",
    "Swing: skip, spread": "spread too wide",
    "Swing: skip, outside session": "outside session",
    "Swing: skip, not enough margin": "lot/margin",
    "Swing: order failed": "order failed",
    "Swing: ATR not ready": "ATR not ready",
}


def parse_log(path, since, until):
    text = open(path, encoding="utf-16", errors="replace").read()
    runs, cur = [], None
    for raw in text.splitlines():
        f = raw.split("\t")
        if len(f) < 5:
            continue
        rt, msg = f[2], f[4]
        if "testing of" in msg and "started with inputs" in msg:
            m = re.search(r",(\w+): testing of .* from (\d{4}\.\d{2}\.\d{2})", msg)
            cur = {"start": rt, "tf": m.group(1) if m else "?", "from": m.group(2) if m else "?", "mode": None,
                   "bias": Counter(), "placed": 0, "kept": 0, "cancelled": 0, "cancel_reasons": Counter(),
                   "triggered": 0, "skips": Counter(), "samples": [], "style": "0", "armed": 0, "kept_armed": 0,
                   "sweeps": 0, "disarmed": Counter(), "confirm_entries": 0}
            if since <= rt[:5] <= until:
                runs.append(cur)
            continue
        if cur is None:
            continue
        s = msg.strip()
        if s.startswith("InpEntryMode="):
            cur["mode"] = s.split("=", 1)[1]
        elif s.startswith("InpSwingEntryStyle="):
            cur["style"] = s.split("=", 1)[1]
        elif "Swing: armed" in msg:
            cur["armed"] += 1
            if len(cur["samples"]) < 3:
                cur["samples"].append(s)
        elif "Swing: keeping armed" in msg:
            cur["kept_armed"] += 1
        elif "Swing: sweep started" in msg:
            cur["sweeps"] += 1
        elif "Swing: disarmed" in msg:
            r = re.search(r"\(([^)]+)\)\s*$", msg)
            reason = r.group(1) if r else "?"
            if reason.startswith("reward"):
                reason = "reward < min R:R at confirmation"
            elif reason.startswith("order failed"):
                reason = "order failed"
            cur["disarmed"][reason.split(":")[0]] += 1
        elif "Swing confirm: entered" in msg:
            cur["confirm_entries"] += 1
        elif "Swing bias:" in msg:
            b = re.search(r"-> (-?\d)", msg)
            cur["bias"][{"1": "BUY", "-1": "SELL", "0": "WAIT"}.get(b.group(1) if b else "", "?")] += 1
        elif "Swing: placed" in msg:
            cur["placed"] += 1
            if len(cur["samples"]) < 3:
                cur["samples"].append(s)
        elif "Swing: keeping pending" in msg:
            cur["kept"] += 1
        elif "Swing: cancelled unfilled" in msg:
            cur["cancelled"] += 1
            r = re.search(r"\(([^)]+)\)\s*$", msg)
            cur["cancel_reasons"][r.group(1) if r else "hourly re-plan"] += 1
        elif re.search(r"(buy|sell) limit .*triggered", msg):
            cur["triggered"] += 1
        else:
            for key, label in SKIPS.items():
                if key in msg:
                    cur["skips"][label] += 1
                    break
    return runs


def main():
    since = sys.argv[1] if len(sys.argv) > 1 else "00:00"
    until = sys.argv[2] if len(sys.argv) > 2 else "99:99"
    day = sys.argv[3] if len(sys.argv) > 3 else datetime.now().strftime("%Y%m%d")
    runs = []
    for path in sorted(glob.glob(os.path.join(TESTER_DIR, "Agent-*", "logs", f"{day}.log"))):
        runs += parse_log(path, since, until)
    runs.sort(key=lambda r: r["start"])

    swing_runs = [r for r in runs if r["mode"] == "1"]
    print(f"runs started {since}-{until} on {day}: {len(runs)} total, {len(swing_runs)} in swing mode\n")
    for r in swing_runs:
        checks = sum(r["bias"].values())
        print(f"week from {r['from']} ({r['tf']} chart, started {r['start']}): {checks} bias checks -> "
              f"BUY {r['bias']['BUY']}, SELL {r['bias']['SELL']}, WAIT {r['bias']['WAIT']}")
        print(f"  orders placed {r['placed']}, kept at a check {r['kept']}, filled {r['triggered']}, "
              f"cancelled unfilled {r['cancelled']} {dict(r['cancel_reasons']) if r['cancel_reasons'] else ''}")
        if r["style"] == "1" or r["armed"]:
            print(f"  confirm style: armed {r['armed']}, kept armed at a check {r['kept_armed']}, sweeps {r['sweeps']}, "
                  f"entries {r['confirm_entries']}, disarmed {dict(r['disarmed']) if r['disarmed'] else 0}")
        print(f"  skips: {dict(r['skips']) if r['skips'] else 'none'}")
        for smp in r["samples"]:
            print(f"  sample: {smp}")
        print()


if __name__ == "__main__":
    main()
