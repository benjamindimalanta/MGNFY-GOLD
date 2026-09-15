# MGNFY GOLD — Backtest Journal

Running log of every backtest combination tried and its result, so nothing
gets lost between sessions. Newest entries at the bottom. Each entry is
self-contained (dataset, config, full metrics) — you shouldn't need to
re-read earlier entries to understand a later one.

**Standard report fields:** Trades / Win / Loss / Win% / Net $ / PF (profit
factor) / MaxDD% (max drawdown) / End Eq (ending equity from $100 start
unless noted).

**Known facts established so far (don't need to re-test to confirm):**
- The live `MGNFY GOLD.mq5` (v1.11) has a real bug: at 0.01 lot (MT5's
  minimum), the 1R/2R/3R partial take-profit system silently fails —
  33%/33% of 0.01 lot rounds to 0.00, so `ClosePartial()` refuses and
  `tp1Hit` never becomes true. TP1's breakeven-move and TP2/TP3 never fire.
  Only the independent ATR trailing stop still offers any protection.
  `backtest_mgnfy.py`'s `fix_min_lot_tp1_bug` flag can reproduce the bug
  (`False`) or the fixed behavior (`True`, default from 2026-09-14 onward).
- MACD filter and H4 trend filter are OFF by default on every preset
  except Conservative — for Balance/Active/TEST Trading, MACD is computed
  but never used in a trading decision.
- Fixed 0.01-lot sizing on a $100 account regularly triggers a margin
  lockout after a short losing stretch (needs ~20% margin headroom above
  the ~$40+ margin cost of even the minimum lot at current gold prices).

---

## Sweep: 2026-09-14 21:24 — full entry/filter/sizing grid, August 2026 (31d, real XAUUSDm broker data)

Starting equity: $100.00. TP1-partial-close bug fix applied (`fix_min_lot_tp1_bug=True`). 48 combinations tested.

| Midline brk | Trend-flip req | MACD filter | H4 trend filter | Sizing | Trades | Win | Loss | Win% | Net $ | PF | MaxDD% | End Eq |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| False | True | True | True | fixed | 7 | 0 | 7 | 0.0 | -47.77 | 0.00 | 47.8 | 52.23 |
| False | True | True | True | risk0.5 | 7 | 0 | 7 | 0.0 | -47.77 | 0.00 | 47.8 | 52.23 |
| False | True | True | True | risk1.0 | 7 | 0 | 7 | 0.0 | -47.77 | 0.00 | 47.8 | 52.23 |
| False | True | False | True | fixed | 12 | 2 | 10 | 16.7 | -48.88 | 0.32 | 48.9 | 51.12 |
| False | True | False | True | risk0.5 | 12 | 2 | 10 | 16.7 | -48.88 | 0.32 | 48.9 | 51.12 |
| False | True | False | True | risk1.0 | 12 | 2 | 10 | 16.7 | -48.88 | 0.32 | 48.9 | 51.12 |
| True | True | True | True | fixed | 7 | 0 | 7 | 0.0 | -49.15 | 0.00 | 49.2 | 50.85 |
| True | True | True | True | risk0.5 | 7 | 0 | 7 | 0.0 | -49.15 | 0.00 | 49.2 | 50.85 |
| True | True | True | True | risk1.0 | 7 | 0 | 7 | 0.0 | -49.15 | 0.00 | 49.2 | 50.85 |
| False | True | True | False | fixed | 7 | 0 | 7 | 0.0 | -49.78 | 0.00 | 49.8 | 50.22 |
| False | True | True | False | risk0.5 | 7 | 0 | 7 | 0.0 | -49.78 | 0.00 | 49.8 | 50.22 |
| False | True | True | False | risk1.0 | 7 | 0 | 7 | 0.0 | -49.78 | 0.00 | 49.8 | 50.22 |
| True | True | False | True | fixed | 10 | 1 | 9 | 10.0 | -50.13 | 0.25 | 50.1 | 49.87 |
| True | True | False | True | risk0.5 | 10 | 1 | 9 | 10.0 | -50.13 | 0.25 | 50.1 | 49.87 |
| True | True | False | True | risk1.0 | 10 | 1 | 9 | 10.0 | -50.13 | 0.25 | 50.1 | 49.87 |
| False | False | False | True | fixed | 16 | 3 | 13 | 18.8 | -51.11 | 0.31 | 51.1 | 48.89 |
| False | False | False | True | risk0.5 | 16 | 3 | 13 | 18.8 | -51.11 | 0.31 | 51.1 | 48.89 |
| False | False | False | True | risk1.0 | 16 | 3 | 13 | 18.8 | -51.11 | 0.31 | 51.1 | 48.89 |
| True | False | True | False | fixed | 24 | 8 | 16 | 33.3 | -51.54 | 0.35 | 51.5 | 48.46 |
| True | False | True | False | risk0.5 | 24 | 8 | 16 | 33.3 | -51.54 | 0.35 | 51.5 | 48.46 |
| True | False | True | False | risk1.0 | 24 | 8 | 16 | 33.3 | -51.54 | 0.35 | 51.5 | 48.46 |
| True | False | False | True | fixed | 24 | 7 | 17 | 29.2 | -51.93 | 0.37 | 51.9 | 48.07 |
| True | False | False | True | risk0.5 | 24 | 7 | 17 | 29.2 | -51.93 | 0.37 | 51.9 | 48.07 |
| True | False | False | True | risk1.0 | 24 | 7 | 17 | 29.2 | -51.93 | 0.37 | 51.9 | 48.07 |
| False | True | False | False | fixed | 11 | 2 | 9 | 18.2 | -52.03 | 0.15 | 52.0 | 47.97 |
| False | True | False | False | risk0.5 | 11 | 2 | 9 | 18.2 | -52.03 | 0.15 | 52.0 | 47.97 |
| False | True | False | False | risk1.0 | 11 | 2 | 9 | 18.2 | -52.03 | 0.15 | 52.0 | 47.97 |
| False | False | True | False | fixed | 8 | 0 | 8 | 0.0 | -52.09 | 0.00 | 52.1 | 47.91 |
| False | False | True | False | risk0.5 | 8 | 0 | 8 | 0.0 | -52.09 | 0.00 | 52.1 | 47.91 |
| False | False | True | False | risk1.0 | 8 | 0 | 8 | 0.0 | -52.09 | 0.00 | 52.1 | 47.91 |
| True | False | False | False | fixed | 16 | 5 | 11 | 31.2 | -52.83 | 0.17 | 52.8 | 47.17 |
| True | False | False | False | risk0.5 | 16 | 5 | 11 | 31.2 | -52.83 | 0.17 | 52.8 | 47.17 |
| True | False | False | False | risk1.0 | 16 | 5 | 11 | 31.2 | -52.83 | 0.17 | 52.8 | 47.17 |
| True | True | False | False | fixed | 9 | 1 | 8 | 11.1 | -53.27 | 0.06 | 53.3 | 46.73 |
| True | True | False | False | risk0.5 | 9 | 1 | 8 | 11.1 | -53.27 | 0.06 | 53.3 | 46.73 |
| True | True | False | False | risk1.0 | 9 | 1 | 8 | 11.1 | -53.27 | 0.06 | 53.3 | 46.73 |
| True | False | True | True | fixed | 22 | 6 | 16 | 27.3 | -53.62 | 0.34 | 53.6 | 46.38 |
| True | False | True | True | risk0.5 | 22 | 6 | 16 | 27.3 | -53.62 | 0.34 | 53.6 | 46.38 |
| True | False | True | True | risk1.0 | 22 | 6 | 16 | 27.3 | -53.62 | 0.34 | 53.6 | 46.38 |
| True | True | True | False | fixed | 7 | 0 | 7 | 0.0 | -55.07 | 0.00 | 55.1 | 44.93 |
| True | True | True | False | risk0.5 | 7 | 0 | 7 | 0.0 | -55.07 | 0.00 | 55.1 | 44.93 |
| True | True | True | False | risk1.0 | 7 | 0 | 7 | 0.0 | -55.07 | 0.00 | 55.1 | 44.93 |
| False | False | False | False | fixed | 8 | 0 | 8 | 0.0 | -55.52 | 0.00 | 55.5 | 44.48 |
| False | False | False | False | risk0.5 | 8 | 0 | 8 | 0.0 | -55.52 | 0.00 | 55.5 | 44.48 |
| False | False | False | False | risk1.0 | 8 | 0 | 8 | 0.0 | -55.52 | 0.00 | 55.5 | 44.48 |
| False | False | True | True | fixed | 10 | 1 | 9 | 10.0 | -58.31 | 0.01 | 58.3 | 41.69 |
| False | False | True | True | risk0.5 | 10 | 1 | 9 | 10.0 | -58.31 | 0.01 | 58.3 | 41.69 |
| False | False | True | True | risk1.0 | 10 | 1 | 9 | 10.0 | -58.31 | 0.01 | 58.3 | 41.69 |


## Sweep: 2026-09-14 21:26 — full entry/filter/sizing grid, August 2026 (31d, real XAUUSDm broker data)

Starting equity: $1000.00. TP1-partial-close bug fix applied (`fix_min_lot_tp1_bug=True`). 48 combinations tested.

| Midline brk | Trend-flip req | MACD filter | H4 trend filter | Sizing | Trades | Win | Loss | Win% | Net $ | PF | MaxDD% | End Eq |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| True | True | True | True | fixed | 16 | 2 | 14 | 12.5 | -86.41 | 0.25 | 10.4 | 913.59 |
| True | True | True | True | risk0.5 | 16 | 2 | 14 | 12.5 | -86.41 | 0.25 | 10.4 | 913.59 |
| True | True | True | True | risk1.0 | 16 | 2 | 14 | 12.5 | -86.41 | 0.25 | 10.4 | 913.59 |
| False | True | True | True | fixed | 17 | 2 | 15 | 11.8 | -90.90 | 0.25 | 10.8 | 909.10 |
| False | True | True | True | risk0.5 | 17 | 2 | 15 | 11.8 | -90.90 | 0.25 | 10.8 | 909.10 |
| False | True | True | True | risk1.0 | 17 | 2 | 15 | 11.8 | -90.90 | 0.25 | 10.8 | 909.10 |
| True | True | True | False | fixed | 27 | 2 | 25 | 7.4 | -174.39 | 0.14 | 17.4 | 825.61 |
| True | True | True | False | risk0.5 | 27 | 2 | 25 | 7.4 | -174.39 | 0.14 | 17.4 | 825.61 |
| True | True | True | False | risk1.0 | 27 | 2 | 25 | 7.4 | -174.39 | 0.14 | 17.4 | 825.61 |
| False | True | True | False | fixed | 30 | 2 | 28 | 6.7 | -190.70 | 0.13 | 19.1 | 809.30 |
| False | True | True | False | risk0.5 | 30 | 2 | 28 | 6.7 | -190.70 | 0.13 | 19.1 | 809.30 |
| False | True | True | False | risk1.0 | 30 | 2 | 28 | 6.7 | -190.70 | 0.13 | 19.1 | 809.30 |
| False | True | False | True | fixed | 46 | 9 | 37 | 19.6 | -221.32 | 0.27 | 23.3 | 778.68 |
| False | True | False | True | risk0.5 | 46 | 9 | 37 | 19.6 | -221.32 | 0.27 | 23.3 | 778.68 |
| False | True | False | True | risk1.0 | 46 | 9 | 37 | 19.6 | -221.32 | 0.27 | 23.3 | 778.68 |
| True | True | False | True | fixed | 43 | 7 | 36 | 16.3 | -227.88 | 0.24 | 24.0 | 772.12 |
| True | True | False | True | risk0.5 | 43 | 7 | 36 | 16.3 | -227.88 | 0.24 | 24.0 | 772.12 |
| True | True | False | True | risk1.0 | 43 | 7 | 36 | 16.3 | -227.88 | 0.24 | 24.0 | 772.12 |
| False | False | True | True | fixed | 78 | 14 | 64 | 17.9 | -395.71 | 0.23 | 39.6 | 604.29 |
| False | False | True | True | risk0.5 | 78 | 14 | 64 | 17.9 | -395.71 | 0.23 | 39.6 | 604.29 |
| False | False | True | True | risk1.0 | 78 | 14 | 64 | 17.9 | -395.71 | 0.23 | 39.6 | 604.29 |
| False | False | False | True | fixed | 105 | 21 | 84 | 20.0 | -495.08 | 0.26 | 51.9 | 504.92 |
| False | False | False | True | risk0.5 | 105 | 21 | 84 | 20.0 | -495.08 | 0.26 | 51.9 | 504.92 |
| False | False | False | True | risk1.0 | 105 | 21 | 84 | 20.0 | -495.08 | 0.26 | 51.9 | 504.92 |
| False | True | False | False | fixed | 90 | 14 | 76 | 15.6 | -507.33 | 0.19 | 51.9 | 492.67 |
| False | True | False | False | risk0.5 | 90 | 14 | 76 | 15.6 | -507.33 | 0.19 | 51.9 | 492.67 |
| False | True | False | False | risk1.0 | 90 | 14 | 76 | 15.6 | -507.33 | 0.19 | 51.9 | 492.67 |
| True | True | False | False | fixed | 86 | 12 | 74 | 14.0 | -507.54 | 0.17 | 51.9 | 492.46 |
| True | True | False | False | risk0.5 | 86 | 12 | 74 | 14.0 | -507.54 | 0.17 | 51.9 | 492.46 |
| True | True | False | False | risk1.0 | 86 | 12 | 74 | 14.0 | -507.54 | 0.17 | 51.9 | 492.46 |
| True | False | True | True | fixed | 224 | 58 | 166 | 25.9 | -627.79 | 0.48 | 62.8 | 372.21 |
| True | False | True | True | risk0.5 | 224 | 58 | 166 | 25.9 | -627.79 | 0.48 | 62.8 | 372.21 |
| True | False | True | True | risk1.0 | 224 | 58 | 166 | 25.9 | -627.79 | 0.48 | 62.8 | 372.21 |
| False | False | True | False | fixed | 124 | 17 | 107 | 13.7 | -725.68 | 0.15 | 72.6 | 274.32 |
| False | False | True | False | risk0.5 | 124 | 17 | 107 | 13.7 | -725.68 | 0.15 | 72.6 | 274.32 |
| False | False | True | False | risk1.0 | 124 | 17 | 107 | 13.7 | -725.68 | 0.15 | 72.6 | 274.32 |
| False | False | False | False | fixed | 169 | 25 | 144 | 14.8 | -948.54 | 0.17 | 94.9 | 51.46 |
| False | False | False | False | risk0.5 | 169 | 25 | 144 | 14.8 | -948.54 | 0.17 | 94.9 | 51.46 |
| False | False | False | False | risk1.0 | 169 | 25 | 144 | 14.8 | -948.54 | 0.17 | 94.9 | 51.46 |
| True | False | False | False | fixed | 394 | 104 | 290 | 26.4 | -954.36 | 0.53 | 95.4 | 45.64 |
| True | False | False | False | risk0.5 | 394 | 104 | 290 | 26.4 | -954.36 | 0.53 | 95.4 | 45.64 |
| True | False | False | False | risk1.0 | 394 | 104 | 290 | 26.4 | -954.36 | 0.53 | 95.4 | 45.64 |
| True | False | False | True | fixed | 339 | 84 | 255 | 24.8 | -954.91 | 0.49 | 95.5 | 45.09 |
| True | False | False | True | risk0.5 | 339 | 84 | 255 | 24.8 | -954.91 | 0.49 | 95.5 | 45.09 |
| True | False | False | True | risk1.0 | 339 | 84 | 255 | 24.8 | -954.91 | 0.49 | 95.5 | 45.09 |
| True | False | True | False | fixed | 317 | 80 | 237 | 25.2 | -966.98 | 0.43 | 96.7 | 33.02 |
| True | False | True | False | risk0.5 | 317 | 80 | 237 | 25.2 | -966.98 | 0.43 | 96.7 | 33.02 |
| True | False | True | False | risk1.0 | 317 | 80 | 237 | 25.2 | -966.98 | 0.43 | 96.7 | 33.02 |


## Test: 2026-09-14 21:27 — VALIDATED pullback entry (RSI extreme+reversal, EMA trend, H4 bias) + MGNFY GOLD exit machinery, August 2026 real XAUUSDm data, $100 start

Trades 0, Win 0, Loss 0, Win% 0.0, Net $0.00, PF inf, End Eq $100.00

## Test: 2026-09-14 21:28 — VALIDATED pullback entry (RSI extreme+reversal, EMA trend, H4 bias) + MGNFY GOLD exit machinery, August 2026 real XAUUSDm data, $100 start

Trades 6, Win 4, Loss 2, Win% 66.7, Net $17.41, PF 3.5340336702885113, End Eq $117.41

## Test: 2026-09-14 21:32 — pullback entry (M15 signal, M15 position mgmt) x H4/H1 bias, 2-YEAR real XAUUSDm M15 history (2024-09 to 2026-08), IS/OOS split, $100 start

| Window | Bias TF | Trades | Win | Loss | Win% | Net $ | PF | End Eq |
|---|---|---|---|---|---|---|---|---|
| IS (Sep24-Dec25) | 4h | 34 | 13 | 21 | 38.2 | -0.82 | 0.99 | 99.18 |
| OOS (Jan26-Aug26) | 4h | 12 | 4 | 8 | 33.3 | -41.22 | 0.55 | 58.78 |
| FULL (Sep24-Aug26) | 4h | 44 | 16 | 28 | 36.4 | -51.67 | 0.70 | 48.33 |
| IS (Sep24-Dec25) | 1h | 42 | 16 | 26 | 38.1 | -0.32 | 1.00 | 99.68 |
| OOS (Jan26-Aug26) | 1h | 12 | 4 | 8 | 33.3 | -60.16 | 0.35 | 39.84 |
| FULL (Sep24-Aug26) | 1h | 53 | 19 | 34 | 35.8 | -67.09 | 0.68 | 32.91 |

Note: position management here steps through M15 bars (not M1) — coarser than the June-Aug 2026 M1-precision test, since M1 history only exists back to ~June 2026 on this broker. Treat this as directionally informative, not a precise dollar figure.

## Finding: 2026-09-15 — Stairstep SL-lock (user's idea) vs flat breakeven, 2-year real data

User asked: instead of moving SL to flat breakeven after TP1, should SL jump
to TP1's price (and TP2's price after TP2) — a "staircase" lock? Tested
against the pullback strategy's full 2-year window (M15 signal+mgmt, H4
bias, 44-46 trades):

