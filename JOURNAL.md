# MGNFY GOLD -- Backtest Journal

Running log of every backtest batch tried and its result, driven by MT5's
own Strategy Tester (not a custom simulation), so nothing gets lost between
sessions. Newest entries at the bottom. Each entry is self-contained
(dataset, config, full metrics).

**Standard report fields:** Trades / Win / Loss / Win% / Net $ / PF (profit
factor) / MaxDD% (max drawdown) / End Eq (ending equity from $100 start).

**Known facts established so far (don't need to re-test to confirm):**
- The live `MGNFY GOLD.mq5` (v1.11, currently compiled/attached in MT5) has
  a real bug, confirmed against MT5's own real-tick Strategy Tester (not
  just a custom simulation): at 0.01 lot (MT5's minimum), the 1R/2R/3R
  partial take-profit system silently fails -- 33%/33% of 0.01 lot rounds
  to 0.00, so `ClosePartial()` refuses and `tp1Hit` never becomes true.
  TP1's breakeven-move and TP2/TP3 never fire. **Direct evidence:** across
  481 real trades in the 2026-09-15 batch below, exactly 0 closed via a TP
  level -- 477 were stop-loss exits and the remaining 4 were forced
  end-of-test closes. Not a single partial take-profit fired. A v1.12 fix
  exists (source recovered into this repo) but has not yet been deployed
  to the live MT5 terminal -- pending the user's explicit go-ahead (this
  is a "production deploy" the session's safety layer correctly declined
  to do without confirmation).
- MACD filter and H4 trend filter are off in the settings tested so far
  (matches the "Balance" preset / the settings visible in the user's own
  manual GUI backtest).
- Fixed 0.01-lot sizing on a $100 account regularly triggers a margin
  lockout after a short losing stretch.

---

## 2026-09-15 -- Correction: the previous Python-based journal and backtester were wrong, removed

An earlier session (not this one) built an offline Python bar-stepping
backtester (`backtest_mgnfy.py` + friends) and a `JOURNAL.md` from it. The
user correctly identified that this produced results that don't match
MT5's own Strategy Tester on identical settings -- confirming it by
pointing out that even feeding it the exact settings from their own manual
MT5 backtest still came back negative, when the real MT5 tester (see
below) does not. **That entire Python engine, its JOURNAL.md, and all CSVs
derived from it were deleted from this repo** (see the git history for the
removal commit). Root cause: bar-close signal evaluation is not equivalent
to real-tick execution for a signal this sensitive to intrabar timing, and
apparently diverged enough from ground truth to be actively misleading
rather than merely imprecise.

