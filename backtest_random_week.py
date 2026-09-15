"""Pick a genuinely random 1-week window from Jun-Sep 2026 and backtest it.

The week is chosen with Python's OS-entropy RNG (random.SystemRandom) BEFORE
any data is pulled or any result is seen — the choice is printed first, so
it's verifiable that it wasn't cherry-picked to make the EA look good or bad.
"""
from datetime import datetime, timedelta
import random

import MetaTrader5 as mt5
import pandas as pd

import backtest_mgnfy as bt

RANGE_START = datetime(2026, 6, 1)   # first candidate Monday
RANGE_END_EXCL = datetime(2026, 9, 8)  # last candidate week must fully end by "today" (2026-09-14)
WARMUP_DAYS = 5  # extra days of history pulled before the week, to prime ATR/trend state (not traded on)


def candidate_mondays():
    d = RANGE_START
    # snap to the first Monday on/after RANGE_START
    d += timedelta(days=(7 - d.weekday()) % 7)
    out = []
    while d < RANGE_END_EXCL:
        out.append(d)
        d += timedelta(days=7)
    return out


def main():
    candidates = candidate_mondays()
    rng = random.SystemRandom()
    week_start = rng.choice(candidates)
    week_end = week_start + timedelta(days=7)

    print(f"Candidate weeks (Mon-Sun) considered: {len(candidates)}")
    print(f"  from {candidates[0].date()} to {candidates[-1].date()}")
    print(f"RANDOMLY SELECTED WEEK: {week_start.date()} -> {(week_end - timedelta(days=1)).date()}")
    print()

    pull_start = week_start - timedelta(days=WARMUP_DAYS)

    mt5.initialize()
    sym = "XAUUSDm"
    mt5.symbol_select(sym, True)

    def fetch(tf):
        rates = mt5.copy_rates_range(sym, tf, pull_start, week_end)
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        return df.rename(columns={"tick_volume": "tickvol"})[["time", "open", "high", "low", "close", "tickvol", "spread"]].set_index("time")

    m15 = fetch(mt5.TIMEFRAME_M15)
    m1 = fetch(mt5.TIMEFRAME_M1)
    info = mt5.symbol_info(sym)
    acct = mt5.account_info()
    mt5.shutdown()

    print(f"Pulled {len(m15)} M15 bars, {len(m1)} M1 bars "
          f"(includes {WARMUP_DAYS}d warm-up before the traded week, not traded on)")
    print()

    label = f"{week_start.date()}_to_{(week_end - timedelta(days=1)).date()}"
    m15.to_csv(f"{bt.DATA_DIR}/bars_m15_{label}.csv")
    m1.to_csv(f"{bt.DATA_DIR}/bars_m1_{label}.csv")

    cfg = bt.Cfg()  # Balance preset (same as the August run, for apples-to-apples comparison)
    trades, final_eq = bt.run(
        cfg, m15=m15, m1=m1, signal_start=week_start,
        deposit=acct.balance, leverage=acct.leverage, contract_size=info.trade_contract_size,
        tick_value=info.trade_tick_value, tick_size=info.trade_tick_size, point=info.point,
        min_lot=info.volume_min, lot_step=info.volume_step, max_lot=info.volume_max,
    )
    bt.summarize(trades, acct.balance)


if __name__ == "__main__":
    main()
