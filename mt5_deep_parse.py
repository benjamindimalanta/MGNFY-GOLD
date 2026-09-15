"""Parse an MT5 Strategy Tester report (.htm) into one row per trade.

Joins the Orders table (initial SL at entry) to the Deals table. A trade starts at an "in" deal and collects
every following "out" deal until the next "in" (the EA holds one position at a time), so partial closes at
TP1/TP2 are summed into one trade. Per trade: P/L, volume, R-multiple (P/L / initial risk at the traded volume),
hold time, number of exit deals, and the final exit's kind (sl / tp / end / other).
"""
import glob
import os

import numpy as np
import pandas as pd

DATA_PATH = r"C:\Users\Benja\AppData\Roaming\MetaQuotes\Terminal\53785E099C927DB68A545C249CDBCE06"
OUT = r"C:\Users\Benja\AppData\Local\Temp\claude\C--Users-Benja-OneDrive-Pictures-MSB-OB\c739d792-d8b9-4d83-b2a2-028661b569de\scratchpad"

VALUE_PER_POINT_PER_LOT = 100.0  # XAUUSDm: tick_value/tick_size = 0.1/0.001 -> $100 per 1.00 price move per lot


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
    entry_sl = entry_orders.set_index("order")["sl"].to_dict()

    deals = t.iloc[deals_hdr + 2:].copy()
    deals.columns = ["time", "deal", "symbol", "type", "direction", "volume",
                     "price", "order", "commission", "swap", "profit", "balance", "comment"]
    deals = deals.dropna(subset=["time"])
    deals["time"] = pd.to_datetime(deals["time"], errors="coerce")
    deals = deals.dropna(subset=["time"])
    for c in ("profit", "balance", "order", "commission", "swap", "volume", "price"):
        # the report writes thousands with a space ("5 080.46"), which to_numeric would turn into NaN
        deals[c] = pd.to_numeric(deals[c].astype(str).str.replace(r"[\s ]", "", regex=True), errors="coerce")

    rows, cur = [], None
    for d in deals.itertuples(index=False):
        if d.direction == "in":
            if cur is not None and cur["n_exits"] > 0:
                rows.append(cur)
            cur = {"entry_time": d.time, "dir": str(d.type).upper(), "entry_price": d.price,
                   "initial_sl": entry_sl.get(d.order, np.nan), "volume": d.volume, "pnl": 0.0, "swap_comm": 0.0,
                   "n_exits": 0, "exit_time": pd.NaT, "exit_price": np.nan, "exit_comment": "", "balance_after": np.nan}
        elif d.direction == "out" and cur is not None:
            cur["pnl"] += 0.0 if pd.isna(d.profit) else d.profit
            cur["swap_comm"] += (0.0 if pd.isna(d.swap) else d.swap) + (0.0 if pd.isna(d.commission) else d.commission)
            cur["n_exits"] += 1
            cur["exit_time"], cur["exit_price"] = d.time, d.price
            cur["exit_comment"], cur["balance_after"] = d.comment, d.balance
    if cur is not None and cur["n_exits"] > 0:
        rows.append(cur)

    cols = ["entry_time", "dir", "entry_price", "initial_sl", "exit_time", "exit_price", "exit_comment", "pnl",
            "balance_after", "volume", "n_exits", "swap_comm"]
    trades = pd.DataFrame(rows, columns=cols)
    trades.insert(0, "signal_tf", signal_tf)
    trades.insert(0, "week", week)
    trades.insert(0, "run_id", run_id)
    for c in ("entry_price", "initial_sl", "exit_price", "pnl", "balance_after", "volume", "n_exits", "swap_comm"):
        trades[c] = pd.to_numeric(trades[c], errors="coerce")  # also keeps a zero-trade report numeric
    trades["pnl"] = trades["pnl"].round(2)

    trades["risk_dollars"] = (trades["entry_price"] - trades["initial_sl"]).abs() * VALUE_PER_POINT_PER_LOT * trades["volume"]
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


if __name__ == "__main__":
    main()
