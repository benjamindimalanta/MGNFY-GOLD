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
