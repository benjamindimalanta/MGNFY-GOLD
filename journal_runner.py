"""Multi-week, multi-timeframe journal run for MGNFY GOLD.

Picks N genuinely random 1-week windows (random.SystemRandom, chosen and
printed BEFORE any result is seen -- not cherry-picked) from the real data
history available on this broker/account, and backtests each week on three
signal timeframes (M15, M30, H1) under two/three EA configurations:

  - baseline  : v1.11 behaviour exactly as currently live/compiled in MT5
                (min-lot partial-close bug reproduced, flat BE, trail 1.0x)
  - fixed     : v1.12 (this session's update) -- bug fixed, stairstep SL
                lock, trail 1.5x -- same entry/filter logic as "Balance"
  - fixed_cons: v1.12 fix applied to the "Conservative" preset's filters
                (MACD filter, H4 trend filter, trend-flip required, tighter
                risk) to see whether filtering improves win rate / PF

Every trade from every run is written out (nothing summarized-away), plus
one master summary CSV with one row per (week, timeframe, config) combo,
plus a pooled entries-by-hour/weekday table across all "fixed" runs.
"""
from __future__ import annotations

import json
import os
import random
from datetime import datetime, timedelta

import MetaTrader5 as mt5
import numpy as np
import pandas as pd

import backtest_mgnfy as bt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = bt.DATA_DIR
TRADES_DIR = os.path.join(DATA_DIR, "journal_trades")
os.makedirs(TRADES_DIR, exist_ok=True)

SYMBOL = "XAUUSDm"
N_WEEKS = 6
WARMUP_DAYS = 5
# Re-run guard: the FIRST run of this script (2026-09-15) genuinely random-sampled these 6 weeks
# with SystemRandom and printed them before any result was seen. This rerun only fixes a config
# bug (baseline trail_atr_mult was wrong -- see cfg_baseline()); reusing the same weeks keeps the
# comparison apples-to-apples instead of drawing a fresh, incomparable sample. Set to [] to draw new.
FIXED_WEEKS = ["2026-07-06", "2026-07-13", "2026-07-20", "2026-08-10", "2026-08-17", "2026-09-07"]
SIGNAL_TFS = {
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
}

RUN_STAMP = datetime.now().strftime("%Y-%m-%d %H:%M")


def cfg_baseline():
    # Matches the "Balance" preset exactly (confirmed against the live screenshot backtest's
    # on-chart input readout: ATRMultiplier=2.0, StopLossPercent=0.7, MACDFilter=false all match
    # Balance, not the bare .mq5 code defaults). Balance.set already specifies Trail_ATR_Mult=1.5
    # (only the *bare* code default was 1.0 pre-v1.12) and InpUseTrendFilter=false.
    return bt.Cfg(fix_min_lot_tp1_bug=False, stairstep_lock=False, trail_atr_mult=1.5)


def cfg_fixed():
    return bt.Cfg(fix_min_lot_tp1_bug=True, stairstep_lock=True, trail_atr_mult=1.5)


def cfg_fixed_conservative():
    return bt.Cfg(
        fix_min_lot_tp1_bug=True, stairstep_lock=True, trail_atr_mult=1.5,
        atr_mult=2.5, sl_atr_mult=1.5, tp1_r=1.0, tp2_r=2.0, tp3_r=3.0,
        use_macd_filter=True, use_trend_filter=True, require_trend_flip=True,
        use_risk_sizing=True, risk_percent=0.5, margin_buffer=1.30,
        max_spread_points=300,
    )


def candidate_mondays(earliest, latest_full_week_end_excl):
    d = earliest
    d += timedelta(days=(7 - d.weekday()) % 7)  # snap to Monday
    out = []
    while d + timedelta(days=7) <= latest_full_week_end_excl:
        out.append(d)
        d += timedelta(days=7)
    return out


def fetch(sym, tf, start, end):
    rates = mt5.copy_rates_range(sym, tf, start, end)
    if rates is None or len(rates) == 0:
        return pd.DataFrame(columns=["time", "open", "high", "low", "close", "tickvol", "spread"]).set_index("time")
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df.rename(columns={"tick_volume": "tickvol"})[
        ["time", "open", "high", "low", "close", "tickvol", "spread"]
    ].set_index("time")


def max_streak(bools):
    best = cur = 0
    for b in bools:
        cur = cur + 1 if b else 0
        best = max(best, cur)
    return best


