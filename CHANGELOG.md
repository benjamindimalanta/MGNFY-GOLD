# Changelog

All notable changes to MGNFY GOLD will be logged here from now on.

## [1.13] - 2026-09-15
Full HUD rewrite, requested after the user found the previous panel "ugly
and not very informative" and pointed out its Entry/SL/TP price lines
could visually cut through it.

- **Tabbed panel**: STATS and RISK CALCULATOR tabs (click to switch)
  instead of one static block.
- **Stats tab** now surfaces balance, equity, floating P/L, realized P/L,
  win rate, win/loss counts, profit factor, max drawdown, and the current
  open position's direction/entry/SL/TP1-TP2 status — profit factor and
  max drawdown didn't exist anywhere in the EA before this.
- **Risk Calculator tab** (new): editable entry price / lot size / TP
  price / SL price; computes real $ gain at TP and $ loss at SL via the
  broker's own `OrderCalcProfit()` (not hand-rolled pip math), plus the
  resulting risk:reward ratio.
- **Root cause of "blocked by the chart" fixed**: every HUD object now
  gets an explicit z-order above the EA's own Entry/SL/TP price lines
  (`OBJ_HLINE`, price-anchored, span the full chart width) — at whatever
  y-pixel those lines land on screen they could previously render on top
  of the panel and cut through it. Not a color/transparency issue.
- Dark, high-contrast, gold-accent theme, replacing a plain white panel
  that didn't match the file's own long-standing "dark-themed HUD"
  description.
- **Bugfix, found while testing the above**: `DrawLine()` (draws the
  Entry/SL/TP1/TP2/TP3 lines on chart) suffixed every object's name with
  the current bar's timestamp, so it created a brand-new HLINE object
  every single bar a trade stayed open instead of ever matching an
  existing one to move — one full set of lines per bar, unbounded,
  never cleaned up (the existing cleanup function's condition only
  handled `InpVisualKeepBars <= 1` and silently did nothing otherwise;
  the shipped default reads 1, but at least one preset/test config in
  the field was running with a different value, e.g. 2, which disabled
  cleanup entirely). Visible as a wall of stacked green TP lines and real
  lag once a trend trade rode across many bars — reported by the user
  running Tester visual mode. Fixed: each line is now one persistent
  object, moved in place every update; `CleanupOldVisuals()` now just
  clears the trade lines once flat instead of sweeping by bar age.
  `InpVisualKeepBars` is unused as of this fix (kept only so old presets
  referencing it still load without error).
- **Startup sweep**: `OnInit()` now deletes any leftover Entry/SL/TP/Cloud
  line objects by name prefix, so charts that already carry hundreds of
  old `TP1_<bartime>` objects from earlier builds get cleaned on attach.
  `OnDeinit()` logs the remaining horizontal-line count as a check — the
  verification run below logged `0`.
- **Trailing stop no longer spams the broker**: the ATR trail sent a
  modify request on nearly every tick for sub-cent moves. `MoveSLto()` now
  skips changes smaller than 500 points (0.50 on XAUUSDm). Measured over
  the same simulated window (2026-09-07 00:00 to 09-08 06:30, H1, real
  ticks): **2,756 modify requests before, 232 after.** Stairstep/BE moves
  are far larger than the threshold and unaffected. Trailing now moves in
  coarser steps, so backtest numbers can shift slightly — rerun the
  journal before comparing against earlier batches.
- **HUD background/font bug**: the panel helpers wrapped the
  background-color call in `#ifdef OBJPROP_BGCOLOR` (inherited from the
  original code). That's an enum value, not a macro, so the line was
  always compiled out — panels stayed on MT5's default light background
  and the light-gray text was nearly unreadable. Same issue with
  `#ifdef OBJPROP_BOLD` (MQL5 has no such property). Both removed; bold
  now comes from the font face.
- Shortened the HUD `#property description` (compiler warning 47:
  description too long). Builds with 0 errors, 0 warnings.
- **HUD blinking fixed** (reported by the user): `EnsureHUD()` rebuilt the
  whole layout on every tick, resetting each value label to `""` — which
  MT5 renders as the placeholder text `Label` — before the update wrote
  the real value back, and re-applied tab colors/visibility each time. A
  tester-window capture caught every value reading "Label". Now the
  layout builds once (rebuilds only if the panel objects are removed),
  and empty labels are written as a space so they never show the
  placeholder. Verified with four HUD captures 0.5s apart mid-trade.
- **Evidence the v1.12 take-profit fix works in real MT5**: in the
  verification run (XAUUSDm, 2026-09-07 to 09-11, real ticks, user's
  inputs), 7 of 57 trades closed with an empty exit comment — the
  signature of the TP3 `PositionClose()` — all winners at +1.3R to +3.3R.
  The v1.11 journal batch recorded zero TP exits in 481 trades. Note the
  R spread: TP1-TP3 are recomputed from the *current* bar's ATR on every
  tick rather than fixed at entry, so the TP3 distance drifts while a
  trade is open — worth a deliberate decision before tuning exits.
- Verified by compiling with MetaEditor and running Strategy Tester visual
  mode directly (2026-09-07 to 09-11, XAUUSDm H1, the user's exact inputs),
  with screenshots, rather than inferring from code alone.

## [1.12] - 2026-09-15
Backtested against 2 years of real XAUUSDm broker data before shipping —
full trace of every test in `JOURNAL.md`.

- **Bugfix:** at min lot size (0.01), a 33% partial close rounds to 0.00
  and `ClosePartial()` silently fails. `tp1Hit`/`tp2Hit` previously never
  became `true` in that case, so breakeven-move and TP2/TP3 never fired —
  the entire partial-TP ladder was dead code on small accounts. Now the
  level always counts as reached once price gets there, regardless of
  whether a partial close was physically possible.
- **Stairstep stop lock** replaces flat breakeven: SL now moves to TP1's
  own price after TP1 (not flat entry), and to TP2's price after TP2.
  Tested: profit factor 0.70 -> 0.87 vs the old flat-BE behavior on 2
  years of real data, because a pullback after TP1 now exits with real
  profit locked in instead of breakeven.
- `InpTrail_ATR_Mult` default raised 1.0 -> 1.5 — tested as the best
  pairing with the stairstep lock (a tighter trail combined with
  stairstep cuts winners short; looser values beyond 1.5 also underperform).
- All 5 presets: fixed `InpSymbol` from `XAUUSD` to `XAUUSDm` — the plain
  `XAUUSD` symbol doesn't exist on this account type, which silently
  failed `OnInit()` (indicator handles couldn't be created) and refused
  to run at all. This affects any Exness account using `m`-suffixed
  symbols; adjust back to `XAUUSD` if your broker uses that naming.

## [1.11] - 2025-11-03 (baseline)
Source recovered from an unversioned OneDrive folder and committed to this
repo for the first time on 2026-09-14. Treated as the baseline — no earlier
history is known or recorded.

Feature set at this baseline (see README.md for full detail):
- ATR regime channel (SuperTrend-style) with midline or band breakout entries
- Optional MACD filter, higher-timeframe EMA trend filter (default on: H4 EMA200)
- ATR-based or percent-based stop-loss
- 1R/2R/3R partial take-profit ladder with breakeven-after-TP1
- Optional ATR trailing stop
- Small-account profit capture mode (<= $300 equity)
- Margin, spread, and session filters
- On-chart HUD with realized/floating P/L, win rate, drawdown
- 5 presets: Conservative, Balance, Balance FIXED, Active, TEST Trading
