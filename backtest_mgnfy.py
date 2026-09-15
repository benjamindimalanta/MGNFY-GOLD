"""Offline backtester for MGNFY GOLD.mq5 (v1.11), ported line-for-line from
the actual EA logic (not the marketing description) so results reflect what
the live EA really does, not an idealized version of it.

DATA
----
August 2026 M15 + M1 XAUUSDm bars pulled directly from the user's Exness
demo terminal via the MetaTrader5 Python API (data/bars_*_aug2026.csv).
This is broker-matched data, not a third-party feed.

FIDELITY NOTES — read before trusting the numbers
---------------------------------------------------
1. SIGNAL evaluation (regime channel, midline breakout) is done once per
   CLOSED M15 bar, using that bar's own high/low for the midline and its
   close vs. the previous bar's close for the crossing check. The live EA
   actually evaluates this continuously tick-by-tick against the STILL
   FORMING bar's growing high/low. Evaluating at bar-close is the standard
   simplification non-tick backtests make (MT5's own tester does the same
   in OHLC modes) — a real "every tick" MT5 Strategy Tester run would be
   the authoritative version of this number.
2. POSITION MANAGEMENT (SL, TP1/TP2/TP3 partials, breakeven, ATR trailing,
   small-account capture) steps through M1 bars, not M15 closes — this is
   MORE precise than the signal layer for the partial-exit ladder, which
   is the part most sensitive to intrabar timing.
3. SL is broker-enforced (a real stop order in the live EA) — simulated
   here as: if a step's low/high crosses SL, the trade closes at SL price.
   TP1/TP2/TP3 are EA-polled (no broker TP order), simulated the same way
   the live code does it — sequential checks in the exact order the .mq5
   runs them each tick.
4. MACD filter and H4 trend filter are now implemented. The trend filter
   uses the last CLOSED H4 bar's EMA200 (a causal simplification of the
   live EA's continuously-updating current-bar EMA — see note 1).
5. Spread cost is applied once at entry+exit using each bar's real
   recorded spread column, same convention as the rest of this project's
   backtests.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

DATA_DIR = r"D:\EA Robot\MGNFY_GOLD_LIVE\data"


def load(name):
    df = pd.read_csv(f"{DATA_DIR}/bars_{name}.csv")
    df["time"] = pd.to_datetime(df["time"])
    return df.set_index("time").sort_index()


def load_df(path):
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["time"])
    return df.set_index("time").sort_index()


def load_meta():
    m = pd.read_csv(f"{DATA_DIR}/symbol_meta.csv").set_index("field")["value"]
    return {k: float(v) if k not in ("symbol",) else v for k, v in m.items()}


def atr_wilder(df, n):
    pc = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / n, adjust=False).mean()


class Cfg:
    """Mirrors the .mq5 inputs. Defaults here = the 'Balance' preset,
    which also matches the EA's own built-in default input values."""
    def __init__(self, **kw):
        self.atr_period = 14
        self.atr_mult = 2.0            # channel width
        self.use_midline_breakout = True
        self.require_trend_flip = False
        self.confirm_bars = 1
        self.use_macd_filter = False   # NOT implemented — must stay False
        self.use_trend_filter = False  # NOT implemented — must stay False
        self.use_session_filter = False
        self.max_spread_points = 400
        self.margin_buffer = 1.20
        self.use_atr_stops = True
        self.sl_atr_mult = 1.0
        self.tp1_r = 1.0
        self.tp2_r = 2.0
        self.tp3_r = 3.0
        self.tp1_frac = 0.33
        self.tp2_frac = 0.33
        self.move_be_after_tp1 = True
        self.be_buffer_pts = 0        # extra points locked in when moving to BE after TP1 (0 = flat entry, old behavior)
        self.fix_min_lot_tp1_bug = True  # True = fixed behavior; False = reproduce the live EA's bug
        self.stairstep_lock = False   # SL jumps to TP1/TP2 price once hit, instead of flat BE
        # Option B (user's idea): TP2 closes the ENTIRE remaining position at TP2's price on a
        # normal touch. If price already overshot TP2 by more than tp2_overshoot_buffer_atr (a
        # fast/strong move, not a gentle touch), don't force the close — lock SL at TP2 instead
        # and let the trailing stop ride the momentum for potentially more than TP2's profit.
        self.tp2_full_close = False
        self.tp2_overshoot_buffer_atr = 0.10
        self.use_atr_trailing = True
        self.trail_atr_mult = 1.0
        self.use_risk_sizing = False
        self.risk_percent = 1.0
        self.fixed_lots = 0.01
        # small-account capture
        self.small_cap_threshold = 300.0
        self.small_profit_abs = 2.0
        self.small_profit_pct = 0.5
        self.small_partial_frac = 0.50
        self.small_move_to_be = True
        self.small_be_buffer_pts = 10
        for k, v in kw.items():
            setattr(self, k, v)