| Exit config | Trades | Win% | PF | Net $ |
|---|---|---|---|---|
| Baseline: flat BE after TP1, trail 1.0x | 44 | 36.4 | 0.70 | -51.67 |
| Stairstep lock, trail 1.0x | 46 | 41.3 | 0.86 | -29.18 |
| BE only, tight trail 0.5x | 46 | 34.8 | 0.79 | -34.97 |
| Stairstep + tight trail 0.5x (combined tightening) | 38 | 31.6 | 0.55 | -60.01 |
| **Stairstep + trail 1.5x (best found)** | 46 | 45.7 | **0.87** | **-28.62** |
| Stairstep + trail 2.0x | 46 | 45.7 | 0.83 | -40.27 |
| Stairstep + trail 2.5x/3.0x | 46 | 45.7 | 0.82 | -41.53 |

**Conclusion:** stairstep-lock (SL jumps to TP1/TP2 price once hit, not flat
breakeven) is a real, confirmed improvement — cuts the loss roughly in half
and lifts PF from 0.70 to 0.87. BUT stacking it with an aggressively
tighter ATR trail (0.5x) backfires badly — over-tightens, fewer trades,
worse PF (0.55) than doing nothing. Best combo found: stairstep lock +
trail_atr_mult=1.5 (slightly looser than the 1.0x default, giving winners
room beyond the stairstep floor). Still net negative overall — this is an
exit-mechanics improvement, not a fix for the underlying entry signal's
lack of edge (see the 2-year IS/OOS sweep above).

