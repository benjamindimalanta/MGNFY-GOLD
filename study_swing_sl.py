"""Study swing mode's stop buffer and order distance from v1.14's real tester runs.

Inputs: every "Swing: placed" / "Swing bias" line the EA logged in the 4 comparison runs (H1 chart,
swing mode), the 20 real swing trades (mode_compare_trades.csv), and real XAUUSDm M1 bars from MT5.

1. Real trades: how far price went against each trade (in ATR(M30)) before TP1, and whether it later
   reached TP1 -- i.e. would a wider stop have kept the loser alive?
2. Stop-buffer replay: every placed order is replayed on M1 bars (limit fill, then stop vs TP1, whichever
   price reaches first; same-bar ties count as losses) for each buffer, in dollars at 0.01 lot.
   Calibration: the as-run replay (0.3 buffer, order cancelled at the next hourly check) should find
   roughly the 20 fills the tester actually had.
3. Distance vs fill rate: distance of each order from price when placed, in ATR(M30).
"""
import re
from datetime import datetime, timedelta

import MetaTrader5 as mt5
import numpy as np
import pandas as pd

AGENT_LOG = r"C:\Users\Benja\AppData\Roaming\MetaQuotes\Tester\53785E099C927DB68A545C249CDBCE06\Agent-127.0.0.1-3000\logs\20260915.log"
SCRATCH = r"C:\Users\Benja\AppData\Local\Temp\claude\C--Users-Benja-OneDrive-Pictures-MSB-OB\c739d792-d8b9-4d83-b2a2-028661b569de\scratchpad"
TRADES = SCRATCH + r"\mode_compare_trades.csv"
SYMBOL = "XAUUSDm"
POINT = 0.001
BUFFER_USED = 0.3
BUFFERS = [0.3, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0]
MIN_RR = 1.0

PLACED_RE = re.compile(r"(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Swing: placed (BUY|SELL) LIMIT [\d.]+ lots @ "
                       r"([\d.]+) sl=([\d.]+) tp1=([\d.]+) \(risk ([\d.]+), reward ([\d.]+)\)")
BIAS_RE = re.compile(r"(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Swing bias: .*-> (-?\d)")


def ts(s):
    return datetime.strptime(s, "%Y.%m.%d %H:%M:%S")


def parse_runs():
    text = open(AGENT_LOG, encoding="utf-16", errors="replace").read()
    runs, cur = [], None
    for raw in text.splitlines():
        f = raw.split("\t")
        if len(f) < 5:
            continue
        msg = f[4]
        if "testing of" in msg and "started with inputs" in msg:
            m = re.search(r",(\w+): testing of .* from (\d{4}\.\d{2}\.\d{2})", msg)
            cur = {"tf": m.group(1) if m else "?", "from": m.group(2) if m else "?", "mode": None,
                   "rt": f[2], "events": []}
            runs.append(cur)
            continue
        if cur is None:
            continue
        s = msg.strip()
        if s.startswith("InpEntryMode="):
            cur["mode"] = s.split("=", 1)[1]
            continue
        m = PLACED_RE.search(msg)
        if m:
            cur["events"].append(("place", ts(m.group(1)), 1 if m.group(2) == "BUY" else -1,
                                  float(m.group(3)), float(m.group(5)), float(m.group(6))))
            continue
        m = BIAS_RE.search(msg)
        if m:
            cur["events"].append(("bias", ts(m.group(1)), int(m.group(2))))
    return [r for r in runs if r["mode"] == "1" and r["tf"] == "H1" and "15:12" <= r["rt"][:5] <= "15:16"]


def build_orders(run):
    week_start = datetime.strptime(run["from"], "%Y.%m.%d")
    week_end = week_start + timedelta(days=5, hours=23, minutes=59)
    hourly, kept, cur = [], [], None
    ev = run["events"]
    for i, e in enumerate(ev):
        if e[0] == "place":
            _, t, d, entry, tp1, risk = e
            atr = risk / BUFFER_USED
            nxt = next((x[1] for x in ev[i + 1:] if x[0] == "bias"), week_end)
            hourly.append(dict(week=run["from"], start=t, end=nxt, week_end=week_end, dir=d, entry=entry, tp1=tp1, atr=atr))
            if cur and cur["dir"] == d and abs(cur["entry"] - entry) < 1e-6:
                continue
            if cur:
                cur["end"] = t
                kept.append(cur)
            cur = dict(week=run["from"], start=t, end=week_end, week_end=week_end, dir=d, entry=entry, tp1=tp1, atr=atr)
        elif e[0] == "bias" and cur and e[2] == -cur["dir"]:
            cur["end"] = e[1]
            kept.append(cur)
            cur = None
    if cur:
        kept.append(cur)
    return hourly, kept