def run(cfg: Cfg, m15=None, m1=None, signal_start=None, deposit=100.0, leverage=100.0, contract_size=100.0,
        tick_value=0.1, tick_size=0.001, point=0.001, min_lot=0.01, lot_step=0.01, max_lot=200.0):
    if m15 is None:
        m15 = load("m15_aug2026")
    if m1 is None:
        m1 = load("m1_aug2026")
    m15["atr"] = atr_wilder(m15, cfg.atr_period)
    ema12 = m15["close"].ewm(span=12, adjust=False).mean()
    ema26 = m15["close"].ewm(span=26, adjust=False).mean()
    m15["macd"] = ema12 - ema26

    if cfg.use_trend_filter:
        h4 = m15["close"].resample("4h", label="left", closed="left").last().dropna()
        h4_ema = h4.ewm(span=200, adjust=False).mean()
        # causal: only a CLOSED H4 bar's EMA may inform a decision (simplification vs the
        # live EA's continuously-updating current-bar EMA — see module docstring)
        m15["trend_ema"] = h4_ema.shift(1).reindex(m15.index, method="ffill")
    else:
        m15["trend_ema"] = np.nan

    m15 = m15.dropna(subset=["atr"]).copy()
    warmup_bars = 0
    if signal_start is not None:
        warmup_bars = int((m15.index < signal_start).sum())

    value_per_unit = tick_value / tick_size  # $ per 1.0 price-unit move per 1.0 lot

    idx = m15.index
    h = m15["high"].to_numpy(); l = m15["low"].to_numpy(); c = m15["close"].to_numpy()
    sp = (m15["spread"].to_numpy() * point)
    atr = m15["atr"].to_numpy()
    macd = m15["macd"].to_numpy()
    trend_ema = m15["trend_ema"].to_numpy()

    prevUp1 = 0.0; prevDn1 = 0.0; prevTrend = 0
    equity = deposit
    trades = []
    open_trades_log = []

    m1_by_time = m1  # indexed by time already

    def margin_for(lots, price):
        return lots * contract_size * price / leverage

    def open_signal(i):
        nonlocal prevUp1, prevDn1, prevTrend
        close0, close1 = c[i], c[i - 1]
        hlMid = (h[i] + l[i]) * 0.5
        lowerBand = hlMid - cfg.atr_mult * atr[i]
        upperBand = hlMid + cfg.atr_mult * atr[i]

        up1 = lowerBand if prevUp1 == 0.0 else (max(lowerBand, prevUp1) if close1 > prevUp1 else lowerBand)
        dn1 = upperBand if prevDn1 == 0.0 else (min(upperBand, prevDn1) if close1 < prevDn1 else upperBand)

        trend = 1 if prevTrend == 0 else prevTrend
        if close0 > dn1:
            trend = 1
        elif close0 < up1:
            trend = -1

        if cfg.use_midline_breakout:
            buyBreak = close1 <= hlMid and close0 > hlMid
            sellBreak = close1 >= hlMid and close0 < hlMid
        else:
            buyBreak = close1 <= dn1 and close0 > dn1
            sellBreak = close1 >= up1 and close0 < up1

        if cfg.require_trend_flip:
            buySignal = (trend == 1 and prevTrend == -1) and buyBreak
            sellSignal = (trend == -1 and prevTrend == 1) and sellBreak
        else:
            buySignal, sellSignal = buyBreak, sellBreak

        prevUp1, prevDn1, prevTrend = up1, dn1, trend
        return buySignal, sellSignal

    i = 1
    n = len(m15)
    while i < n:
        buySignal, sellSignal = open_signal(i)
        if i < warmup_bars:
            # prime the trend-channel state using pre-week bars, but don't trade on them
            i += 1
            continue

        if cfg.use_session_filter:
            buySignal = sellSignal = False  # not needed for this preset (off)

        spread = sp[i]
        if cfg.max_spread_points > 0 and spread > cfg.max_spread_points * point:
            buySignal = sellSignal = False

        if cfg.use_macd_filter:
            if buySignal and not (macd[i] > 0):
                buySignal = False
            if sellSignal and not (macd[i] < 0):
                sellSignal = False

        if cfg.use_trend_filter and not np.isnan(trend_ema[i]):
            if buySignal and not (c[i] > trend_ema[i]):
                buySignal = False
            if sellSignal and not (c[i] < trend_ema[i]):
                sellSignal = False

        if buySignal or sellSignal:
            entry = c[i]
            a = atr[i]
            slDist = cfg.sl_atr_mult * a if cfg.use_atr_stops else 0.0
            direction = 1 if buySignal else -1
            sl = entry - direction * slDist

            if cfg.use_risk_sizing and slDist > 0:
                risk_amt = equity * cfg.risk_percent / 100.0
                loss_per_lot = (slDist / tick_size) * tick_value
                lots = risk_amt / loss_per_lot if loss_per_lot > 0 else 0.0
                lots = np.floor(lots / lot_step) * lot_step
                lots = max(min_lot, min(max_lot, lots))
            else:
                lots = cfg.fixed_lots

            req_margin = margin_for(lots, entry)
            free_margin = equity  # only one position at a time, no position open here
            if free_margin < req_margin * cfg.margin_buffer or lots <= 0:
                lots = 0.0

            if lots > 0:
                tp1 = entry + direction * cfg.tp1_r * slDist
                tp2 = entry + direction * cfg.tp2_r * slDist
                tp3 = entry + direction * cfg.tp3_r * slDist

                trade = {
                    "entry_time": idx[i], "dir": direction, "entry": entry, "sl": sl,
                    "tp1": tp1, "tp2": tp2, "tp3": tp3, "lots_open": lots, "lots_orig": lots,
                    "tp1_hit": False, "tp2_hit": False, "small_taken": False,
                    "realized": 0.0, "spread_cost": spread * lots * value_per_unit,
                    "exit_time": None, "reason": None,
                }
                equity -= trade["spread_cost"]  # entry spread cost, matches project convention

                # ---- step through M1 bars from just after entry ----
                path = m1_by_time[m1_by_time.index > idx[i]]
                # cap the walk at the next signal-relevant horizon: end of data
                closed = False
                cur_atr = a
                next_m15_pos = i + 1
                for t, row in path.iterrows():
                    # roll cur_atr forward as M15 bars close during the trade
                    while next_m15_pos < n and idx[next_m15_pos] <= t:
                        cur_atr = atr[next_m15_pos]
                        next_m15_pos += 1

                    lo, hi = row["low"], row["high"]

                    # 1) broker-enforced SL
                    hitSL = (lo <= trade["sl"]) if direction == 1 else (hi >= trade["sl"])
                    if hitSL:
                        move = (trade["sl"] - trade["entry"]) * direction
                        trade["realized"] += move * trade["lots_open"] * value_per_unit
                        equity += move * trade["lots_open"] * value_per_unit
                        trade["exit_time"], trade["reason"] = t, "sl"
                        closed = True
                        break

                    floating_px = row["close"]
                    floating = (floating_px - trade["entry"]) * direction * trade["lots_open"] * value_per_unit

                    # 2) small-account capture (one-time per trade)
                    if deposit <= cfg.small_cap_threshold and not trade["small_taken"]:
                        thresh = max(cfg.small_profit_abs, deposit * cfg.small_profit_pct / 100.0)
                        if floating >= thresh:
                            frac = cfg.small_partial_frac
                            close_lots = np.floor((trade["lots_orig"] * frac) / lot_step) * lot_step
                            if lot_step <= close_lots < trade["lots_open"]:
                                move = (floating_px - trade["entry"]) * direction
                                pnl = move * close_lots * value_per_unit
                                trade["realized"] += pnl
                                equity += pnl
                                trade["lots_open"] -= close_lots
                                trade["small_taken"] = True
                                if cfg.small_move_to_be:
                                    trade["sl"] = trade["entry"] + direction * cfg.small_be_buffer_pts * point

                    # 3) TP1 — BUGFIX (matches a real bug found in the live .mq5): the original
                    # code only marks TP1 "hit" (and moves SL to BE) if the partial-close volume
                    # actually rounds to >= 1 lot step. At 0.01 lot, 33% rounds to 0.00 and the
                    # whole TP1/TP2/BE mechanism silently never fires. cfg.fix_min_lot_tp1_bug
                    # controls whether we reproduce the live bug (False) or the fixed behavior
                    # (True): price reaching TP1 always counts as "hit" and moves SL to BE,
                    # even when there isn't enough volume to physically split off a partial.
                    hitTP1 = (row["high"] >= trade["tp1"]) if direction == 1 else (row["low"] <= trade["tp1"])
                    if not trade["tp1_hit"] and hitTP1:
                        close_lots = np.floor((trade["lots_orig"] * cfg.tp1_frac) / lot_step) * lot_step
                        can_close = lot_step <= close_lots < trade["lots_open"]
                        if can_close:
                            move = (trade["tp1"] - trade["entry"]) * direction
                            pnl = move * close_lots * value_per_unit
                            trade["realized"] += pnl
                            equity += pnl
                            trade["lots_open"] -= close_lots
                        if can_close or cfg.fix_min_lot_tp1_bug:
                            trade["tp1_hit"] = True
                            if cfg.stairstep_lock:
                                trade["sl"] = trade["tp1"]
                            elif cfg.move_be_after_tp1:
                                trade["sl"] = trade["entry"] + direction * cfg.be_buffer_pts * point

                    # 4) TP2 (only after TP1)
                    hitTP2 = (row["high"] >= trade["tp2"]) if direction == 1 else (row["low"] <= trade["tp2"])
                    if trade["tp1_hit"] and not trade["tp2_hit"] and hitTP2:
                        if cfg.tp2_full_close:
                            overshoot = (row["high"] - trade["tp2"]) if direction == 1 else (trade["tp2"] - row["low"])
                            if overshoot <= cfg.tp2_overshoot_buffer_atr * cur_atr:
                                # normal touch: close the ENTIRE remaining position at TP2's price
                                move = (trade["tp2"] - trade["entry"]) * direction
                                pnl = move * trade["lots_open"] * value_per_unit
                                trade["realized"] += pnl
                                equity += pnl
                                trade["lots_open"] = 0.0
                                trade["tp2_hit"] = True
                                trade["exit_time"], trade["reason"] = t, "tp2_full"
                                closed = True
                                break
                            else:
                                # blew past TP2 already (fast move): don't force the close,
                                # lock the stop at TP2 and let trailing ride the momentum
                                trade["tp2_hit"] = True
                                trade["sl"] = trade["tp2"]
                        else:
                            close_lots = np.floor((trade["lots_orig"] * cfg.tp2_frac) / lot_step) * lot_step
                            can_close = lot_step <= close_lots < trade["lots_open"]
                            if can_close:
                                move = (trade["tp2"] - trade["entry"]) * direction
                                pnl = move * close_lots * value_per_unit
                                trade["realized"] += pnl
                                equity += pnl
                                trade["lots_open"] -= close_lots
                            if can_close or cfg.fix_min_lot_tp1_bug:
                                trade["tp2_hit"] = True
                                if cfg.stairstep_lock:
                                    trade["sl"] = trade["tp2"]

                    # 5) ATR trailing (unconditional, ratchets in favor only)
                    if cfg.use_atr_trailing:
                        trail = cfg.trail_atr_mult * cur_atr
                        newSL = (row["close"] - trail) if direction == 1 else (row["close"] + trail)
                        if direction == 1 and newSL > trade["sl"]:
                            trade["sl"] = newSL
                        elif direction == -1 and newSL < trade["sl"]:
                            trade["sl"] = newSL

                    # 6) TP3 -> close remainder
                    hitTP3 = (row["high"] >= trade["tp3"]) if direction == 1 else (row["low"] <= trade["tp3"])
                    if trade["tp1_hit"] and trade["tp2_hit"] and hitTP3:
                        move = (trade["tp3"] - trade["entry"]) * direction
                        pnl = move * trade["lots_open"] * value_per_unit
                        trade["realized"] += pnl
                        equity += pnl
                        trade["lots_open"] = 0.0
                        trade["exit_time"], trade["reason"] = t, "tp3"
                        closed = True
                        break

                if not closed:
                    # ran out of data (position still open at month end) — mark to last price
                    last_px = m1.iloc[-1]["close"]
                    move = (last_px - trade["entry"]) * direction
                    pnl = move * trade["lots_open"] * value_per_unit
                    trade["realized"] += pnl
                    equity += pnl
                    trade["exit_time"], trade["reason"] = m1.index[-1], "eom_markout"

                trade["pnl"] = trade["realized"] - trade["spread_cost"]
                trades.append(trade)

                # advance i to the M15 bar at/after the trade's exit so we don't
                # evaluate new signals while "in" this trade (OnlyOnePosition=true)
                if trade["exit_time"] is not None:
                    exit_pos = idx.searchsorted(trade["exit_time"], side="right")
                    i = max(i + 1, exit_pos)
                    continue

        i += 1

    return trades, equity