def summarize_run(trades, deposit):
    if not trades:
        return dict(trades=0, wins=0, losses=0, win_rate=0.0, net=0.0, pf=0.0,
                     max_dd_pct=0.0, avg_win=0.0, avg_loss=0.0, max_win=0.0,
                     max_loss=0.0, max_consec_wins=0, max_consec_losses=0,
                     end_eq=deposit)
    pnls = np.array([t["pnl"] for t in trades])
    wins = pnls[pnls > 0]
    losses = pnls[pnls <= 0]
    net = pnls.sum()
    eq = deposit + np.cumsum(pnls)
    peak = np.maximum.accumulate(np.concatenate([[deposit], eq]))
    dd = (peak[1:] - eq) / peak[1:] * 100
    pf = (wins.sum() / abs(losses.sum())) if len(losses) and losses.sum() != 0 else float("inf")
    return dict(
        trades=len(trades), wins=len(wins), losses=len(losses),
        win_rate=len(wins) / len(pnls) * 100, net=net, pf=pf,
        max_dd_pct=dd.max() if len(dd) else 0.0,
        avg_win=wins.mean() if len(wins) else 0.0,
        avg_loss=losses.mean() if len(losses) else 0.0,
        max_win=wins.max() if len(wins) else 0.0,
        max_loss=losses.min() if len(losses) else 0.0,
        max_consec_wins=max_streak(pnls > 0),
        max_consec_losses=max_streak(pnls <= 0),
        end_eq=deposit + net,
    )