`Cfg(stairstep_lock=True, trail_atr_mult=1.5)` is now the best-known exit
config in this project. Entry signal still needs work.

## Finding: 2026-09-15 — Option A (stairstep, ride) vs Option B (full close at TP2, or ride if overshot), August 2026 real data

User's Option B: TP2 closes the ENTIRE remaining position immediately on a
"normal" touch; if price already overshot TP2 by more than a buffer when
noticed (fast move), don't force the close — lock SL at TP2 and ride
instead (same as Option A in that branch).

Tested with `tp2_overshoot_buffer_atr` swept 0.1 -> 2.0x ATR to find where
the "normal touch" branch actually fires (it rarely does — gold moves fast
enough on M1 that most TP2 touches are already past a 0.1-0.5x ATR buffer
by the time the bar is checked).

**Result: byte-identical net P&L/PF/win% between A and B at every buffer
setting tested**, including the 1-2 trades per run where B's hard-close
branch did fire. Reason (provable, not coincidence): Option A's
"lock SL at TP2, let trailing ride" is a strict superset of what a hard
close achieves — if price reverses immediately after TP2, the locked SL
never moves and gets hit at exactly TP2 (same $ as a hard close); if price
keeps running, trailing captures more. There's no scenario in this
(frictionless-stop) backtest where forcing an immediate close does better.

