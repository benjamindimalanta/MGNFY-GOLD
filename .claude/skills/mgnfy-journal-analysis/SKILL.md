---
name: mgnfy-journal-analysis
description: Analyze MGNFY GOLD EA backtest journal data (win rate, PF, drawdown, timeframe/config comparisons, streaks, entries by hour/weekday) from this repo's journal CSVs and JOURNAL.md. Use whenever the user asks to analyze, compare, or query past MGNFY GOLD backtest results, or wants a new batch of backtests journaled the same way.
---

# MGNFY GOLD journal analysis

This repo is the versioned source + backtest history for the MGNFY GOLD
MQL5 Expert Advisor (XAUUSD, MetaTrader 5). It contains both the EA source
and an offline Python backtest engine with a running journal of every test
run. This skill is about analyzing that history, not about MQL5 itself —
read `README.md` first if you need to understand what the EA does.

## Where the data lives

- **`JOURNAL.md`** — the narrative history. Every backtest batch ever run
  gets an entry here: methodology, config, full results table, and a
  written conclusion. This is the primary source of truth for "what has
  already been tried and what was found" — always read it before
  re-running something, to avoid duplicating work or contradicting an
  already-established finding (there's a "known facts" block near the top
  that summarizes settled conclusions so you don't have to re-derive them).
- **`journal_results_summary.csv`** — one row per backtest *run* (a
  week/period x timeframe x config combination). Columns: `trades, wins,
  losses, win_rate, net, pf, max_dd_pct, avg_win, avg_loss, max_win,
  max_loss, max_consec_wins, max_consec_losses, end_eq, week, week_start,
  signal_tf, config, run_id`. This file is **appended to**, not
  overwritten, across sessions — it accumulates every batch ever run, so
  filter by date/run_id prefix if you only want one batch.
- **`journal_all_trades.csv`** — every individual trade from every run,
  one row each: `run_id, week, signal_tf, config, entry_time, dir, entry,
  sl_initial, tp1, tp2, tp3, exit_time, exit_reason, lots, pnl,
  spread_cost, tp1_hit, tp2_hit`. This is the ground truth for any
  finer-grained question (time-of-day, day-of-week, exit-reason
  breakdown, streaks, R-multiple distribution) that the summary CSV can't
  answer on its own.
- **`data/journal_trades/<run_id>.csv`** — the same per-trade data, split
  one file per run (gitignored, regenerable — see below). Prefer the
  combined `journal_all_trades.csv` unless you specifically need one run
  isolated.
- **`data/symbol_meta.csv`, `data/bars_*.csv`** — gitignored raw inputs
  (account/symbol metadata, OHLC bars). Not committed because they're
  regenerable from the live MT5 terminal and would bloat the repo; if
  they're missing, re-run `journal_runner.py` (needs the `MetaTrader5`
  Python package and a running MT5 terminal logged into the account named
  in `journal_run_meta.json`).

## Before analyzing: read the caveats

Every `JOURNAL.md` entry states its own methodology and caveats — READ
THEM before drawing conclusions, especially:
- Whether runs compound across periods or each reset to a fresh deposit
  (affects whether summed `net` across rows means anything as a portfolio
  number, or only describes each period in isolation).
- Any noted artifacts from the test methodology itself (e.g. the
  2026-09-15 batch found that per-week state resets create a spurious
  Monday/Tuesday entry skew — that's a methodology artifact, not a real
  time-of-day edge; don't rediscover it as if it were new).
- Sample size per cell — anything under ~20 trades is not a stable win
  rate/PF estimate. Say so explicitly rather than reporting a headline
  number from a 3-trade cell as if it were reliable.

## Typical analyses

Load with pandas:
```python
import pandas as pd
trades = pd.read_csv("journal_all_trades.csv", parse_dates=["entry_time", "exit_time"])
runs = pd.read_csv("journal_results_summary.csv")
```

- **Win rate / PF / net by any slice**: group `trades` by `config`,
  `signal_tf`, `exit_reason`, or a derived column (`entry_time.dt.hour`,
  `.dt.day_name()`, `.dt.month`) and aggregate `pnl` (win rate = `(pnl>0).mean()`,
  PF = `pnl[pnl>0].sum() / -pnl[pnl<=0].sum()`).
- **Consecutive win/loss streaks**: sort by `entry_time` within a run,
  run-length-encode `pnl > 0`.
- **R-multiple distribution**: `pnl` isn't already expressed in R — derive
  it from `(exit price implied by pnl) vs (entry - sl_initial)` per trade,
  or extend `journal_runner.py` to record R directly on future runs.
- **Config/timeframe comparison**: pivot `runs` on `config`/`signal_tf`
  with `win_rate`/`pf`/`net` as values — this is what most of
  `JOURNAL.md`'s sweep tables already are; reuse that shape for
  consistency when writing up a new one.
- **Exit-reason breakdown** (`exit_reason`: `sl`, `tp3`, `tp2_full`,
  `eom_markout`): tells you whether losses are mostly clean stop-outs vs.
  whipsaws, and whether winners are usually riding to TP3 or getting cut
  by the ATR trail first.

## Running a new batch

`journal_runner.py` is the reusable entry point — it picks N random weeks
(`random.SystemRandom`, printed before any result is seen — keep this
property when modifying it, it's what makes the sampling defensible),
tests them across configured timeframes/configs, and appends to all three
output files plus writes a fresh `journal_run_meta.json`. Set
`FIXED_WEEKS = []` at the top to draw a new random sample instead of
reusing a previous one; only reuse a fixed list when the explicit goal is
an apples-to-apples rerun after a code/config fix (as the 2026-09-15 batch
did after correcting a baseline-config bug).

After running, **write the JOURNAL.md entry in the same session** — don't
leave raw CSVs uninterpreted. Follow the existing entries' structure:
trigger/context, method, caveats, results table(s), and a plain-language
conclusion. If the finding contradicts or refines an earlier "known fact"
at the top of `JOURNAL.md`, update that block too.

## Reporting to the user

Lead with the honest headline number (win rate, PF, net) and its sample
size, not the best-looking cherry from a sub-table. If asked about a
specific win-rate or profit target, check it against the pooled (not
per-run) numbers — per-run cells are small-sample and volatile. State
plainly when a target is architecturally incompatible with the EA's
design (see the 85%-win-rate discussion in the 2026-09-15 JOURNAL.md entry
for the reasoning pattern to reuse: tie the limit back to a structural
property of the exit/entry logic, not just "the numbers don't show it").
