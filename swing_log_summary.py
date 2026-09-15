"""Summarize what swing-pullback mode did in each tester run, from the tester agent log.

Usage: python swing_log_summary.py HH:MM   (only runs that started at/after this real time today)

Per run with InpEntryMode=1: bias checks and their outcome, orders placed / filled / cancelled,
and every skip reason, plus a few sample placement lines to sanity-check prices.
"""
import re
import sys
from collections import Counter

AGENT_LOG = r"C:\Users\Benja\AppData\Roaming\MetaQuotes\Tester\53785E099C927DB68A545C249CDBCE06\Agent-127.0.0.1-3000\logs\20260915.log"

SKIPS = {
    "no usable swing": "no usable swing",
    "Swing: skip, reward": "reward < min R:R",
    "Swing: skip, free margin": "free margin",
    "Swing: skip, spread": "spread too wide",
    "Swing: skip, outside session": "outside session",
    "Swing: skip, not enough margin": "lot/margin",
    "Swing: order failed": "order failed",
    "Swing: ATR not ready": "ATR not ready",
}


def main():
    since = sys.argv[1] if len(sys.argv) > 1 else "00:00"
    text = open(AGENT_LOG, encoding="utf-16", errors="replace").read()
    runs, cur = [], None
    for raw in text.splitlines():
        f = raw.split("\t")
        if len(f) < 5:
            continue
        rt, msg = f[2], f[4]
        if "testing of" in msg and "started with inputs" in msg:
            m = re.search(r"from (\d{4}\.\d{2}\.\d{2})", msg)
            cur = {"start": rt, "from": m.group(1) if m else "?", "mode": None, "bias": Counter(),
                   "placed": 0, "cancelled": 0, "triggered": 0, "skips": Counter(), "samples": []}
            if rt >= since:
                runs.append(cur)
            continue
        if cur is None or rt < since:
            continue
        if msg.strip().startswith("InpEntryMode="):
            cur["mode"] = msg.strip().split("=", 1)[1]
        elif "Swing bias:" in msg:
            b = re.search(r"-> (-?\d)", msg)
            cur["bias"][{"1": "BUY", "-1": "SELL", "0": "WAIT"}.get(b.group(1) if b else "", "?")] += 1
        elif "Swing: placed" in msg:
            cur["placed"] += 1
            if len(cur["samples"]) < 3:
                cur["samples"].append(msg.strip())
        elif "Swing: cancelled unfilled" in msg:
            cur["cancelled"] += 1
        elif re.search(r"(buy|sell) limit .*triggered", msg):
            cur["triggered"] += 1
        else:
            for key, label in SKIPS.items():
                if key in msg:
                    cur["skips"][label] += 1
                    break

    swing_runs = [r for r in runs if r["mode"] == "1"]
    print(f"runs since {since}: {len(runs)} total, {len(swing_runs)} in swing mode\n")
    for r in swing_runs:
        checks = sum(r["bias"].values())
        print(f"week from {r['from']} (started {r['start']}): {checks} bias checks -> "
              f"BUY {r['bias']['BUY']}, SELL {r['bias']['SELL']}, WAIT {r['bias']['WAIT']}")
        print(f"  orders placed {r['placed']}, filled {r['triggered']}, cancelled unfilled {r['cancelled']}")
        print(f"  skips: {dict(r['skips']) if r['skips'] else 'none'}")
        for s in r["samples"]:
            print(f"  sample: {s}")
        print()


if __name__ == "__main__":
    main()
