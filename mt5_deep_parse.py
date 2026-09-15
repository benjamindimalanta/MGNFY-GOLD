"""Deep re-parse of the 15 MT5 Strategy Tester reports already on disk.

Joins the Orders table (initial SL/TP at entry) to the Deals table (actual
fills, exit price, real $ pnl, running balance) to compute per-trade:
R-multiple, hold time, whether the exit stop differs from the initial stop
(trailing/stairstep did or didn't move it), and richer aggregate stats
than the first-pass journal had (streaks with dates, direction split,
session/hour granularity, drawdown *per trade* not just per run).
"""
import glob
import os

import numpy as np
import pandas as pd

DATA_PATH = r"C:\Users\Benja\AppData\Roaming\MetaQuotes\Terminal\53785E099C927DB68A545C249CDBCE06"
OUT = r"C:\Users\Benja\AppData\Local\Temp\claude\C--Users-Benja-OneDrive-Pictures-MSB-OB\c739d792-d8b9-4d83-b2a2-028661b569de\scratchpad"

VALUE_PER_POINT_PER_LOT = 100.0  # tick_value/tick_size = 0.1/0.001, confirmed from symbol_info
LOT = 0.01


def parse_one(path):
    run_id = os.path.splitext(os.path.basename(path))[0]
    week, signal_tf = run_id.rsplit("__", 1)
    tables = pd.read_html(path, flavor="lxml")
    t = tables[1]

    orders_hdr = t.index[t[0] == "Orders"][0]
    deals_hdr = t.index[t[0] == "Deals"][0]

    orders = t.iloc[orders_hdr + 2: deals_hdr - 1].copy()
    orders.columns = ["open_time", "order", "symbol", "type", "vol1", "vol2",
                       "price", "sl", "tp", "time2", "time3", "state", "comment"]
    orders = orders.dropna(subset=["order"])
    orders["order"] = pd.to_numeric(orders["order"], errors="coerce")
    orders["sl"] = pd.to_numeric(orders["sl"], errors="coerce")
    entry_orders = orders[orders["comment"].astype(str).str.startswith(("ATRRegime", "SwingPullback"))].copy()
    entry_orders = entry_orders.set_index("order")["sl"]

    deals = t.iloc[deals_hdr + 2:].copy()
    deals.columns = ["time", "deal", "symbol", "type", "direction", "volume",
                      "price", "order", "commission", "swap", "profit", "balance", "comment"]
    deals = deals.dropna(subset=["time"])
    deals["time"] = pd.to_datetime(deals["time"], errors="coerce")
    deals = deals.dropna(subset=["time"])
    for c in ("profit", "balance", "order", "commission", "swap"):
        deals[c] = pd.to_numeric(deals[c], errors="coerce")

    ins = deals[deals["direction"] == "in"].reset_index(drop=True)
    outs = deals[deals["direction"] == "out"].reset_index(drop=True)
    n = min(len(ins), len(outs))
    ins, outs = ins.iloc[:n].copy(), outs.iloc[:n].copy()

    ins["initial_sl"] = ins["order"].map(entry_orders)

    trades = pd.DataFrame({
        "run_id": run_id, "week": week, "signal_tf": signal_tf,
        "entry_time": ins["time"].values, "dir": ins["type"].str.upper().values,
        "entry_price": pd.to_numeric(ins["price"], errors="coerce").values,
        "initial_sl": ins["initial_sl"].values,
        "exit_time": outs["time"].values,
        "exit_price": pd.to_numeric(outs["price"], errors="coerce").values,
        "exit_comment": outs["comment"].values,
        "pnl": outs["profit"].values,
        "balance_after": outs["balance"].values,
    })

    trades["risk_dollars"] = (trades["entry_price"] - trades["initial_sl"]).abs() * VALUE_PER_POINT_PER_LOT * LOT
    trades["r_multiple"] = trades["pnl"] / trades["risk_dollars"]
    trades["hold_minutes"] = (pd.to_datetime(trades["exit_time"]) - pd.to_datetime(trades["entry_time"])).dt.total_seconds() / 60.0

    def final_sl_from_comment(c):
        c = str(c)
        if c.startswith("sl "):
            try:
                return float(c.split()[1])
            except (IndexError, ValueError):
                return np.nan
        return np.nan

    trades["final_sl_price"] = trades["exit_comment"].map(final_sl_from_comment)
    trades["sl_moved"] = (trades["final_sl_price"] - trades["initial_sl"]).abs() > 0.01
    trades["exit_kind"] = trades["exit_comment"].astype(str).str.extract(r'^(sl|tp\d?|end)', expand=False).fillna("other")

    return trades


def main():
    files = sorted(glob.glob(os.path.join(DATA_PATH, "2026-*.htm")))
    all_trades = [parse_one(f) for f in files]
    trades = pd.concat(all_trades, ignore_index=True)
    trades = trades.sort_values(["signal_tf", "week", "entry_time"]).reset_index(drop=True)
    trades.to_csv(os.path.join(OUT, "mt5_journal_trades_deep.csv"), index=False)
    print(f"Parsed {len(files)} reports, {len(trades)} trades.")
    print(trades[["run_id", "dir", "entry_price", "initial_sl", "exit_price", "pnl",
                   "risk_dollars", "r_multiple", "hold_minutes", "sl_moved", "exit_kind"]].head(15).to_string())
    print()
    print("sl_moved value counts:", trades["sl_moved"].value_counts(dropna=False).to_dict())
    print("risk_dollars describe:\n", trades["risk_dollars"].describe())
    print("r_multiple describe:\n", trades["r_multiple"].describe())


if __name__ == "__main__":
    main()