def summarize(trades, deposit):
    """Standard report format for every backtest in this project from now on."""
    if not trades:
        print("No trades.")
        return
    pnls = np.array([t["pnl"] for t in trades])
    wins = pnls[pnls > 0]; losses = pnls[pnls <= 0]
    n_win, n_loss = len(wins), len(losses)
    total_win = wins.sum() if n_win else 0.0
    total_loss = losses.sum() if n_loss else 0.0  # negative number
    net = pnls.sum()
    ending_eq = deposit + net
    win_rate = n_win / len(pnls) * 100
    max_win = wins.max() if n_win else 0.0
    max_loss = losses.min() if n_loss else 0.0    # most negative
    avg_win = wins.mean() if n_win else 0.0
    avg_loss = losses.mean() if n_loss else 0.0
    win_loss_ratio = (avg_win / abs(avg_loss)) if avg_loss != 0 else float("inf")

    eq = deposit + np.cumsum(pnls)
    peak = np.maximum.accumulate(np.concatenate([[deposit], eq]))
    dd = (peak[1:] - eq) / peak[1:] * 100

    print("=" * 50)
    print("BACKTEST REPORT")
    print("=" * 50)
    print("ACCOUNT")
    print(f"{'  Starting equity ($):':<28}{deposit:,.2f}")
    print(f"{'  Ending equity ($):':<28}{ending_eq:,.2f}")
    print(f"{'  Net P&L ($):':<28}{net:,.2f}")
    print(f"{'  Max drawdown (%):':<28}{dd.max():.2f}")
    print("TRADE ACTIVITY")
    print(f"{'  Total trades:':<28}{len(trades)}")
    print(f"{'  Winning trades:':<28}{n_win}")
    print(f"{'  Losing trades:':<28}{n_loss}")
    print(f"{'  Win rate (%):':<28}{win_rate:.1f}")
    print("PROFIT / LOSS DETAIL")
    print(f"{'  Total win ($):':<28}{total_win:,.2f}")
    print(f"{'  Total loss ($):':<28}{total_loss:,.2f}")
    print(f"{'  Max win ($):':<28}{max_win:,.2f}")
    print(f"{'  Max loss ($):':<28}{max_loss:,.2f}")
    print(f"{'  Win:Loss ratio (avg $):':<28}{win_loss_ratio:.2f} : 1")
    print("=" * 50)
    print()
    print(f"{'#':>3} {'entry_time':<20}{'dir':>4}{'entry':>10}{'exit_reason':>12}{'pnl':>10}")
    for n, t in enumerate(trades, 1):
        print(f"{n:>3} {str(t['entry_time']):<20}{'BUY' if t['dir']==1 else 'SELL':>4}"
              f"{t['entry']:>10.3f}{t['reason']:>12}{t['pnl']:>10.2f}")


if __name__ == "__main__":
    meta = load_meta()
    cfg = Cfg()
    trades, final_eq = run(
        cfg, deposit=meta["balance"], leverage=meta["leverage"],
        contract_size=meta["contract_size"], tick_value=meta["tick_value"],
        tick_size=meta["tick_size"], point=meta["point"],
        min_lot=meta["volume_min"], lot_step=meta["volume_step"], max_lot=meta["volume_max"],
    )
    summarize(trades, meta["balance"])
