"""Sweep TP1 distance (the main win-rate lever) and the new BE-buffer option,
on the full August 2026 month (largest sample we have), to see the real
trade-off between win rate and profitability — not just chase a number.

TP1 is expressed as a fraction of the SL distance (which stays fixed at the
Balance preset's 1x ATR). Smaller fraction = closer target = easier to hit
= higher win rate, but each win is worth less relative to a full stop-out.
"""
import backtest_mgnfy as bt

meta = bt.load_meta()

print(f"{'TP1 (xSL)':>10}{'BE buf $':>10} | {'trades':>7}{'win%':>7}{'PF':>7}{'net$':>9}{'maxDD%':>8}")
print("-" * 70)

for tp1_frac_of_sl in (0.15, 0.25, 0.35, 0.5, 0.75, 1.0):
    for be_buf_usd in (0.0, 0.5, 1.0):
        be_buf_pts = be_buf_usd / meta["point"]
        cfg = bt.Cfg(tp1_r=tp1_frac_of_sl, be_buffer_pts=be_buf_pts)
        trades, final_eq = bt.run(
            cfg, deposit=meta["balance"], leverage=meta["leverage"],
            contract_size=meta["contract_size"], tick_value=meta["tick_value"],
            tick_size=meta["tick_size"], point=meta["point"],
            min_lot=meta["volume_min"], lot_step=meta["volume_step"], max_lot=meta["volume_max"],
        )
        if not trades:
            print(f"{tp1_frac_of_sl:>10.2f}{be_buf_usd:>10.2f} | {'0 trades':>7}")
            continue
        import numpy as np
        pnls = np.array([t["pnl"] for t in trades])
        wins = pnls[pnls > 0]; losses = pnls[pnls <= 0]
        win_rate = len(wins) / len(pnls) * 100
        pf = wins.sum() / abs(losses.sum()) if len(losses) and losses.sum() != 0 else float("inf")
        eq = meta["balance"] + np.cumsum(pnls)
        peak = np.maximum.accumulate(np.concatenate([[meta["balance"]], eq]))
        dd = ((peak[1:] - eq) / peak[1:] * 100).max()
        pf_str = f"{pf:.2f}" if pf != float("inf") else "inf"
        print(f"{tp1_frac_of_sl:>10.2f}{be_buf_usd:>10.2f} | {len(trades):>7}{win_rate:>7.1f}{pf_str:>7}{pnls.sum():>9.2f}{dd:>8.1f}")
