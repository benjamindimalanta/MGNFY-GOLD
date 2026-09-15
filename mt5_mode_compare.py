"""Compare the two entry modes on the same weeks through MT5's real Strategy Tester.

Full Mon-Fri weeks, the user's inputs from the base ini, $500 deposit (so the ~$53 margin floor of a
$100 account doesn't cut weeks short). Only InpEntryMode differs between the two runs of each week,
plus any EXTRA_INPUTS applied to both.

Environment:
  WEEK_START=YYYY-MM-DD  first Monday of a custom range (with WEEK_COUNT, default 4)
  WEEKS=4                the 4 diagnosis weeks (Aug 10, Aug 17, Aug 31, Sep 7) -- default
  WEEKS=12               every full week Jun 22 - Sep 11
  TAG=...                suffix for the trades CSV and report names, so batches don't overwrite each other
  EXTRA_INPUTS="Name=value;Name2=value2"
                         EA input overrides for this batch; replaces the base ini line or appends one.
                         Check the tester log's "started with inputs" list to confirm they took effect.
Arguments: optional mode names to run only those (breakout, swing).
"""
import os
import re
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

import mt5_deep_parse as dp
from mt5_week_check import BASE_INI, INI_DIR, run_test

if os.environ.get("WEEK_START"):
    _first = datetime.strptime(os.environ["WEEK_START"], "%Y-%m-%d")
    WEEKS = [_first + timedelta(weeks=i) for i in range(int(os.environ.get("WEEK_COUNT", "4")))]
elif os.environ.get("WEEKS", "4") == "12":
    WEEKS = [datetime(2026, 6, 22) + timedelta(weeks=i) for i in range(12)]
else:
    WEEKS = [datetime(2026, 8, 10), datetime(2026, 8, 17), datetime(2026, 8, 31), datetime(2026, 9, 7)]
TAG = os.environ.get("TAG", "")
EXTRA_INPUTS = [kv.strip() for kv in os.environ.get("EXTRA_INPUTS", "").split(";") if kv.strip()]
DEPOSIT = 500.0
MODES = {"breakout": 0, "swing": 1}
SCRATCH = os.path.dirname(os.path.abspath(__file__))


def set_input(ini_text, name, value):
    line = f"{name}={value}||{value}||0||{value}||N"
    new, n = re.subn(rf"^{re.escape(name)}=.*$", line, ini_text, flags=re.M)
    return new if n else ini_text.rstrip("\n") + "\n" + line + "\n"


def make_ini(start, end, report, mode_value):
    s = open(BASE_INI, encoding="utf-8").read()
    for key, val in (("FromDate", f"{start:%Y.%m.%d}"), ("ToDate", f"{end:%Y.%m.%d}"), ("Visual", "0"),
                     ("Report", report), ("ShutdownTerminal", "1"), ("Deposit", f"{DEPOSIT:.0f}")):
        s, n = re.subn(rf"^{key}=.*$", f"{key}={val}", s, flags=re.M)
        assert n == 1, f"{key} not found exactly once in base ini"
    s = s.rstrip("\n") + f"\nInpEntryMode={mode_value}||0||0||1||N\n"
    for kv in EXTRA_INPUTS:
        name, value = kv.split("=", 1)
        s = set_input(s, name.strip(), value.strip())
    path = os.path.join(INI_DIR, report + ".ini")
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)
    return path


def streak(mask):
    best = cur = 0
    for m in mask:
        cur = cur + 1 if m else 0
        best = max(best, cur)
    return best


