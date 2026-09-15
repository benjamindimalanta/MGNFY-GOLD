"""Large-sample test: pullback entry (RSI extreme+reversal) + MGNFY GOLD exit
machinery, signal AND position management both on M15 (the only timeframe
with 2 years of real XAUUSDm history on this broker — M1 only goes back to
June 2026). Tests H4 and H1 bias pairings, with an IS/OOS split.

Position management uses M15 bar high/low directly (pessimistic SL-first
ordering, same convention as the rest of this project) instead of M1
sub-stepping — coarser than the earlier June-Aug test, but the only way to
reach a real 2-year sample size on this broker's available history.
"""
import sys
sys.path.insert(0, r"D:\EA Robot")

from datetime import datetime

import numpy as np
import pandas as pd

import backtest_mgnfy as bt
import backtest_v4 as v4
import backtest_pullback_realdata as pb

JOURNAL = r"D:\EA Robot\MGNFY_GOLD_LIVE\JOURNAL.md"


def prep(m15, bias_tf):
    m15 = m15.copy()
    hb = m15["close"].resample(bias_tf, label="left", closed="left").agg(["first"]).rename(columns={"first": "close"})
    hb["bF"] = v4.ema(hb["close"], 20)
    hb["bS"] = v4.ema(hb["close"], 50)
    bias_dir = np.sign(hb["bF"] - hb["bS"])
    m15["_bias_override"] = bias_dir.shift(1).reindex(m15.index, method="ffill").fillna(0.0)
    return m15


def run_window(m15_full, bias_tf, start, end, meta, label, cfg=None):
    window = m15_full[(m15_full.index >= start) & (m15_full.index < end)]
    m15p = prep(window, bias_tf)
    if cfg is None:
        cfg = bt.Cfg()
    trades, eq = pb.run_pullback(
        cfg, m15p, None, signal_start=None, deposit=meta["balance"], leverage=meta["leverage"],
        contract_size=meta["contract_size"], tick_value=meta["tick_value"], tick_size=meta["tick_size"],
        point=meta["point"], min_lot=meta["volume_min"], lot_step=meta["volume_step"], max_lot=meta["volume_max"],
    )
    pnls = np.array([t["pnl"] for t in trades]) if trades else np.array([])
    wins = pnls[pnls > 0] if len(pnls) else np.array([])
    losses = pnls[pnls <= 0] if len(pnls) else np.array([])
    pf = (wins.sum() / abs(losses.sum())) if len(losses) and losses.sum() != 0 else float("inf")
    win_rate = (len(wins) / len(pnls) * 100) if len(pnls) else 0.0
    net = pnls.sum() if len(pnls) else 0.0
    print(f"{label:<28} bias={bias_tf:<4} trades={len(trades):>3} win%={win_rate:>5.1f} "
          f"PF={pf if pf!=float('inf') else float('nan'):>5.2f} net=${net:>7.2f} end_eq=${meta['balance']+net:>7.2f}")
    return dict(label=label, bias_tf=bias_tf, trades=len(trades), wins=len(wins), losses=len(losses),
                win_rate=win_rate, pf=pf, net=net, end_eq=meta["balance"] + net)


def main():
    meta = bt.load_meta()
    m15_full = bt.load_df("data/bars_m15_2y.csv")
    m15_full["atr"] = bt.atr_wilder(m15_full, 14)
    m15_full["atr_avg"] = m15_full["atr"].rolling(20).mean()
    m15_full["emaF"] = v4.ema(m15_full["close"], 20)
    m15_full["emaS"] = v4.ema(m15_full["close"], 50)
    m15_full["rsi"] = v4.rsi_wilder(m15_full["close"], 14)

    IS = (m15_full.index.min(), pd.Timestamp("2026-01-01"))
    OOS = (pd.Timestamp("2026-01-01"), m15_full.index.max() + pd.Timedelta(minutes=15))
    FULL = (m15_full.index.min(), m15_full.index.max() + pd.Timedelta(minutes=15))

    rows = []
    for bias_tf in ("4h", "1h"):
        rows.append(run_window(m15_full, bias_tf, *IS, meta, "IS (Sep24-Dec25)"))
        rows.append(run_window(m15_full, bias_tf, *OOS, meta, "OOS (Jan26-Aug26)"))
        rows.append(run_window(m15_full, bias_tf, *FULL, meta, "FULL (Sep24-Aug26)"))

    with open(JOURNAL, "a", encoding="utf-8") as f:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        f.write(f"\n## Test: {ts} — pullback entry (M15 signal, M15 position mgmt) x H4/H1 bias, "
                f"2-YEAR real XAUUSDm M15 history (2024-09 to 2026-08), IS/OOS split, $100 start\n\n")
        f.write("| Window | Bias TF | Trades | Win | Loss | Win% | Net $ | PF | End Eq |\n")
        f.write("|---|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            pf_str = f"{r['pf']:.2f}" if r["pf"] != float("inf") else "inf"
            f.write(f"| {r['label']} | {r['bias_tf']} | {r['trades']} | {r['wins']} | {r['losses']} | "
                    f"{r['win_rate']:.1f} | {r['net']:.2f} | {pf_str} | {r['end_eq']:.2f} |\n")
        f.write("\nNote: position management here steps through M15 bars (not M1) — coarser than the "
                "June-Aug 2026 M1-precision test, since M1 history only exists back to ~June 2026 on this "
                "broker. Treat this as directionally informative, not a precise dollar figure.\n")

    print(f"\nAppended to {JOURNAL}")


if __name__ == "__main__":
    main()
