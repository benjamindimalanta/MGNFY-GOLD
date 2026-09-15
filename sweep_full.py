"""Full grid sweep of MGNFY GOLD's entry/filter/sizing variations, on real
August 2026 XAUUSDm broker data. Writes every combination + result to
JOURNAL.md (appended, not overwritten) so nothing gets lost between sessions.
"""
from datetime import datetime
import itertools

import numpy as np

import backtest_mgnfy as bt

JOURNAL = r"D:\EA Robot\MGNFY_GOLD_LIVE\JOURNAL.md"


def metrics(trades, deposit):
    if not trades:
        return dict(trades=0, wins=0, losses=0, win_rate=0.0, net=0.0, pf=0.0,
                    max_dd=0.0, ending_eq=deposit, win_loss_ratio=0.0)
    pnls = np.array([t["pnl"] for t in trades])
    wins = pnls[pnls > 0]; losses = pnls[pnls <= 0]
    net = pnls.sum()
    eq = deposit + np.cumsum(pnls)
    peak = np.maximum.accumulate(np.concatenate([[deposit], eq]))
    dd = ((peak[1:] - eq) / peak[1:] * 100).max()
    avg_win = wins.mean() if len(wins) else 0.0
    avg_loss = losses.mean() if len(losses) else 0.0
    return dict(
        trades=len(trades), wins=len(wins), losses=len(losses),
        win_rate=len(wins) / len(pnls) * 100,
        net=net, pf=(wins.sum() / abs(losses.sum())) if len(losses) and losses.sum() != 0 else float("inf"),
        max_dd=dd, ending_eq=deposit + net,
        win_loss_ratio=(avg_win / abs(avg_loss)) if avg_loss != 0 else float("inf"),
    )


def main(deposit_override=None):
    meta = bt.load_meta()
    deposit = deposit_override if deposit_override is not None else meta["balance"]

    grid = list(itertools.product(
        [True, False],   # use_midline_breakout
        [True, False],   # require_trend_flip
        [True, False],   # use_macd_filter
        [True, False],   # use_trend_filter
        ["fixed", "risk0.5", "risk1.0"],  # sizing
    ))

    rows = []
    for midline, flip, macdf, trendf, sizing in grid:
        kw = dict(
            use_midline_breakout=midline, require_trend_flip=flip,
            use_macd_filter=macdf, use_trend_filter=trendf,
        )
        if sizing == "fixed":
            kw["use_risk_sizing"] = False
        else:
            kw["use_risk_sizing"] = True
            kw["risk_percent"] = 0.5 if sizing == "risk0.5" else 1.0
        cfg = bt.Cfg(**kw)
        trades, final_eq = bt.run(
            cfg, deposit=deposit, leverage=meta["leverage"], contract_size=meta["contract_size"],
            tick_value=meta["tick_value"], tick_size=meta["tick_size"], point=meta["point"],
            min_lot=meta["volume_min"], lot_step=meta["volume_step"], max_lot=meta["volume_max"],
        )
        m = metrics(trades, deposit)
        rows.append(dict(midline=midline, flip=flip, macdf=macdf, trendf=trendf, sizing=sizing, **m))

    rows.sort(key=lambda r: r["net"], reverse=True)

    # ---- console summary ----
    hdr = f"{'mid':>5}{'flip':>6}{'macd':>6}{'trend':>6}{'sizing':>9} | {'tr':>4}{'win%':>7}{'PF':>7}{'net$':>9}{'maxDD%':>8}"
    print(hdr); print("-" * len(hdr))
    for r in rows[:15]:
        pf_str = f"{r['pf']:.2f}" if r["pf"] != float("inf") else "inf"
        print(f"{str(r['midline']):>5}{str(r['flip']):>6}{str(r['macdf']):>6}{str(r['trendf']):>6}{r['sizing']:>9} | "
              f"{r['trades']:>4}{r['win_rate']:>7.1f}{pf_str:>7}{r['net']:>9.2f}{r['max_dd']:>8.1f}")

    # ---- journal ----
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(JOURNAL, "a", encoding="utf-8") as f:
        f.write(f"\n## Sweep: {ts} — full entry/filter/sizing grid, August 2026 (31d, real XAUUSDm broker data)\n\n")
        f.write(f"Starting equity: ${deposit:.2f}. TP1-partial-close bug fix applied "
                f"(`fix_min_lot_tp1_bug=True`). {len(rows)} combinations tested.\n\n")
        f.write("| Midline brk | Trend-flip req | MACD filter | H4 trend filter | Sizing | Trades | Win | Loss | Win% | Net $ | PF | MaxDD% | End Eq |\n")
        f.write("|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            pf_str = f"{r['pf']:.2f}" if r["pf"] != float("inf") else "inf"
            f.write(f"| {r['midline']} | {r['flip']} | {r['macdf']} | {r['trendf']} | {r['sizing']} | "
                    f"{r['trades']} | {r['wins']} | {r['losses']} | {r['win_rate']:.1f} | {r['net']:.2f} | "
                    f"{pf_str} | {r['max_dd']:.1f} | {r['ending_eq']:.2f} |\n")
        f.write("\n")

    print(f"\nFull {len(rows)}-row table appended to {JOURNAL}")


if __name__ == "__main__":
    import sys
    dep = float(sys.argv[1]) if len(sys.argv) > 1 else None
    main(dep)