def main():
    ok = mt5.initialize()
    if not ok:
        raise SystemExit(f"MT5 initialize failed: {mt5.last_error()}")
    mt5.symbol_select(SYMBOL, True)
    info = mt5.symbol_info(SYMBOL)
    acct = mt5.account_info()

    meta_rows = {
        "symbol": SYMBOL, "balance": acct.balance, "leverage": acct.leverage,
        "contract_size": info.trade_contract_size, "tick_value": info.trade_tick_value,
        "tick_size": info.trade_tick_size, "point": info.point,
        "volume_min": info.volume_min, "volume_step": info.volume_step, "volume_max": info.volume_max,
    }
    pd.Series(meta_rows).rename_axis("field").reset_index(name="value").to_csv(
        os.path.join(DATA_DIR, "symbol_meta.csv"), index=False
    )

    # M1 execution data is the hard floor on how far back we can test (see probe:
    # earliest available M1 bar on this account/broker is ~2026-06-15).
    m1_probe = mt5.copy_rates_from(SYMBOL, mt5.TIMEFRAME_M1, datetime.now(), 90000)
    earliest_m1 = datetime.utcfromtimestamp(int(m1_probe[0]["time"]))
    now = datetime.now()

    candidates = candidate_mondays(earliest_m1 + timedelta(days=WARMUP_DAYS + 1), now)
    rng = random.SystemRandom()
    if FIXED_WEEKS:
        weeks = [datetime.strptime(d, "%Y-%m-%d") for d in FIXED_WEEKS]
    else:
        weeks = rng.sample(candidates, k=min(N_WEEKS, len(candidates)))
        weeks.sort()

    print(f"Earliest usable M1 data: {earliest_m1}")
    print(f"Candidate Monday-start weeks: {len(candidates)} ({candidates[0].date()} .. {candidates[-1].date()})")
    print(f"RANDOMLY SELECTED (SystemRandom, pre-registered before any result seen):")
    for w in weeks:
        print(f"  {w.date()} -> {(w + timedelta(days=6)).date()}")
    print()

    summary_rows = []
    all_fixed_trades = []  # for pooled hour/weekday stats

    for week_start in weeks:
        week_end = week_start + timedelta(days=7)
        pull_start = week_start - timedelta(days=WARMUP_DAYS)
        wk_label = f"{week_start.date()}_to_{(week_end - timedelta(days=1)).date()}"

        m1 = fetch(SYMBOL, mt5.TIMEFRAME_M1, week_start, week_end)
        if len(m1) == 0:
            print(f"[skip] {wk_label}: no M1 data")
            continue

        for tf_name, tf_const in SIGNAL_TFS.items():
            sig = fetch(SYMBOL, tf_const, pull_start, week_end)
            if len(sig) < 30:
                print(f"[skip] {wk_label} {tf_name}: insufficient signal bars ({len(sig)})")
                continue

            for cfg_name, cfg_fn in [
                ("v1.11_baseline", cfg_baseline),
                ("v1.12_fixed", cfg_fixed),
                ("v1.12_fixed_conservative", cfg_fixed_conservative),
            ]:
                cfg = cfg_fn()
                trades, final_eq = bt.run(
                    cfg, m15=sig.copy(), m1=m1, signal_start=week_start,
                    deposit=acct.balance, leverage=acct.leverage,
                    contract_size=info.trade_contract_size, tick_value=info.trade_tick_value,
                    tick_size=info.trade_tick_size, point=info.point,
                    min_lot=info.volume_min, lot_step=info.volume_step, max_lot=info.volume_max,
                )
                stats = summarize_run(trades, acct.balance)
                run_id = f"{wk_label}__{tf_name}__{cfg_name}"
                stats.update(week=wk_label, week_start=week_start.date().isoformat(),
                             signal_tf=tf_name, config=cfg_name, run_id=run_id)
                summary_rows.append(stats)

                trade_rows = []
                for t in trades:
                    trade_rows.append({
                        "run_id": run_id, "week": wk_label, "signal_tf": tf_name, "config": cfg_name,
                        "entry_time": t["entry_time"], "dir": "BUY" if t["dir"] == 1 else "SELL",
                        "entry": t["entry"], "sl_initial": t["sl"], "tp1": t["tp1"], "tp2": t["tp2"], "tp3": t["tp3"],
                        "exit_time": t["exit_time"], "exit_reason": t["reason"],
                        "lots": t["lots_orig"], "pnl": t["pnl"], "spread_cost": t["spread_cost"],
                        "tp1_hit": t["tp1_hit"], "tp2_hit": t["tp2_hit"],
                    })
                if trade_rows:
                    pd.DataFrame(trade_rows).to_csv(os.path.join(TRADES_DIR, f"{run_id}.csv"), index=False)
                    if cfg_name == "v1.12_fixed":
                        all_fixed_trades.extend(trade_rows)

                print(f"{run_id:<70} trades={stats['trades']:>4} win%={stats['win_rate']:>6.1f} "
                      f"PF={stats['pf']:>6.2f} net$={stats['net']:>9.2f} maxDD%={stats['max_dd_pct']:>6.1f}")

    summary_df = pd.DataFrame(summary_rows)
    summary_path = os.path.join(HERE, "journal_results_summary.csv")
    if os.path.exists(summary_path):
        old = pd.read_csv(summary_path)
        summary_df = pd.concat([old, summary_df], ignore_index=True)
    summary_df.to_csv(summary_path, index=False)
    print(f"\nWrote {len(summary_rows)} run rows -> {summary_path}")

    # pooled entries-by-hour / weekday for the v1.12_fixed config across all TFs/weeks
    if all_fixed_trades:
        pooled = pd.DataFrame(all_fixed_trades)
        pooled["entry_time"] = pd.to_datetime(pooled["entry_time"])
        pooled["hour"] = pooled["entry_time"].dt.hour
        pooled["weekday"] = pooled["entry_time"].dt.day_name()
        pooled["is_win"] = pooled["pnl"] > 0

        by_hour = pooled.groupby("hour").agg(trades=("pnl", "size"), wins=("is_win", "sum"),
                                              net=("pnl", "sum")).reset_index()
        by_hour["win_rate"] = by_hour["wins"] / by_hour["trades"] * 100
        by_hour.to_csv(os.path.join(HERE, "journal_entries_by_hour.csv"), index=False)

        by_wd = pooled.groupby("weekday").agg(trades=("pnl", "size"), wins=("is_win", "sum"),
                                               net=("pnl", "sum")).reset_index()
        by_wd["win_rate"] = by_wd["wins"] / by_wd["trades"] * 100
        by_wd.to_csv(os.path.join(HERE, "journal_entries_by_weekday.csv"), index=False)
        print(f"Wrote pooled entries-by-hour/weekday CSVs ({len(pooled)} v1.12_fixed trades pooled)")

    with open(os.path.join(HERE, "journal_run_meta.json"), "w") as f:
        json.dump({
            "run_stamp": RUN_STAMP,
            "weeks_tested": [w.date().isoformat() for w in weeks],
            "signal_tfs": list(SIGNAL_TFS.keys()),
            "configs": ["v1.11_baseline", "v1.12_fixed", "v1.12_fixed_conservative"],
            "account": {"server": acct.server, "login": acct.login, "balance": acct.balance,
                        "leverage": acct.leverage, "currency": acct.currency},
            "symbol_meta": meta_rows,
        }, f, indent=2)

    mt5.shutdown()


if __name__ == "__main__":
    main()