def fill_time(order, bars):
    w = bars.loc[(bars.index >= order["start"]) & (bars.index < order["end"])]
    if w.empty:
        return None
    spread = w["spread"].to_numpy() * POINT
    mask = (w["low"].to_numpy() + spread <= order["entry"]) if order["dir"] > 0 else (w["high"].to_numpy() >= order["entry"])
    idx = np.flatnonzero(mask)
    return None if len(idx) == 0 else w.index[idx[0]]


def race(order, bars, ft, risk):
    d, entry, tp1 = order["dir"], order["entry"], order["tp1"]
    a = bars.loc[(bars.index >= ft) & (bars.index <= order["week_end"])]
    sp = a["spread"].to_numpy() * POINT
    lo, hi = a["low"].to_numpy(), a["high"].to_numpy()
    sl = entry - d * risk
    if d > 0:
        sl_hit, tp_hit = lo <= sl, hi >= tp1
    else:
        sl_hit, tp_hit = hi + sp >= sl, lo + sp <= tp1
    tp_hit[0] = False  # the fill bar: only let the stop count (conservative)
    s = np.flatnonzero(sl_hit)
    t = np.flatnonzero(tp_hit)
    if len(s) and (not len(t) or s[0] <= t[0]):
        return "loss", -risk, (a.index[s[0]] - ft).total_seconds() / 60
    if len(t):
        return "win", abs(tp1 - entry), (a.index[t[0]] - ft).total_seconds() / 60
    return "open", (a["close"].iloc[-1] - entry) * d, np.nan


