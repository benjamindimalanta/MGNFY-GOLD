"""Test the ONE entry logic in this project with a genuine prior validated
edge (RSI-extreme-then-reversal pullback, from backtest_v4.py) against real
August 2026 XAUUSDm broker data + realistic $100-account lot constraints —
rather than continuing to permute MGNFY GOLD's regime-channel entry, which
has now failed all 48 tested combinations at two account sizes.

Signal: exact port of backtest_v4.pullback_signal — EMA20/50 trend on the
trade timeframe, H4 bias agreement required, RSI(14) must have touched an
extreme (<=32 long / >=68 short) then turned back before entry.
Exits: MGNFY GOLD's exit machinery (ATR SL, 1R/2R/3R partial, BE-after-TP1
with the bug fixed, ATR trailing) — reusing backtest_mgnfy.py's engine so
results are directly comparable to everything else in JOURNAL.md.
"""
import sys
sys.path.insert(0, r"D:\EA Robot")

import numpy as np
import pandas as pd

import backtest_mgnfy as bt
import backtest_v4 as v4

JOURNAL = r"D:\EA Robot\MGNFY_GOLD_LIVE\JOURNAL.md"


def run_pullback(cfg: bt.Cfg, m15, m1, signal_start, deposit, leverage, contract_size,
                  tick_value, tick_size, point, min_lot, lot_step, max_lot,
                  fast_ema=20, slow_ema=50, rsi_period=14, rsi_os=32.0, rsi_ob=68.0, trend_tol_atr=0.05,
                  bias_tf="4h"):
    m15 = m15.copy()
    if "atr" not in m15.columns:
        m15["atr"] = bt.atr_wilder(m15, cfg.atr_period)
    if "atr_avg" not in m15.columns:
        m15["atr_avg"] = m15["atr"].rolling(20).mean()
    if "emaF" not in m15.columns:
        m15["emaF"] = v4.ema(m15["close"], fast_ema)
    if "emaS" not in m15.columns:
        m15["emaS"] = v4.ema(m15["close"], slow_ema)
    if "rsi" not in m15.columns:
        m15["rsi"] = v4.rsi_wilder(m15["close"], rsi_period)

    if "_bias_override" in m15.columns:
        m15["bias"] = m15["_bias_override"]
    else:
        hb = m15["close"].resample(bias_tf, label="left", closed="left").agg(["first"]).rename(columns={"first": "close"})
        hb["bF"] = v4.ema(hb["close"], 20)
        hb["bS"] = v4.ema(hb["close"], 50)
        bias_dir = np.sign(hb["bF"] - hb["bS"])
        m15["bias"] = bias_dir.shift(1).reindex(m15.index, method="ffill").fillna(0.0)

    m15 = m15.dropna().copy()
    warmup_bars = int((m15.index < signal_start).sum()) if signal_start is not None else 0

    idx = m15.index
    o = m15["open"].to_numpy(); h = m15["high"].to_numpy(); l = m15["low"].to_numpy(); c = m15["close"].to_numpy()
    sp = m15["spread"].to_numpy() * point
    atr = m15["atr"].to_numpy()
    rows = m15.to_dict("records")
    n = len(m15)

    equity = deposit
    trades = []

    i = max(3, warmup_bars)
    while i < n:
        prev, prev2, prev3 = rows[i - 1], rows[i - 2], rows[i - 3]
        s, is_long = v4.pullback_signal(prev, prev2, prev3, prev["bias"],
                                         type("C", (), dict(trend_tol_atr=trend_tol_atr, rsi_os=rsi_os, rsi_ob=rsi_ob))())
        spread = sp[i]
        ok_spread = cfg.max_spread_points <= 0 or spread <= cfg.max_spread_points * point

        if is_long is not None and ok_spread:
            entry = c[i]
            a = atr[i]
            slDist = cfg.sl_atr_mult * a
            direction = 1 if is_long else -1
            sl = entry - direction * slDist
            lots = cfg.fixed_lots
            req_margin = lots * contract_size * entry / leverage
            if equity < req_margin * cfg.margin_buffer:
                lots = 0.0

            if lots > 0:
                tp1 = entry + direction * cfg.tp1_r * slDist
                tp2 = entry + direction * cfg.tp2_r * slDist
                tp3 = entry + direction * cfg.tp3_r * slDist
                trade = {"entry_time": idx[i], "dir": direction, "entry": entry, "sl": sl,
                         "tp1": tp1, "tp2": tp2, "tp3": tp3, "lots_open": lots, "lots_orig": lots,
                         "tp1_hit": False, "tp2_hit": False, "small_taken": False,
                         "realized": 0.0, "spread_cost": spread * lots * (tick_value / tick_size),
                         "exit_time": None, "reason": None}
                value_per_unit = tick_value / tick_size
                equity -= trade["spread_cost"]

                step_df = m1 if m1 is not None else m15
                path = step_df[step_df.index > idx[i]]
                closed = False
                cur_atr = a
                next_m15_pos = i + 1
                for t, row in path.iterrows():
                    while next_m15_pos < n and idx[next_m15_pos] <= t:
                        cur_atr = atr[next_m15_pos]
                        next_m15_pos += 1
                    lo, hi = row["low"], row["high"]
                    hitSL = (lo <= trade["sl"]) if direction == 1 else (hi >= trade["sl"])
                    if hitSL:
                        move = (trade["sl"] - trade["entry"]) * direction
                        pnl = move * trade["lots_open"] * value_per_unit
                        trade["realized"] += pnl; equity += pnl
                        trade["exit_time"], trade["reason"] = t, "sl"
                        closed = True; break
                    hitTP1 = (row["high"] >= trade["tp1"]) if direction == 1 else (row["low"] <= trade["tp1"])
                    if not trade["tp1_hit"] and hitTP1:
                        close_lots = np.floor((trade["lots_orig"] * cfg.tp1_frac) / lot_step) * lot_step
                        can_close = lot_step <= close_lots < trade["lots_open"]
                        if can_close:
                            move = (trade["tp1"] - trade["entry"]) * direction
                            pnl = move * close_lots * value_per_unit
                            trade["realized"] += pnl; equity += pnl
                            trade["lots_open"] -= close_lots
                        if can_close or cfg.fix_min_lot_tp1_bug:
                            trade["tp1_hit"] = True
                            if cfg.stairstep_lock:
                                trade["sl"] = trade["tp1"]
                            elif cfg.move_be_after_tp1:
                                trade["sl"] = trade["entry"] + direction * cfg.be_buffer_pts * point
                    hitTP2 = (row["high"] >= trade["tp2"]) if direction == 1 else (row["low"] <= trade["tp2"])
                    if trade["tp1_hit"] and not trade["tp2_hit"] and hitTP2:
                        close_lots = np.floor((trade["lots_orig"] * cfg.tp2_frac) / lot_step) * lot_step
                        can_close = lot_step <= close_lots < trade["lots_open"]
                        if can_close:
                            move = (trade["tp2"] - trade["entry"]) * direction
                            pnl = move * close_lots * value_per_unit
                            trade["realized"] += pnl; equity += pnl
                            trade["lots_open"] -= close_lots
                        if can_close or cfg.fix_min_lot_tp1_bug:
                            trade["tp2_hit"] = True
                            if cfg.stairstep_lock:
                                trade["sl"] = trade["tp2"]
                    if cfg.use_atr_trailing:
                        trail = cfg.trail_atr_mult * cur_atr
                        newSL = (row["close"] - trail) if direction == 1 else (row["close"] + trail)
                        if direction == 1 and newSL > trade["sl"]:
                            trade["sl"] = newSL
                        elif direction == -1 and newSL < trade["sl"]:
                            trade["sl"] = newSL
                    hitTP3 = (row["high"] >= trade["tp3"]) if direction == 1 else (row["low"] <= trade["tp3"])
                    if trade["tp1_hit"] and trade["tp2_hit"] and hitTP3:
                        move = (trade["tp3"] - trade["entry"]) * direction
                        pnl = move * trade["lots_open"] * value_per_unit
                        trade["realized"] += pnl; equity += pnl
                        trade["lots_open"] = 0.0
                        trade["exit_time"], trade["reason"] = t, "tp3"
                        closed = True; break
                if not closed:
                    last_px = step_df.iloc[-1]["close"]
                    move = (last_px - trade["entry"]) * direction
                    pnl = move * trade["lots_open"] * value_per_unit
                    trade["realized"] += pnl; equity += pnl
                    trade["exit_time"], trade["reason"] = step_df.index[-1], "eom_markout"
                trade["pnl"] = trade["realized"] - trade["spread_cost"]
                trades.append(trade)
                exit_pos = idx.searchsorted(trade["exit_time"], side="right")
                i = max(i + 1, exit_pos)
                continue
        i += 1

    return trades, equity


