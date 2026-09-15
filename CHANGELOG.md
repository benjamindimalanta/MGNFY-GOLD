# Changelog

All notable changes to MGNFY GOLD will be logged here from now on.

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