def main():
    runs = parse_runs()
    print(f"swing comparison runs found: {len(runs)} ({', '.join(r['from'] for r in runs)})")
    hourly, kept = [], []
    for r in runs:
        h, k = build_orders(r)
        hourly += h
        kept += k
    print(f"orders as run (one per hourly placement): {len(hourly)} | distinct orders if kept until flip/level change: {len(kept)}")

    if not mt5.initialize():
        raise SystemExit(f"MT5 initialize failed: {mt5.last_error()}")
    first = min(o["start"] for o in hourly) - timedelta(hours=2)
    last = max(o["week_end"] for o in hourly) + timedelta(hours=1)
    rates = mt5.copy_rates_range(SYMBOL, mt5.TIMEFRAME_M1, first, last)
    mt5.shutdown()
    bars = pd.DataFrame(rates)
    bars["time"] = pd.to_datetime(bars["time"], unit="s")
    bars = bars.set_index("time")[["open", "high", "low", "close", "spread"]]
    print(f"M1 bars loaded: {len(bars)} ({bars.index[0]} -> {bars.index[-1]})\n")

    # ---- calibration: as-run replay at the buffer actually used
    as_run_fills = sum(1 for o in hourly if fill_time(o, bars) is not None)
    print(f"CALIBRATION: replay of as-run orders fills {as_run_fills} (tester had 20 swing trades)\n")

    # ---- 1. the 20 real trades
    t = pd.read_csv(TRADES, parse_dates=["entry_time", "exit_time"])
    t = t[t["mode"] == "swing"].sort_values("entry_time")
    rows = []
    for _, tr in t.iterrows():
        d = 1 if tr["dir"] == "BUY" else -1
        cands = [o for o in hourly if o["dir"] == d and o["start"] <= tr["entry_time"] and abs(o["entry"] - tr["entry_price"]) < 1.0]
        if not cands:
            continue
        o = max(cands, key=lambda x: x["start"])
        a = bars.loc[(bars.index >= tr["entry_time"].floor("min")) & (bars.index <= o["week_end"])]
        sp = a["spread"].to_numpy() * POINT
        tp_mask = (a["high"].to_numpy() >= o["tp1"]) if d > 0 else (a["low"].to_numpy() + sp <= o["tp1"])
        tp_idx = np.flatnonzero(tp_mask)
        upto = a if not len(tp_idx) else a.iloc[:tp_idx[0] + 1]
        usp = upto["spread"].to_numpy() * POINT
        mae = (tr["entry_price"] - upto["low"].min()) if d > 0 else ((upto["high"].to_numpy() + usp).max() - tr["entry_price"])
        rows.append({
            "week": o["week"], "entry_time": tr["entry_time"], "dir": tr["dir"], "entry": tr["entry_price"],
            "pnl$": tr["pnl"], "held_min": round(tr["hold_minutes"], 1), "atr_M30": round(o["atr"], 2),
            "against_before_TP1_ATR": round(mae / o["atr"], 2),
            "later_hit_TP1": bool(len(tp_idx)),
            "hours_to_TP1": round((a.index[tp_idx[0]] - tr["entry_time"]).total_seconds() / 3600, 1) if len(tp_idx) else np.nan,
            "TP1_dist_ATR": round(abs(o["tp1"] - tr["entry_price"]) / o["atr"], 2),
        })
    real = pd.DataFrame(rows)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 20)
    print("=== 1. THE REAL SWING TRADES: how far price went against them before TP1 ===")
    print(real.to_string(index=False))
    losers = real[real["pnl$"] <= 0]
    saved = losers[losers["later_hit_TP1"]]
    print(f"\nlosers: {len(losers)} | later reached TP1 anyway: {len(saved)}")
    if len(saved):
        print("buffer each of those would have needed (ATR):", sorted(saved["against_before_TP1_ATR"].tolist()))
    print()

    # ---- 2. stop-buffer replay on distinct kept orders
    print("=== 2. STOP-BUFFER REPLAY (orders kept until bias flip / level change; $ at 0.01 lot) ===")
    fills = [(o, fill_time(o, bars)) for o in kept]
    fills = [(o, ft) for o, ft in fills if ft is not None]
    print(f"distinct orders {len(kept)}, filled {len(fills)}")
    out = []
    for b in BUFFERS:
        res = []
        for o, ft in fills:
            risk = b * o["atr"]
            if abs(o["tp1"] - o["entry"]) < MIN_RR * risk:
                continue
            res.append(race(o, bars, ft, risk))
        wins = [r for r in res if r[0] == "win"]
        losses = [r for r in res if r[0] == "loss"]
        opens = [r for r in res if r[0] == "open"]
        net = sum(r[1] for r in res)
        out.append({
            "buffer_xATR": b, "trades": len(res), "skipped_RR": len(fills) - len(res), "wins": len(wins),
            "losses": len(losses), "still_open": len(opens),
            "win%": round(len(wins) / len(res) * 100, 1) if res else 0.0,
            "avg_win$": round(np.mean([r[1] for r in wins]), 2) if wins else 0.0,
            "avg_loss$": round(np.mean([r[1] for r in losses]), 2) if losses else 0.0,
            "net$": round(net, 2), "per_trade$": round(net / len(res), 2) if res else 0.0,
            "median_min_to_stop": round(np.median([r[2] for r in losses]), 0) if losses else np.nan,
        })
    print(pd.DataFrame(out).to_string(index=False))
    print()

    # ---- 3. distance from price vs fill rate
    def dist_rows(orders, label):
        recs = []
        for o in orders:
            w = bars.loc[bars.index >= o["start"]]
            if w.empty:
                continue
            bid = w["open"].iloc[0]
            price = bid + w["spread"].iloc[0] * POINT if o["dir"] > 0 else bid
            recs.append({"dist_ATR": abs(price - o["entry"]) / o["atr"], "filled": fill_time(o, bars) is not None})
        df = pd.DataFrame(recs)
        df["bucket"] = pd.cut(df["dist_ATR"], [0, 1, 2, 3, 4, 6, 10, np.inf], right=False)
        g = df.groupby("bucket", observed=False).agg(orders=("filled", "size"), filled=("filled", "sum"))
        g["fill%"] = (g["filled"] / g["orders"].replace(0, np.nan) * 100).round(1)
        print(f"--- {label} ---")
        print(g.to_string())

    print("=== 3. DISTANCE FROM PRICE WHEN PLACED (ATR M30) vs FILL RATE ===")
    dist_rows(hourly, "as run: order lives one hour")
    dist_rows(kept, "kept until bias flip / level change")


if __name__ == "__main__":
    main()
