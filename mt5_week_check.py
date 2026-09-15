"""Run 3 random Aug/Sep 2026 weeks through MT5's real Strategy Tester with the user's exact
inputs (copied from the visual-check ini), then print per-week results and a loss diagnosis.

Weeks are drawn with SystemRandom and printed before any test runs.
"""
import os
import random
import re
import subprocess
import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

import mt5_deep_parse as dp

TERMINAL_EXE = r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe"
DATA_PATH = r"C:\Users\Benja\AppData\Roaming\MetaQuotes\Terminal\53785E099C927DB68A545C249CDBCE06"
SCRATCH = os.path.dirname(os.path.abspath(__file__))
INI_DIR = os.path.join(SCRATCH, "ini_runs")
BASE_INI = os.path.join(INI_DIR, "visualcheck_H1_20260907.ini")
PRIOR_REPORT = os.path.join(SCRATCH, "2026-09-07_to_2026-09-10__H1visual.htm")

CANDIDATE_MONDAYS = [datetime(2026, 8, 3), datetime(2026, 8, 10), datetime(2026, 8, 17),
                     datetime(2026, 8, 24), datetime(2026, 8, 31)]  # Sep 7 week already tested


def make_ini(start, end, report):
    s = open(BASE_INI, encoding="utf-8").read()
    for key, val in (("FromDate", f"{start:%Y.%m.%d}"), ("ToDate", f"{end:%Y.%m.%d}"),
                     ("Visual", "0"), ("Report", report), ("ShutdownTerminal", "1")):
        s, n = re.subn(rf"^{key}=.*$", f"{key}={val}", s, flags=re.M)
        assert n == 1, f"{key} not found exactly once in base ini"
    path = os.path.join(INI_DIR, report + ".ini")
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)
    return path


def run_test(ini, report):
    report_path = os.path.join(DATA_PATH, report + ".htm")
    if os.path.exists(report_path):
        os.remove(report_path)
    subprocess.run(["taskkill", "/IM", "terminal64.exe", "/F"], capture_output=True)
    time.sleep(3)
    t0 = time.time()
    subprocess.run([TERMINAL_EXE, f"/config:{ini}"], timeout=900)
    subprocess.run(["taskkill", "/IM", "terminal64.exe", "/F"], capture_output=True)
    return (report_path if os.path.exists(report_path) else None), time.time() - t0


def streak(mask):
    best = cur = 0
    for m in mask:
        cur = cur + 1 if m else 0
        best = max(best, cur)
    return best


def week_stats(t):
    p = t["pnl"].to_numpy()
    w, l = p[p > 0], p[p <= 0]
    bal = t["balance_after"].to_numpy()
    peak = np.maximum.accumulate(np.concatenate([[100.0], bal]))[1:]
    days = max(1, t["entry_time"].dt.normalize().nunique())
    return {
        "trades": len(p), "wins": len(w), "losses": len(l),
        "win%": len(w) / len(p) * 100 if len(p) else 0.0,
        "net$": p.sum(), "PF": w.sum() / abs(l.sum()) if l.sum() != 0 else np.inf,
        "end$": bal[-1] if len(bal) else 100.0,
        "maxDD%": ((peak - bal) / peak * 100).max() if len(bal) else 0.0,
        "avgW$": w.mean() if len(w) else 0.0, "avgL$": l.mean() if len(l) else 0.0,
        "maxLossRun": streak(p <= 0), "trades/day": len(p) / days,
        "SLexits": int((t["exit_kind"] == "sl").sum()),
        "TP3exits": int(((t["exit_kind"] == "other") & (t["pnl"] > 0)).sum()),
        "buys": int((t["dir"] == "BUY").sum()), "sells": int((t["dir"] == "SELL").sum()),
    }