if __name__ == "__main__":
    meta = bt.load_meta()
    m1 = bt.load("m1_aug2026")
    m5 = m1.resample("5min", label="left", closed="left").agg(
        open=("open", "first"), high=("high", "max"), low=("low", "min"),
        close=("close", "last"), spread=("spread", "mean")).dropna()
    cfg = bt.Cfg()  # exit machinery = Balance preset defaults
    trades, final_eq = run_pullback(
        cfg, m5, m1, signal_start=None, deposit=meta["balance"], leverage=meta["leverage"],
        contract_size=meta["contract_size"], tick_value=meta["tick_value"], tick_size=meta["tick_size"],
        point=meta["point"], min_lot=meta["volume_min"], lot_step=meta["volume_step"], max_lot=meta["volume_max"],
    )
    bt.summarize(trades, meta["balance"])

    with open(JOURNAL, "a", encoding="utf-8") as f:
        from datetime import datetime
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        pnls = np.array([t["pnl"] for t in trades]) if trades else np.array([])
        wins = pnls[pnls > 0] if len(pnls) else np.array([])
        losses = pnls[pnls <= 0] if len(pnls) else np.array([])
        pf = (wins.sum() / abs(losses.sum())) if len(losses) and losses.sum() != 0 else float("inf")
        f.write(f"\n## Test: {ts} — VALIDATED pullback entry (RSI extreme+reversal, EMA trend, H4 bias) "
                f"+ MGNFY GOLD exit machinery, August 2026 real XAUUSDm data, $100 start\n\n")
        f.write(f"Trades {len(trades)}, Win {len(wins)}, Loss {len(losses)}, "
                f"Win% {(len(wins)/len(pnls)*100 if len(pnls) else 0):.1f}, "
                f"Net ${pnls.sum() if len(pnls) else 0:.2f}, PF {pf if pf!=float('inf') else 'inf'}, "
                f"End Eq ${meta['balance']+(pnls.sum() if len(pnls) else 0):.2f}\n")
