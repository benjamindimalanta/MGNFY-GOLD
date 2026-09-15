---
name: mgnfy-journal-analysis
description: Analyze MGNFY GOLD EA backtest journal data (win rate, PF, drawdown, timeframe comparisons, streaks, entries by hour/weekday) from this repo's journal CSVs and JOURNAL.md, all sourced from MT5's real Strategy Tester. Use whenever the user asks to analyze, compare, or query past MGNFY GOLD backtest results, or wants a new batch of real-MT5 backtests journaled the same way.
---

# MGNFY GOLD journal analysis

This repo is the versioned source + backtest history for the MGNFY GOLD
MQL5 Expert Advisor (XAUUSD, MetaTrader 5). This skill is about analyzing
that history, not about MQL5 itself — read `README.md` first to understand
what the EA does.

## IMPORTANT: this journal is real-MT5-only — do not reintroduce a custom simulator

An earlier version of this journal was built on a custom Python
bar-stepping backtest engine. **It was deleted (2026-09-15) because its
numbers didn't match MT5's own Strategy Tester on identical settings and
were actively misleading**, not merely imprecise — see the top entry of
`JOURNAL.md` for the full story. If you're tempted to write a faster
custom simulator to avoid the overhead of driving the real MT5 terminal:
don't, unless the user explicitly asks for one and understands it's an
approximation to be validated against the real tester before being
trusted. Every number in this journal must trace back to an actual MT5
Strategy Tester run.

## Where the data lives

- **`JOURNAL.md`** — the narrative history: methodology, full results
  tables, and written conclusions for every batch. Read it before
  re-running anything, to avoid duplicating work or contradicting an
  already-established finding (the "known facts" block near the top
  summarizes settled conclusions).
- **`mt5_journal_summary.csv`** — one row per backtest *run* (a week x
  timeframe combination): `trades, wins, losses, win_rate, net, pf,
  max_dd_pct, avg_win, avg_loss, max_win, max_loss, max_consec_wins,
  max_consec_losses, end_eq, run_id, week, signal_tf, status`.
- **`mt5_journal_trades.csv`** — every individual trade, sourced directly
  from MT5's own Deals table (not derived/simulated): `run_id, week,
  signal_tf, entry_time, dir, entry_price, exit_time, exit_price,
  exit_comment, volume, pnl, balance_after`. `exit_comment` carries MT5's
  own exit reason (e.g. `sl 4182.215`, or `end of test` for a forced
  mark-to-market close at the test boundary) — use it to check whether
  TP levels are actually firing (as of 2026-09-15, they are not — see
  JOURNAL.md's bug writeup).
- **`mt5_journal_by_hour.csv` / `mt5_journal_by_weekday.csv`** — pooled
  entry-time breakdowns, already computed.

## Running a new batch

`mt5_journal.py` is the entry point. It:
1. Kills any running MT5 terminal (a `/config` launch against an
   already-running instance silently ignores the requested dates —
   confirmed the hard way; always start from a clean terminal).
2. Picks N random Monday-start weeks with `random.SystemRandom`, printed
   *before* any test runs — keep this property in any modification, it's
   what makes the sampling defensible.
3. For each week x timeframe (M15/M30/H1 by default), writes a `[Tester]`
   ini (`Model=4`, real ticks — the authoritative fidelity mode, same as
   the user's own manual GUI backtests), launches
   `terminal64.exe /config:<ini>` fresh, waits for it to self-close
   (`ShutdownTerminal=1`), and parses the resulting `.htm` report's
   `Deals` table with `pandas.read_html(path, flavor="lxml")`.
4. Appends to the summary/trades CSVs.

Run with `python mt5_journal.py` (`N_WEEKS` env var controls sample size,
default 5). Needs the MT5 terminal installed at the path hardcoded near
the top of the script (`TERMINAL_EXE`) and a working `MetaTrader5`-adjacent
setup — no Python package is actually required for this script beyond
`pandas`/`lxml`, since it drives the terminal via subprocess, not the
`MetaTrader5` API package.

**Two ini gotchas, already solved in the script but worth knowing if you
touch it:** `Report=` in `[Tester]` must be a flat filename (a nested path
silently produces no report), and reports land in the terminal's data path
root, not `MQL5/Files/`.

After running, **write the JOURNAL.md entry in the same session** — follow
the existing entry's structure (trigger/context, method, caveats, full
results table, pooled tables, and a plain-language conclusion). If a
finding contradicts or refines an earlier "known fact," update that block
at the top of `JOURNAL.md` too, and say explicitly that it supersedes the
old claim rather than leaving both to coexist ambiguously.

## Typical analyses

```python
import pandas as pd
trades = pd.read_csv("mt5_journal_trades.csv", parse_dates=["entry_time", "exit_time"])
runs = pd.read_csv("mt5_journal_summary.csv")
```

- **Win rate / PF / net by any slice**: group `trades` by `signal_tf`,
  `week`, or a derived column (`entry_time.dt.hour`, `.dt.day_name()`) and
  aggregate `pnl`.
- **Exit-reason breakdown**: `trades["exit_comment"].str.extract(r'^(sl|tp\d?|end)')`
  — tells you whether TP levels are firing at all (a real, previously-found
  bug: at 0.01 lot they weren't) or whether losses are clean stop-outs.
- **Consecutive win/loss streaks**: sort by `entry_time` within a `run_id`,
  run-length-encode `pnl > 0`.
- **Config/timeframe comparison**: pivot `runs` on `signal_tf` with
  `win_rate`/`pf`/`net` as values.

## Reporting to the user

Lead with the honest pooled number (win rate, PF, net) and its sample
size, not the best-looking cherry from a sub-table — per-run cells with
under ~20 trades are not stable estimates, say so explicitly. If asked
about a specific win-rate or profit target, check it against pooled
numbers, and if the target is architecturally incompatible with the EA's
exit design (see the 85%-win-rate discussion in JOURNAL.md for the
reasoning pattern to reuse), say so plainly rather than chasing it with
parameter tweaks that can't get there.