**Caveat noted for the record:** this only holds because the backtest
assumes perfect stop-loss execution (no slippage). In live trading, a
resting stop can fill worse than its price during a fast gap, while an
immediate close locks the price with certainty — a real risk this
simplified model can't see. For gold, which gaps on news, this isn't
purely theoretical, but as a systematic default, Option A remains the
better choice.

**Decision: Option A (stairstep lock, `tp2_full_close=False`) adopted as
the winner.** `tp2_full_close` code path kept in `backtest_mgnfy.py` for
reference but not used going forward.


## Journal batch: 2026-09-15 -- 6 random weeks x 3 timeframes x 3 configs (54 backtests, 566 total trades), plus a direct check of the user's 85% win-rate target

**Trigger:** user ran the live v1.11 EA (unpatched, currently compiled and
attached in MT5) through the GUI Strategy Tester, Aug 1 - Sep 14 2026,
M15 chart, real ticks, "Balance"-preset-equivalent inputs
(ATRMultiplier=2.0, StopLossPercent=0.7, MACD filter off -- confirmed by
matching the on-chart HUD parameter readout against `presets/MGNFY GOLD -
Balance.set`). Result: 304 trades, 36.2% win rate, PF 1.16, net +$204.55 on
a $100 deposit, 54.9% max equity drawdown. User asked for: (1) full
understanding of the EA, (2) a check on whether it'll "still perform well,"
(3) a batch of short (1-week), randomly-dated backtests across timeframe
combinations, (4) everything journaled in enough detail to hand to a
separate data-analysis skill later, and (5) explicitly asked whether the
EA can be tuned to an **85% win rate**.