**Going forward, this journal is built exclusively from MT5's own
Strategy Tester** (`terminal64.exe /config:<ini>`, `Model=4` -- "every
tick based on real ticks", the same engine and same real broker tick data
the user's own manual GUI backtest used), automated from the command line.
Two operational gotchas discovered getting this working, recorded here so
they don't have to be rediscovered:

1. **The MT5 terminal must be fully closed before each `/config` launch.**
   Passing `/config` to an already-running terminal instance does not
   apply the requested dates/settings -- it silently reuses whatever was
   last configured in the GUI. Confirmed empirically: an identical `/config`
   run against an already-open terminal returned a report for the *old*
   cached date range, not the one requested. Fix: `taskkill terminal64.exe`
   before every launch, let it fully exit, then launch fresh with
   `ShutdownTerminal=1` so it closes itself when the test completes.
2. **`Report=` in the `[Tester]` ini section must be a flat filename, not
   a subfolder path.** A nested path (e.g. `journal_reports\run1`) silently
   produces no report at all. Reports land directly in the terminal's data
   path root (`...\Terminal\<hash>\<name>.htm`), not in `MQL5\Files\`.
3. The exported `.htm` report contains `Orders` and `Deals` tables (real
   per-tick fill data -- entry/exit price, time, profit, running balance,
   comment) but **not** a pre-formatted `Results` summary block when
   generated this way -- all summary stats (win rate, PF, drawdown,
   streaks) in this journal are computed directly from the `Deals` table,
   which is if anything more trustworthy than parsing a formatted summary.

### Method

`mt5_journal.py` (this session, replaces the removed `journal_runner.py`):
picks N random Monday-start weeks with `random.SystemRandom` (printed
*before* any test runs, so the sample can't be cherry-picked), and for
each week runs MT5's real Strategy Tester on 3 signal timeframes (the
EA's `InpTF` input: M15, M30, H1), using **the exact same input settings
as the user's own manual GUI backtest** (confirmed match: ATRMultiplier
2.0, StopLossPercent 0.7, MACD filter off, Trail_ATR_Mult 1.5 -- the
"Balance" preset). No custom simulation logic is involved anywhere in this
pipeline -- every number below came out of MT5 itself.

Candidate weeks were the 12 Monday-start weeks fully inside this
account's available tick-history window (2026-06-15 through "today",
2026-09-15). 5 were drawn at random:

```
2026-06-22 -> 2026-06-28
2026-06-29 -> 2026-07-05
2026-07-13 -> 2026-07-19
2026-07-27 -> 2026-08-02
2026-08-17 -> 2026-08-23
```

15 real Strategy Tester runs (5 weeks x 3 timeframes), 481 real trades
total. Every trade is saved in `mt5_journal_trades.csv` (columns:
run_id, week, signal_tf, entry_time, dir, entry_price, exit_time,
exit_price, exit_comment, volume, pnl, balance_after) -- committed to the
repo, nothing summarized away. `mt5_journal_summary.csv` has one row per
run. Re-run any time with `python mt5_journal.py` (needs `N_WEEKS` env var,
default 5, and a local MT5 terminal at the hardcoded path in the script).

**Caveat:** each week starts the regime-channel state cold (no warm-up
bars before `FromDate` -- MT5's tester doesn't support a separate
"priming, not trading" period the way a custom script could), so the
first few bars of every run start from `prevTrend=0`/`prevUp1=prevDn1=0`
rather than an already-primed channel. This is an inherent limitation of
testing short, isolated windows (whether via this script or manually in
the GUI) -- not a bug in the automation.

### Full per-run results (15 runs, real MT5 Strategy Tester, real ticks)

| Week | TF | Trades | Wins | Win% | Net $ | PF | MaxDD% | MaxConsecLoss | End Eq (from $100) |
|---|---|---|---|---|---|---|---|---|---|
| 2026-06-22_to_2026-06-28 | M15 | 75 | 25 | 33.3 | -50.92 | 0.87 | 71.7 | 10 | 47.48 |
| 2026-06-22_to_2026-06-28 | M30 | 4 | 0 | 0.0 | -56.99 | 0.00 | 50.6 | 4 | 43.01 |
| 2026-06-22_to_2026-06-28 | H1 | 10 | 4 | 40.0 | -54.33 | 0.43 | 48.4 | 2 | 45.67 |
| 2026-06-29_to_2026-07-05 | M15 | 10 | 2 | 20.0 | -52.71 | 0.13 | 52.3 | 4 | 47.29 |
| 2026-06-29_to_2026-07-05 | M30 | 43 | 17 | 39.5 | 90.06 | 1.36 | 45.2 | 6 | 189.00 |
| 2026-06-29_to_2026-07-05 | H1 | 4 | 0 | 0.0 | -61.25 | 0.00 | 59.3 | 4 | 38.75 |
| 2026-07-13_to_2026-07-19 | M15 | 91 | 33 | 36.3 | 58.54 | 1.15 | 59.8 | 8 | 155.35 |
| 2026-07-13_to_2026-07-19 | M30 | 46 | 17 | 37.0 | 4.52 | 1.02 | 44.4 | 8 | 102.92 |
| 2026-07-13_to_2026-07-19 | H1 | 23 | 9 | 39.1 | -21.50 | 0.88 | 64.5 | 4 | 76.90 |
| 2026-07-27_to_2026-08-02 | M15 | 84 | 40 | 47.6 | 122.33 | 1.51 | 28.3 | 4 | 219.67 |
| 2026-07-27_to_2026-08-02 | M30 | 40 | 18 | 45.0 | 170.24 | 2.08 | 26.4 | 4 | 267.58 |
| 2026-07-27_to_2026-08-02 | H1 | 18 | 6 | 33.3 | -53.65 | 0.64 | 67.6 | 3 | 44.75 |
| 2026-08-17_to_2026-08-23 | M15 | 14 | 3 | 21.4 | -52.21 | 0.25 | 49.4 | 6 | 47.79 |
| 2026-08-17_to_2026-08-23 | M30 | 12 | 4 | 33.3 | -49.86 | 0.28 | 46.0 | 3 | 49.61 |
| 2026-08-17_to_2026-08-23 | H1 | 7 | 1 | 14.3 | -63.81 | 0.07 | 58.0 | 4 | 35.66 |

### Pooled by timeframe (all 5 weeks combined)

| Signal TF | Trades | Wins | Win% | Net $ (sum of 5 isolated $100 runs) | PF | Avg Win $ | Avg Loss $ |
|---|---|---|---|---|---|---|---|
| M15 | 274 | 103 | 37.6 | 25.03 | 1.02 | 11.33 | -6.68 |
| M30 | 145 | 56 | 38.6 | 157.97 | 1.20 | 16.58 | -8.66 |
| H1 | 62 | 20 | 32.3 | -254.54 | 0.54 | 14.95 | -13.18 |

**Overall pooled (all 481 trades):** win rate 37.2%, PF 0.97, net -$71.54
(sum of 15 isolated $100 runs -- not a compounding portfolio number, see
caveat in the per-run table's own reading). This is genuinely close to
breakeven, and directionally consistent with the user's own Aug1-Sep14 GUI
result (36.2% win rate, PF 1.16) -- unlike the removed Python engine's
numbers, which were uniformly, implausibly bad. **M15 and M30 are roughly
breakeven-to-positive pooled; H1 is the clear laggard** (PF 0.54, and 2 of
the 5 H1 weeks had only 4 trades each -- too thin a signal at that
timeframe over a single week to reliably trade or judge).

### Pooled by weekday (all 481 trades, all TFs/weeks)

| Weekday | Trades | Wins | Win% | Net $ | PF |
|---|---|---|---|---|---|
| Friday | 54 | 24 | 44.4 | 87.74 | 1.44 |
| Monday | 142 | 44 | 31.0 | -257.87 | 0.67 |
| Sunday | 8 | 2 | 25.0 | -42.49 | 0.01 |
| Thursday | 87 | 32 | 36.8 | -99.80 | 0.78 |
| Tuesday | 100 | 34 | 34.0 | -5.94 | 0.99 |
| Wednesday | 90 | 43 | 47.8 | 246.82 | 1.53 |

(Small-sample caveat applies same as always -- Sunday's 8 trades and
individual per-weekday PF numbers are not something to trade around
without a much larger sample. Included for completeness per the request
to journal everything, not as an actionable finding.)

### Confirms the min-lot partial-TP bug with real data

Every one of the 481 real trades exited one of two ways: **477 stop-loss
hits, 4 forced end-of-test closes -- zero TP1/TP2/TP3 hits.** This is the
same bug already identified in this repo's source comments and CHANGELOG,
now confirmed against MT5's own tester rather than assumed from reading
the code: at 0.01 lot, `ClosePartial()` can never split off a fraction
large enough to round to a tradeable volume, so the entire 1R/2R/3R ladder
is dead weight on a $100/0.01-lot account. The EA is currently running as
if it were "stop-loss-only, no take-profit, plus an ATR trail" -- and
*still* comes out close to breakeven pooled (PF 0.97). That's a genuinely
interesting result: it suggests the ATR trailing stop alone is doing real
work, and that fixing the TP bug (letting winners actually bank partial
profit at 1R/2R before the trail catches them) could plausibly improve
results further -- worth testing for real once v1.12 is deployed and the
same random-week methodology can be pointed at it.

### On the requested 85% win-rate target

Real data changes the *specific numbers* from the removed Python
analysis but not the conclusion: 37.2% pooled win rate, best single-run
win rate 47.6% (84 trades, 2026-07-27 week, M15 -- a large-enough sample
to be a real number, not noise). Nowhere near 85%, and the reason is the
same structural one as before: **TP1 sits at exactly 1R, the same
distance as the stop**, which caps how often a breakout-style entry can
win before a full redesign of the exit ladder (see the removed journal's
analysis of tightening TP1 -- not re-run here since that tool is gone, but
the logic still holds: shrinking TP1 raises win rate only by shrinking
each win's size, which is a trade-off, not a free improvement). Treat 85%
as off the table for this architecture; a credible target is **PF > 1.3
at 35-48% win rate**, which M15 and M30 are already within range of
before any changes (M15 pooled PF 1.02, best single week 1.51; M30 pooled
PF 1.20, best single week 2.08).

### Next steps

- Get explicit sign-off to deploy v1.12 (bug fix + stairstep stop lock)
  to the live MT5 terminal, then re-run this exact same methodology
  (same random-week machinery, same weeks if a clean before/after
  comparison is wanted) to measure the real effect -- not simulate it.
- H1 is underperforming and thin-sampled; deprioritize it or gather more
  weeks before drawing conclusions there.
- Consider testing the Conservative preset's filters (MACD + H4 trend +
  trend-flip-required) through this same real-MT5 pipeline before
  trusting any conclusion about whether filtering helps -- the removed
  Python journal's finding that filtering hurt PF was exactly the kind of
  claim this correction should NOT be trusted at face value; it needs
  re-verifying against the real tester before being treated as fact again.