def main():
    rng = random.SystemRandom()
    weeks = sorted(rng.sample(CANDIDATE_MONDAYS, 3))
    print("RANDOMLY SELECTED WEEKS (SystemRandom, chosen before any test ran):")
    for w in weeks:
        print(f"  {w:%Y-%m-%d} (Mon) -> {w + timedelta(days=4):%Y-%m-%d} (Fri)")
    print(flush=True)

    frames = []
    if os.path.exists(PRIOR_REPORT):
        prior = dp.parse_one(PRIOR_REPORT)
        prior["week"] = "2026-09-07 (Mon-Thu, prior run)"
        frames.append(prior)

    for w in weeks:
        report = f"wk_{w:%Y-%m-%d}__M15sig"
        ini = make_ini(w, w + timedelta(days=5), report)
        print(f"running {report} ...", flush=True)
        path, secs = run_test(ini, report)
        if path is None:
            print(f"  FAILED: no report after {secs:.0f}s", flush=True)
            continue
        t = dp.parse_one(path)
        t["week"] = f"{w:%Y-%m-%d} (Mon-Fri)"
        frames.append(t)
        print(f"  done in {secs:.0f}s, {len(t)} trades", flush=True)

    allt = pd.concat(frames, ignore_index=True)
    allt["entry_time"] = pd.to_datetime(allt["entry_time"])
    allt["exit_time"] = pd.to_datetime(allt["exit_time"])
    allt.to_csv(os.path.join(SCRATCH, "week_check_trades.csv"), index=False)

    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    rows = {wk: week_stats(g.sort_values("entry_time")) for wk, g in allt.groupby("week", sort=False)}
    rows["ALL POOLED"] = week_stats(allt)
    print("\n=== PER-WEEK RESULTS ($100 start each week, user's exact inputs, real ticks) ===")
    print(pd.DataFrame(rows).T.round(2).to_string())

    p = allt["pnl"]
    losers, winners = allt[p <= 0], allt[p > 0]
    print("\n=== WHY TRADES LOSE (pooled) ===")
    r = losers["r_multiple"]
    print(f"losers: {len(losers)} | full stop-outs (<= -0.9R): {(r <= -0.9).sum()} | "
          f"trail-cushioned (-0.9..-0.3R): {((r > -0.9) & (r <= -0.3)).sum()} | near breakeven (> -0.3R): {(r > -0.3).sum()}")
    h = losers["hold_minutes"]
    print(f"loser hold time: <=15min {(h <= 15).mean()*100:.0f}% | <=30min {(h <= 30).mean()*100:.0f}% | "
          f"<=60min {(h <= 60).mean()*100:.0f}% | median {h.median():.0f}min")
    print(f"winner hold time: median {winners['hold_minutes'].median():.0f}min | "
          f"winners reaching >=1R: {(winners['r_multiple'] >= 1).sum()} of {len(winners)}")

    gaps, outcomes = [], []
    for _, g in allt.sort_values("entry_time").groupby("week", sort=False):
        g = g.reset_index(drop=True)
        for i in range(1, len(g)):
            if g.loc[i - 1, "pnl"] <= 0:
                gaps.append((g.loc[i, "entry_time"] - g.loc[i - 1, "exit_time"]).total_seconds() / 60)
                outcomes.append(g.loc[i, "pnl"] > 0)
    gaps, outcomes = np.array(gaps), np.array(outcomes)
    quick = gaps <= 15
    if len(gaps):
        print(f"re-entry after a loss: {quick.mean()*100:.0f}% re-entered within 15min | "
              f"win rate of those quick re-entries {outcomes[quick].mean()*100 if quick.any() else 0:.0f}% "
              f"vs later re-entries {outcomes[~quick].mean()*100 if (~quick).any() else 0:.0f}%")

    allt["block"] = (allt["entry_time"].dt.hour // 4 * 4).map(lambda b: f"{b:02d}-{b+4:02d}h")
    blk = allt.groupby("block").agg(trades=("pnl", "size"), win_pct=("pnl", lambda s: (s > 0).mean() * 100),
                                    net=("pnl", "sum")).round(1)
    print("\nby entry hour (server time):")
    print(blk.to_string())
    dirs = allt.groupby("dir").agg(trades=("pnl", "size"), win_pct=("pnl", lambda s: (s > 0).mean() * 100),
                                   net=("pnl", "sum")).round(1)
    print("\nby direction:")
    print(dirs.to_string())


if __name__ == "__main__":
    main()