**Method.** Extended `journal_runner.py` (new script, this session) on top
of the existing `backtest_mgnfy.py` offline engine. `random.SystemRandom`
picked 6 Monday-start weeks from the 12 candidate weeks that fully fit
inside this account's actual available M1 history (verified via the
MetaTrader5 Python API: M1 bars exist back to **2026-06-15** on this
broker/account; M15 back to 2022; M30/H1 much further) -- printed *before*
any backtest ran, so the selection can't have been cherry-picked:

```
2026-07-06 -> 2026-07-12
2026-07-13 -> 2026-07-19
2026-07-20 -> 2026-07-26
2026-08-10 -> 2026-08-16   (overlaps the user's Aug1-Sep14 GUI run)
2026-08-17 -> 2026-08-23   (overlaps the user's Aug1-Sep14 GUI run)
2026-09-07 -> 2026-09-13
```

Each week was tested on 3 **signal timeframes** (the EA's `InpTF` --
what chart it's attached to: M15, M30, H1) x 3 **configs**:

- `v1.11_baseline` -- exactly what's live/compiled in MT5 right now,
  including the real partial-close bug (see facts block at the top of this
  file): at 0.01 lot, TP1/TP2 partial closes silently fail, so the
  breakeven-move and TP2/TP3 chain effectively never fires on this size of
  account. `Trail_ATR_Mult=1.5` (matches the Balance preset, not the bare
  1.0 code default -- the user's GUI screenshot's own parameters confirm
  Balance was the preset in effect).
- `v1.12_fixed` -- this session's fix: bug patched, stairstep SL lock
  (SL jumps to TP1/TP2's own price instead of flat breakeven),
  `Trail_ATR_Mult=1.5`. Same entry logic as Balance otherwise.
- `v1.12_fixed_conservative` -- v1.12 fix applied to the **Conservative**
  preset's filters: MACD filter on, H4 EMA200 trend filter on, trend-flip
  required (not just a midline cross), risk-based sizing at 0.5%/trade.

Each run starts fresh at $100 (matching the user's own deposit), is
independent (no compounding across weeks -- see caveat below), and steps
execution through real M1 bars with a 5-day pre-week warmup (untraded) to
prime the ATR/regime-channel state. Every single trade from all 54 runs is
saved to `data/journal_trades/<run_id>.csv` (566 rows total, gitignored --
regenerate with `python journal_runner.py`); nothing is summarized away.
`journal_results_summary.csv` (one row per run) and `journal_all_trades.csv`
(all 566 trades, one file) are committed to the repo for a future
data-analysis pass.

**Caveats -- read before trusting these numbers over the user's GUI run:**
1. **Not compounding, not continuous.** Each of the 18 (week x TF) cells
   restarts at a fresh $100 -- so "Net $" summed across weeks is *not* a
   6-week equity curve the way the user's single continuous GUI backtest
   was. Max-drawdown % is measured against that isolated $100 too, which
   mechanically inflates it on a small sample versus a long continuous run
   that can offset a bad week with a good one. Treat per-run Net$/MaxDD%
   as informative about *that specific week*, not as a portfolio result.
2. **Entries skew hard to Monday/Tuesday** (175 and 97 of 566 trades) --
   this is very likely a **methodology artifact**, not a real weekday
   edge: the regime-channel trend state (`prevTrend`/`prevUp1`/`prevDn1`)
   resets to zero at the start of every isolated run, and the 5-day
   warmup before a Monday week-start lands the state-priming right at the
   week's open, which can trigger a burst of "first breakout since reset"
   signals early in the week. A continuous multi-month run (like the
   user's GUI test) would not have this artifact. Don't read "Monday has
   an edge" out of this table.
3. **Bar-close signal fidelity**, not true tick-by-tick -- see
   `backtest_mgnfy.py`'s own docstring notes 1-5. MT5's GUI tester in
   "every tick real" mode (what the user ran) is the authoritative
   fidelity level; this offline engine trades some of that precision for
   speed and scriptability.
4. Hours with n=1 or n=5 trades (22:00, 23:00, both showing 100% win rate
   in the pooled hour table below) are noise, not signal -- too few
   observations to mean anything.

### Full per-run results (54 runs)

Week | TF | Config | Trades | Wins | Win% | Net $ | PF | MaxDD% | MaxConsecLoss |
|---|---|---|---|---|---|---|---|---|---|
| 2026-07-06_to_2026-07-12 | M15 | v1.11_baseline | 12 | 1 | 8.3 | -60.32 | 0.26 | 60.3 | 8 |
| 2026-07-06_to_2026-07-12 | M15 | v1.12_fixed | 36 | 14 | 38.9 | -58.90 | 0.65 | 58.9 | 4 |
| 2026-07-06_to_2026-07-12 | M15 | v1.12_fixed_conservative | 4 | 2 | 50.0 | 2.93 | 1.14 | 18.4 | 1 |
| 2026-07-06_to_2026-07-12 | M30 | v1.11_baseline | 9 | 2 | 22.2 | -54.75 | 0.21 | 54.7 | 5 |
| 2026-07-06_to_2026-07-12 | M30 | v1.12_fixed | 10 | 2 | 20.0 | -55.18 | 0.30 | 55.2 | 6 |
| 2026-07-06_to_2026-07-12 | M30 | v1.12_fixed_conservative | 1 | 0 | 0.0 | -8.72 | 0.00 | 8.7 | 1 |
| 2026-07-06_to_2026-07-12 | H1 | v1.11_baseline | 7 | 1 | 14.3 | -63.64 | 0.22 | 69.2 | 6 |
| 2026-07-06_to_2026-07-12 | H1 | v1.12_fixed | 15 | 6 | 40.0 | -61.35 | 0.60 | 77.9 | 8 |
| 2026-07-06_to_2026-07-12 | H1 | v1.12_fixed_conservative | 0 | 0 | 0.0 | 0.00 | 0.00 | 0.0 | 0 |
| 2026-07-13_to_2026-07-19 | M15 | v1.11_baseline | 10 | 2 | 20.0 | -53.67 | 0.19 | 53.7 | 3 |
| 2026-07-13_to_2026-07-19 | M15 | v1.12_fixed | 12 | 3 | 25.0 | -58.32 | 0.32 | 58.3 | 3 |
| 2026-07-13_to_2026-07-19 | M15 | v1.12_fixed_conservative | 4 | 0 | 0.0 | -49.70 | 0.00 | 49.7 | 4 |
| 2026-07-13_to_2026-07-19 | M30 | v1.11_baseline | 31 | 10 | 32.3 | -5.65 | 0.97 | 64.1 | 9 |
| 2026-07-13_to_2026-07-19 | M30 | v1.12_fixed | 11 | 3 | 27.3 | -52.91 | 0.48 | 56.9 | 5 |
| 2026-07-13_to_2026-07-19 | M30 | v1.12_fixed_conservative | 0 | 0 | 0.0 | 0.00 | 0.00 | 0.0 | 0 |
| 2026-07-13_to_2026-07-19 | H1 | v1.11_baseline | 14 | 6 | 42.9 | 53.52 | 1.53 | 38.5 | 6 |
| 2026-07-13_to_2026-07-19 | H1 | v1.12_fixed | 6 | 1 | 16.7 | -67.03 | 0.21 | 67.8 | 4 |
| 2026-07-13_to_2026-07-19 | H1 | v1.12_fixed_conservative | 1 | 0 | 0.0 | -24.78 | 0.00 | 24.8 | 1 |
| 2026-07-20_to_2026-07-26 | M15 | v1.11_baseline | 8 | 0 | 0.0 | -53.64 | 0.00 | 53.6 | 8 |
| 2026-07-20_to_2026-07-26 | M15 | v1.12_fixed | 23 | 8 | 34.8 | -54.12 | 0.52 | 54.1 | 5 |
| 2026-07-20_to_2026-07-26 | M15 | v1.12_fixed_conservative | 3 | 0 | 0.0 | -29.60 | 0.00 | 29.6 | 3 |
| 2026-07-20_to_2026-07-26 | M30 | v1.11_baseline | 13 | 2 | 15.4 | -54.48 | 0.43 | 54.5 | 5 |
| 2026-07-20_to_2026-07-26 | M30 | v1.12_fixed | 26 | 10 | 38.5 | -61.31 | 0.63 | 68.6 | 7 |
| 2026-07-20_to_2026-07-26 | M30 | v1.12_fixed_conservative | 2 | 1 | 50.0 | 7.41 | 1.86 | 8.6 | 1 |
| 2026-07-20_to_2026-07-26 | H1 | v1.11_baseline | 3 | 0 | 0.0 | -53.37 | 0.00 | 53.4 | 3 |
| 2026-07-20_to_2026-07-26 | H1 | v1.12_fixed | 3 | 0 | 0.0 | -53.37 | 0.00 | 53.4 | 3 |
| 2026-07-20_to_2026-07-26 | H1 | v1.12_fixed_conservative | 0 | 0 | 0.0 | 0.00 | 0.00 | 0.0 | 0 |
| 2026-08-10_to_2026-08-16 | M15 | v1.11_baseline | 61 | 20 | 32.8 | -3.65 | 0.99 | 67.8 | 7 |
| 2026-08-10_to_2026-08-16 | M15 | v1.12_fixed | 44 | 19 | 43.2 | -52.79 | 0.75 | 68.3 | 7 |
| 2026-08-10_to_2026-08-16 | M15 | v1.12_fixed_conservative | 3 | 1 | 33.3 | -12.91 | 0.45 | 23.4 | 2 |
| 2026-08-10_to_2026-08-16 | M30 | v1.11_baseline | 15 | 4 | 26.7 | -56.02 | 0.52 | 66.0 | 5 |
| 2026-08-10_to_2026-08-16 | M30 | v1.12_fixed | 26 | 11 | 42.3 | -49.97 | 0.73 | 65.7 | 5 |
| 2026-08-10_to_2026-08-16 | M30 | v1.12_fixed_conservative | 3 | 2 | 66.7 | 19.88 | 2.43 | 11.8 | 1 |
| 2026-08-10_to_2026-08-16 | H1 | v1.11_baseline | 3 | 0 | 0.0 | -55.82 | 0.00 | 55.8 | 3 |
| 2026-08-10_to_2026-08-16 | H1 | v1.12_fixed | 3 | 0 | 0.0 | -55.82 | 0.00 | 55.8 | 3 |
| 2026-08-10_to_2026-08-16 | H1 | v1.12_fixed_conservative | 1 | 0 | 0.0 | -21.84 | 0.00 | 21.8 | 1 |
| 2026-08-17_to_2026-08-23 | M15 | v1.11_baseline | 9 | 1 | 11.1 | -53.08 | 0.05 | 53.1 | 5 |
| 2026-08-17_to_2026-08-23 | M15 | v1.12_fixed | 36 | 14 | 38.9 | -56.26 | 0.66 | 56.3 | 4 |
| 2026-08-17_to_2026-08-23 | M15 | v1.12_fixed_conservative | 5 | 1 | 20.0 | -41.49 | 0.17 | 41.5 | 2 |
| 2026-08-17_to_2026-08-23 | M30 | v1.11_baseline | 5 | 0 | 0.0 | -54.49 | 0.00 | 54.5 | 5 |
| 2026-08-17_to_2026-08-23 | M30 | v1.12_fixed | 5 | 0 | 0.0 | -54.49 | 0.00 | 54.5 | 5 |
| 2026-08-17_to_2026-08-23 | M30 | v1.12_fixed_conservative | 0 | 0 | 0.0 | 0.00 | 0.00 | 0.0 | 0 |
| 2026-08-17_to_2026-08-23 | H1 | v1.11_baseline | 4 | 0 | 0.0 | -52.61 | 0.00 | 52.6 | 4 |
| 2026-08-17_to_2026-08-23 | H1 | v1.12_fixed | 5 | 1 | 20.0 | -48.61 | 0.23 | 48.6 | 2 |
| 2026-08-17_to_2026-08-23 | H1 | v1.12_fixed_conservative | 2 | 0 | 0.0 | -53.79 | 0.00 | 53.8 | 2 |
| 2026-09-07_to_2026-09-13 | M15 | v1.11_baseline | 15 | 3 | 20.0 | -52.82 | 0.34 | 52.8 | 6 |
| 2026-09-07_to_2026-09-13 | M15 | v1.12_fixed | 9 | 1 | 11.1 | -55.77 | 0.13 | 55.8 | 6 |
| 2026-09-07_to_2026-09-13 | M15 | v1.12_fixed_conservative | 4 | 0 | 0.0 | -37.01 | 0.00 | 37.0 | 4 |
| 2026-09-07_to_2026-09-13 | M30 | v1.11_baseline | 4 | 0 | 0.0 | -48.81 | 0.00 | 48.8 | 4 |
| 2026-09-07_to_2026-09-13 | M30 | v1.12_fixed | 4 | 0 | 0.0 | -48.81 | 0.00 | 48.8 | 4 |
| 2026-09-07_to_2026-09-13 | M30 | v1.12_fixed_conservative | 0 | 0 | 0.0 | 0.00 | 0.00 | 0.0 | 0 |
| 2026-09-07_to_2026-09-13 | H1 | v1.11_baseline | 8 | 2 | 25.0 | -54.13 | 0.14 | 54.1 | 3 |
| 2026-09-07_to_2026-09-13 | H1 | v1.12_fixed | 28 | 15 | 53.6 | 34.07 | 1.14 | 48.5 | 3 |
| 2026-09-07_to_2026-09-13 | H1 | v1.12_fixed_conservative | 0 | 0 | 0.0 | 0.00 | 0.00 | 0.0 | 0 |

### Pooled by config (all 6 weeks x 3 TFs combined)

Config | Trades | Wins | Win% | Net $ (sum of 18 isolated $100 runs) | PF | AvgWin$ | AvgLoss$ |
|---|---|---|---|---|---|---|---|
| v1.11_baseline | 231 | 54 | 23.4 | -777.42 | 0.53 | 16.33 | -9.37 |
| v1.12_fixed | 302 | 108 | 35.8 | -910.92 | 0.57 | 10.99 | -10.81 |
| v1.12_fixed_conservative | 33 | 7 | 21.2 | -249.62 | 0.27 | 13.20 | -13.15 |

### Pooled by config x timeframe

Config | TF | Trades | Wins | Win% | Net $ | PF | AvgWin$ | AvgLoss$ |
|---|---|---|---|---|---|---|---|---|
| v1.11_baseline | H1 | 39 | 9 | 23.1 | -226.04 | 0.45 | 20.25 | -13.61 |
| v1.11_baseline | M15 | 115 | 27 | 23.5 | -277.18 | 0.57 | 13.82 | -7.39 |
| v1.11_baseline | M30 | 77 | 18 | 23.4 | -274.19 | 0.54 | 18.12 | -10.17 |
| v1.12_fixed | H1 | 60 | 23 | 38.3 | -252.10 | 0.62 | 17.62 | -17.77 |
| v1.12_fixed | M15 | 160 | 59 | 36.9 | -336.16 | 0.58 | 8.02 | -8.01 |
| v1.12_fixed | M30 | 82 | 26 | 31.7 | -322.66 | 0.49 | 11.86 | -11.27 |
| v1.12_fixed_conservative | H1 | 4 | 0 | 0.0 | -100.41 | 0.00 | 0.00 | -25.10 |
| v1.12_fixed_conservative | M15 | 23 | 4 | 17.4 | -167.78 | 0.20 | 10.65 | -11.07 |
| v1.12_fixed_conservative | M30 | 6 | 3 | 50.0 | 18.57 | 1.60 | 16.59 | -10.40 |

### Pooled entries by hour (server time) -- v1.12_fixed config only, all TFs/weeks

Hour (broker/server time) | Trades | Wins | Win% | Net $ |
|---|---|---|---|---|
| 00:00 | 36 | 7 | 19.4 | -194.40 |
| 01:00 | 27 | 9 | 33.3 | -126.99 |
| 02:00 | 22 | 12 | 54.5 | 49.99 |
| 03:00 | 15 | 6 | 40.0 | -43.44 |
| 04:00 | 8 | 5 | 62.5 | 16.30 |
| 05:00 | 15 | 7 | 46.7 | -12.52 |
| 06:00 | 15 | 5 | 33.3 | -46.42 |
| 07:00 | 15 | 3 | 20.0 | -96.46 |
| 08:00 | 16 | 7 | 43.8 | -14.14 |
| 09:00 | 13 | 6 | 46.2 | 7.52 |
| 10:00 | 9 | 4 | 44.4 | -0.56 |
| 11:00 | 8 | 3 | 37.5 | -19.13 |
| 12:00 | 20 | 7 | 35.0 | -76.68 |
| 13:00 | 12 | 1 | 8.3 | -117.50 |
| 14:00 | 17 | 4 | 23.5 | -119.43 |
| 15:00 | 14 | 5 | 35.7 | -40.61 |
| 16:00 | 10 | 3 | 30.0 | -61.30 |
| 17:00 | 5 | 2 | 40.0 | -3.65 |
| 18:00 | 9 | 3 | 33.3 | -17.09 |
| 19:00 | 6 | 3 | 50.0 | 12.20 |
| 20:00 | 4 | 0 | 0.0 | -51.11 |
| 22:00 | 1 | 1 | 100.0 | 6.02 |
| 23:00 | 5 | 5 | 100.0 | 38.49 |

### Pooled entries by weekday -- v1.12_fixed config only, all TFs/weeks

(See caveat #2 above before reading anything into this.)

Weekday | Trades | Wins | Win% | Net $ |
|---|---|---|---|---|
| Friday | 5 | 2 | 40.0 | -26.59 |
| Monday | 175 | 64 | 36.6 | -480.32 |
| Thursday | 7 | 3 | 42.9 | -25.09 |
| Tuesday | 97 | 35 | 36.1 | -225.95 |
| Wednesday | 18 | 4 | 22.2 | -152.98 |

### Reality check: can this EA reach an 85% win rate?

**No -- not without changing its fundamental architecture, and the numbers
above show why.** Across 566 trades spanning 6 independently-sampled weeks
(not just the user's one favorable Aug1-Sep14 window), win rate topped out
at **35.8%** pooled (`v1.12_fixed`), and the *single best* per-run result
in the whole batch was 66.7% on a 3-trade sample (`v1.12_fixed_conservative`,
M30, Aug10-16 -- too few trades to be a real rate, not a repeatable one).
The 2-year IS/OOS sweep earlier in this journal found the same ceiling from
a completely different angle (45.7% best-found, still net negative).

The mechanical reason is baked into the exit design, not tunable away:
- **TP1 sits at exactly 1R -- the same distance as the stop-loss.** For a
  breakout entry with no directional edge beyond roughly a coin flip
  (which is what a SuperTrend-style midline-cross signal is, absent a
  strong regime), price reaching a target the same distance as the stop
  before reaching the stop is close to a 50/50 proposition *before*
  accounting for spread, slippage, and the fact that breakouts fail (revert
  through the midline) more often than they follow through. That's the
  structural ceiling -- not a parameter you can nudge to 85%.
- **To engineer an 85% win rate you'd need TP1 far closer than the SL**
  (e.g. TP at 0.2-0.3R against a 1R stop) -- `sweep_winrate.py`, already in
  this repo, tested exactly this trade-off on the August data: tightening
  TP1 raises win rate but shrinks PF and net$ because each win is now worth
  a fraction of a loss. An 85%-win-rate version of this exit ladder would
  need roughly one loss to erase four-plus wins' worth of profit --
  survivable only with an entry signal so directionally accurate that this
  project's testing (2 years, multiple filter combinations, multiple
  timeframes) has found no evidence of. High win rate and this EA's
  "cut losses at 1R, ride winners to 3R" design are opposite goals by
  construction.
- **A genuinely high-win-rate system is a different EA, not a parameter
  set** -- small, frequent, high-probability targets against a wide stop
  (classic mean-reversion/scalping shape), which flips the risk profile:
  frequent small wins, rare-but-large losses when the mean-reversion
  premise fails (news spike, trend day). The README already notes a
  completely separate rewrite exists at
  `OneDrive\Desktop\MGNFY GOLD v2\` (H1/H4/D1 majority-vote bias, no
  partial TPs) -- that's a different product, not evaluated in this repo,
  and would need its own from-scratch validation before any win-rate claim.

**Recommendation:** treat 85% as off the table for this EA's design, and
target realistic, controllable levers instead:
- **Profit factor > 1.3-1.5 with win rate in the 35-45% range** is the
  honest target for a 1R/2R/3R trend system -- v1.12_fixed's pooled PF
  (0.57) and even the user's own favorable GUI run (1.16) are both below
  the 1.3+ that would be needed for genuine live-tradeable edge after
  real-world slippage/spread (which this offline engine already partially
  models, but the GUI "every tick" run is more trustworthy on that front).
- **The Conservative filter set (MACD + H4 trend + trend-flip-required)
  cuts trade count by ~85-95%** (566 -> 33 trades pooled) without reliably
  improving quality (pooled PF actually *dropped* to 0.27) -- in this
  sample, filtering harder mostly means "trade less of the same weak
  edge," not "trade only the good setups." That's a real finding, not
  intuition: don't assume adding filters is free money.
- **The entry signal itself is the bottleneck**, confirmed independently
  by this batch and the earlier 2-year IS/OOS sweep. Before chasing win
  rate, the highest-leverage next step is testing a genuinely different
  entry condition (e.g. the pullback-entry variant already explored
  earlier in this journal, which hit 66.7% win rate / PF 3.53 on a small
  August sample -- promising but not yet validated out-of-sample the way
  the regime-flip entry has been).

### What shipped this session

- **v1.12 deployed**: recompiled from the fixed source and installed as
  the live EA in MT5 (see CHANGELOG.md / README.md for the full diff vs
  v1.11). The min-lot partial-close bug is real and was live in production
  until this update -- anyone running this EA at 0.01 lot on a broker that
  requires XAUUSDm was silently never reaching TP2/TP3/the breakeven move.
- `backtest_mgnfy.py`'s hardcoded `D:\EA Robot\...` data path (stale from
  a prior machine) fixed to resolve relative to the repo, so the whole
  toolchain (this script, `sweep_winrate.py`, `sweep_full.py`) runs from
  any checkout again.
- `journal_runner.py` (new): the reusable multi-week x multi-TF x
  multi-config batch runner used for this entry. Re-run any time with
  `FIXED_WEEKS = []` at the top to draw a fresh random sample.