def stats(t):
    if t.empty:
        return {"trades": 0, "wins": 0, "losses": 0, "win%": 0.0, "net$": 0.0, "PF": np.nan, "end$": DEPOSIT,
                "maxDD%": 0.0, "avgW$": 0.0, "avgL$": 0.0, "maxLossRun": 0, "trades/day": 0.0,
                "loser_median_min": np.nan, "SLexits": 0, "TP3exits": 0, "buys": 0, "sells": 0}
    t = t.sort_values("entry_time")
    p = t["pnl"].to_numpy()
    w, l = p[p > 0], p[p <= 0]
    bal = t["balance_after"].to_numpy()
    peak = np.maximum.accumulate(np.concatenate([[DEPOSIT], bal]))[1:]
    return {
        "trades": len(p), "wins": len(w), "losses": len(l), "win%": len(w) / len(p) * 100,
        "net$": p.sum(), "PF": w.sum() / abs(l.sum()) if l.sum() != 0 else np.inf, "end$": bal[-1],
        "maxDD%": ((peak - bal) / peak * 100).max(),
        "avgW$": w.mean() if len(w) else 0.0, "avgL$": l.mean() if len(l) else 0.0,
        "maxLossRun": streak(p <= 0), "trades/day": len(p) / 5.0,
        "loser_median_min": t.loc[t["pnl"] <= 0, "hold_minutes"].median(),
        "SLexits": int((t["exit_kind"] == "sl").sum()),
        "TP3exits": int(((t["exit_kind"] == "other") & (t["pnl"] > 0)).sum()),
        "buys": int((t["dir"] == "BUY").sum()), "sells": int((t["dir"] == "SELL").sum()),
    }


def main():
    only = sys.argv[1:]
    if EXTRA_INPUTS:
        print(f"EXTRA_INPUTS: {EXTRA_INPUTS}", flush=True)
    frames = []
    for w in WEEKS:
        for mode, value in MODES.items():
            if only and mode not in only:
                continue
            report = f"cmp{TAG}_{mode}_{w:%Y-%m-%d}__M15sig"
            ini = make_ini(w, w + timedelta(days=5), report, value)
            print(f"running {report} ...", flush=True)
            path, secs = run_test(ini, report)
            if path is None:
                print(f"  FAILED: no report after {secs:.0f}s", flush=True)
                continue
            t = dp.parse_one(path)
            t["mode"], t["week"] = mode, f"{w:%Y-%m-%d}"
            frames.append(t)
            print(f"  done in {secs:.0f}s, {len(t)} trades", flush=True)

    allt = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if allt.empty:
        print("no trades at all")
        return
    allt["entry_time"] = pd.to_datetime(allt["entry_time"])
    allt["exit_time"] = pd.to_datetime(allt["exit_time"])
    allt.to_csv(os.path.join(SCRATCH, f"mode_compare_trades{TAG}.csv"), index=False)

    pd.set_option("display.width", 260)
    pd.set_option("display.max_columns", 30)
    rows = {}
    for w in WEEKS:
        for mode in MODES:
            if only and mode not in only:
                continue
            sub = allt[(allt["mode"] == mode) & (allt["week"] == f"{w:%Y-%m-%d}")]
            rows[f"{mode:8s} {w:%Y-%m-%d}"] = stats(sub)
    for mode in MODES:
        if only and mode not in only:
            continue
        sub = allt[allt["mode"] == mode]
        pooled = stats(sub)
        pooled["end$"], pooled["maxDD%"], pooled["maxLossRun"] = np.nan, np.nan, np.nan
        pooled["trades/day"] = len(sub) / (5.0 * len(WEEKS))
        weekly = [stats(allt[(allt["mode"] == mode) & (allt["week"] == f"{w:%Y-%m-%d}")])["net$"] for w in WEEKS]
        pooled["weeks+"] = sum(1 for x in weekly if x > 0)
        pooled["weeks-"] = sum(1 for x in weekly if x < 0)
        rows[f"{mode:8s} ALL {len(WEEKS)} WEEKS"] = pooled
    print(f"\n=== MODE COMPARISON (${DEPOSIT:.0f} start each week, real ticks, user's inputs) ===")
    print(pd.DataFrame(rows).T.round(2).to_string())


if __name__ == "__main__":
    main()
