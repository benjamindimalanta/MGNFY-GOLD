# Changelog

All notable changes to MGNFY GOLD will be logged here from now on.

## [1.20] - 2026-09-17
The user's decisions after reading the round-4 report. No change to entries, sizing or exits.

- **`InpSkipWeekdays` back to "" (Fridays are traded again).** Shown the holdout evidence -- the six
  Friday trades made +$173.70, about 42% of the holdout's +$408.78, and the in-sample skip test had
  failed and was circular -- the user chose the evidence over the preference. Set it to "5" to turn
  Fridays off again.
- **The equity guard is confirmed, not assumed.** The user's "10% per week (moving)" rule means:
  pause new entries while equity is 10% or more below its highest value of the last 7 days, and
  resume once back inside or when that peak ages out. That is what `InpUseEquityGuard` /
  `InpEquityGuardPct=10` / `InpEquityGuardDays=7` already did; the wording is now recorded in the
  source and here. It has still never fired in any test.
- **The shock pause stays off** during forward observation, so demo results stay comparable with the
  tested build.
- **Two HUD status lines were overflowing the 300 px panel and were cut off mid-sentence** -- the
  round-4 report flagged that they had been verified by log and code path, not visually. A $100
  visual run showed `... 0.01 lot risks 7.2% (cap 1.5` with the rest missing. Both lines are now
  short enough to fit at 9 pt (`Skipped 06:05 SELL 4402.99: risk 4.7%, needs ~$310`,
  `Market: normal 1.03x   Entries: on`); the full sentence, with the cap and the stop distance, is
  still printed to the Experts log on every refusal (410 such lines in a $100 week).
- **`InpUseContext` now defaults to true (measurement only).** Without it the HUD could only say
  "Market: not measured", which is useless for the thing the user asked for -- knowing whether the
  week is normal. Verified it does not touch trading: the Aug 10 week produced 6 identical trades
  with identical entry times and +$55.74 either way. The features that *do* change trading
  (`InpUseRegimeFilter`, `InpUseShockPause`) remain off.
- Verified visually this time: HUD screenshot from a $100 visual run, `ini_runs/hudcheck_v120_100usd.ini`.
  Note for future configs: MT5 fills inputs **absent from a .ini with the tester's last used values**,
  not with the EA's defaults -- the first check silently ran in breakout mode until `InpEntryMode` was
  stated explicitly.

## [1.19] - 2026-09-16
Small-account visibility and the user's Friday rule, review round 4
(`reviews/2026-09-16-pro-trader-review-round4.md`). No change to how trades are selected or sized.

- **`InpSkipWeekdays` now defaults to "5" (no new entries on Fridays).** This is the **user's own
  preference, not a validated edge**: the in-sample test failed (avg +0.478R against the +0.482R
  required) and was circular anyway (every surviving trade was identical, so the "gain" was only the
  removal of trades that had lost in those same weeks), and on the holdout the Friday trades **made**
  money (+$173.70 over 6 trades). Set it to "" to trade every day. Verified: on two in-sample weeks
  it removes exactly the Friday entries and leaves every other trade identical.
- **A setup refused by the risk cap is now explained instead of silently dropped.** The log prints one
  line per refusal -- what was found, the risk the minimum lot would cost, and the balance the setup
  needs: `Swing: setup skipped -- SELL at 3993.112, 0.01 lot would risk 17.2% of $100.00 (cap 1.5%,
  stop 17.23); this setup needs about $1149 balance`. Verified on a $100 tester week: 0 trades, 4
  explanatory lines, balances needed $530-$1,149.
- **The HUD's SYSTEM block gained two lines** (panel 460 -> 500 px): the market state (normal /
  compressed / expanded with the ATR(D1) ratio) together with why entries are off (equity guard,
  shock cooldown or the weekday rule), and the last setup the cap refused. Built once and updated in
  place, as the rest of the HUD is.
- Holdout result (the last untouched data, Jan 5 - Feb 27, $5,000 weeks, 1% risk): **v1.18/v1.19
  defaults made 41 trades, +$408.78, PF 1.41, +8.22R, 5 of 8 weeks positive, worst weekly drawdown
  3.90%** -- the first out-of-sample read of this strategy, positive but on a small sample. The
  user's chosen candidate, the regime filter at half size on abnormal days, **failed** its
  pre-registered criteria: drawdown fell to 2.20% but net dropped to $133.81 (33% of the baseline,
  where 60% was required), because on those weeks the abnormal days were where the profit was. It
  stays off by default.

## [1.18] - 2026-09-16
Market context, review round 3 (`reviews/2026-09-16-pro-trader-review-round3.md`).

- **`InpTrailATRTF` now defaults to M30.** The round-2 candidate was run once on the untouched
  validation weeks (Mar 2 - May 22, $5,000, 1% risk) against the old default and met all three
  pre-registered criteria: paired +0.190R per trade (needed > 0 and >= half the in-sample +0.179R),
  total +29.74R vs +17.80R, +$1,362.66 vs +$861.88. Caveat kept on the record: 26 of 57 paired
  trades were worse and only 10 better, t = 1.26, better in 6 of 12 weeks -- the gain comes from a
  few large winners.
- **New market-context features, all off by default and measured from history at runtime** (no
  hardcoded tables):
  - `InpUseContext` / `InpContextDays`: median M5 range, tick volume and spread for every weekday
    and hour, rebuilt daily from the last 30 days.
  - `InpUseRegimeFilter` with `InpRegimeMinRatio` / `InpRegimeMaxRatio` / `InpRegimeRiskFactor`:
    today's ATR(D1) against its own 20-day median; outside the band the EA either skips the trade
    or trades it at a fraction of normal risk.
  - `InpUseShockPause` with `InpShockRangeMult` / `InpShockVolMult` / `InpShockSpreadMult` /
    `InpShockCooldownMin`: an M5 bar far outside what that hour normally does (or a spread spike)
    pauses new entries. This is the backtestable answer to the news question, since the Strategy
    Tester has no economic calendar.
  - `InpSkipWeekdays`: no new entries on the listed weekdays (server time).
- Verified in the tester with forced settings (Jun 22 week): the shock pause at 3x took 4 of the 5
  trades instead of 5; a regime band of 1.00-1.05 skipped every setup (no trades at all); a regime
  risk factor of 0.5 halved the lots (0.01-0.03 against 0.02-0.06, risk $17-24 against $34-48).
  With defaults unchanged, v1.18 reproduces the round-2 trades exactly on the checked weeks.
- **Nothing else became a default.** On the 12 in-sample weeks the two filters the diagnosis
  supported both missed their pre-registered bars: no Friday entries 46 trades +22.00R (needed
  avg >= +0.482R, got +0.478R) and no 00:00-06:00 UTC entries 41 trades +21.43R (needed total
  >= +21.92R), against a baseline of 57 trades and +18.92R. In both cases every surviving trade is
  identical to the baseline, so the gain is only the removal of trades that were negative in those
  same weeks.
- Tooling: `mt5_mode_compare.py` writes string inputs plainly when an override is marked
  `Name=str:value` (the optimization suffix was reaching the EA as part of the string).

## [1.17] - 2026-09-15
User-approved defaults and exit/session experiments, review round 2
(`reviews/2026-09-15-pro-trader-review-round2.md`). The new defaults are risk controls, not a
claim of edge.

- **Default entry mode is now swing pullback** (`InpEntryMode`), **with the M5 confirmation
  entry** (`InpSwingEntryStyle`; round 1: +0.02R vs -0.23R per trade for limit orders on the same
  weeks, neither proven).
- **Risk sizing on by default at 1%** (`InpUseRiskSizing=true`, `InpRiskPercent=1.0`). The lot is
  floored to the 0.01 step, so risk stays at or below 1%, except when it has to be raised to the
  0.01 minimum lot: then the trade is skipped if that lot would risk more than the new
  `InpMaxRiskPercent` (default 1.5%). Applies to both entry modes.
- **Equity guard** (`InpUseEquityGuard=true`, `InpEquityGuardPct=10`, `InpEquityGuardDays=7`): no
  new entries while equity is 10% or more below its highest value of the last 7 days (hourly
  buckets, rebuilt from deal history on restart). Pending orders are cancelled and armed levels
  dropped while it is active; open trades keep their stops; entries resume once equity is back
  inside the limit or the old peak leaves the window. Its log is limited to one line per minute
  (with a trade open, equity can cross the limit tick after tick: 152 lines in one test week
  before, 14 after, same trades). Verified in the tester with a 1% / 1-day setting: paused, skipped
  46 hourly checks, resumed when the peak aged out. The 1.5% cap was verified at $500 (5 of 5
  setups skipped with a log line each).
- **No stop modifications while the market is closed** (`InpThrottleClosedMarket=true`): skipped
  outside the symbol's trade sessions, plus a 60-second pause after a "market closed" rejection.
  Jan 5-7 2026 run (breakout, the user's inputs): 7,811 rejected requests before, 0 after; the 28
  trades and the final balance ($581.63) are identical.
- New inputs, off by default: `InpExitAtTP1` (what the stop does at TP1/TP2: TP1 price as before,
  breakeven + spread, or an M15 structure trail), `InpTrailATRTF` (ATR trailing timeframe),
  `InpUseTradeWindows` / `InpTradeWindows` (entries only inside server-time windows; default text is
  the user's hours, 06:00-10:00, 11:00-13:00, 15:00-17:00 UTC).
- With v1.16-equivalent inputs, v1.17 reproduces the stored v1.15 trades exactly (Jul 6, both
  modes).
- Tools: `mt5_deep_parse.py` groups partial closes into one trade, computes R at the traded
  volume (identical output on 0.01-lot reports) and reads numbers with thousand separators
  ("5 080.46" used to become NaN) and handles reports with no trades; `mt5_mode_compare.py`
  takes `DEPOSIT=`.
- Tested on the 12 in-sample weeks at $5,000 and 1% risk (JOURNAL.md): new defaults (B2) 56
  trades, +3.37R, +$115.35, PF 1.09, worst week -4.0%. Exits: breakeven at TP1 +2.62R (no
  effect); M15 structure trail +19.27R and ATR trail on M30 +18.92R, but both from two or three
  trending weeks and worse in most weeks (paired t 0.63 and 1.12), so not proven. User's trade
  windows +0.97R on 27 trades (the removed trades were the better ones). None became a default.

## [1.16] - 2026-09-15
Pro trader review, round 1 (`reviews/2026-09-15-pro-trader-review.md`). Default inputs keep
v1.15 trading behavior.

- **Bugfix, hedging accounts:** `MoveSLto()` (trailing stop and stairstep lock) selected the
  position with `PositionSelect(symbol)`, which on a hedging account returns the lowest-ticket
  position of the symbol -- a manual trade if one was opened first -- and applied that
  position's type and TP to the EA's own position. Tester proof with a harness that opens a
  manual SELL before the EA trades (Jun 23-24 2026): every EA SELL (22 positions) got the
  manual trade's TP copied onto it, about 4,300 stop modifications were sent in 2 days because
  the 500-point step guard compared against the manual stop, and 13 were rejected as invalid
  stops. The manual position itself was never modified or closed. It now selects the EA's own
  position by symbol and magic number and modifies it by ticket.
- New input `InpBreakoutClosedBar` (default false): breakout mode evaluates the regime channel,
  midline/band cross and trend flip on closed bars, with the channel rebuilt from the last 300
  closed bars each bar. Default false keeps the v1.15 signal (first tick of the new bar vs the
  previous close).
- New inputs `InpSwingEntryStyle` (default: limit order at the swing, as v1.15) and
  `InpSwingSweepMaxATR` (default 1.0): optional confirmation entry for swing mode -- watch the
  swing level, and after price sweeps it, enter on the first M5 close back on the bias side
  with the stop beyond the sweep; drop the setup if the sweep runs more than 1.0 x ATR(M30).
- `swing_log_summary.py` also reports the confirmation-entry flow (armed, sweeps, entries,
  disarm reasons).
- Tested (real ticks, $500, user's inputs, 12 in-sample weeks Jun 22 - Sep 11; JOURNAL.md):
  default inputs reproduce v1.15 trades exactly (4 of 4 week/mode runs). Confirmation entry:
  56 trades, PF 1.01, +$2.30 (v1.15 swing: 77, PF 0.72, -$55.80); fast stop-outs fell from 55%
  to 11% of losers, but no edge. Closed-bar regime flip: 124 trades, PF 1.01, +$6.88, weekly
  drawdown 12.3% (v1.15 breakout: 943, PF 0.93, -$300.18, 50%). Neither passed the promotion
  criteria, so both stay off by default and neither is a recommended setting.

## [1.15] - 2026-09-15
Swing-mode order handling, requested by the user after the v1.14 comparison.

- Pending orders are kept across hourly bias checks. One is cancelled only when
  the bias flips to the opposite direction, the swing level for the same
  direction changes, or price moves more than `InpSwingMaxDistATR` x ATR(M30)
  away from it. New input `InpSwingCancelOnWait` (default off) also cancels it
  when the bias turns neutral.
- New input `InpSwingMaxDistATR` (default 3.0): new orders only use swings within
  that distance of price. Set from data: in the v1.14 runs, orders placed 3+ ATR
  from price filled 0 of 49 times, versus 45-60% under 1 ATR.
- Stop buffer left at 0.3 x ATR after studying the v1.14 trades (JOURNAL.md).
  Replaying the orders on real M1 prices, every wider buffer lost more money
  (0.3: +$38.61 over 25 trades; 0.5: -$10.94; 1.0: -$89.51): win rate barely
  rose while each loss grew in proportion.
- Swing mode logs kept orders and cancel reasons; `swing_log_summary.py` reports
  them per run.
- Tested on all 12 weeks with tick data (Jun 22 - Sep 11, $500, real ticks; see
  JOURNAL.md): swing v1.15 made 77 trades, PF 0.72, -$55.80, 4 of 12 weeks
  positive, worst weekly drawdown 4.8%; breakout mode on the same weeks made 943
  trades, PF 0.93, -$300.18, 6 of 12 positive, worst weekly drawdown 50%. The
  new order handling works (fill rate 12% -> 38.5%), but swing mode still loses:
  34 of its 62 losing trades were stopped within 5 minutes of filling.

## [1.14] - 2026-09-15
Optional swing-pullback entry mode, built from the user's manual trading method.

- New input `InpEntryMode`: `ENTRY_REGIME_BREAKOUT` (default, behavior unchanged)
  or `ENTRY_SWING_PULLBACK`.
- Swing mode bias, per timeframe on M30/H1/H4: last close vs an EMA
  (`InpBiasEMALength`, default 50) sloping the same way, plus higher highs and
  higher lows (or lower highs and lower lows). `InpBiasMinAgree` (default 2)
  timeframes must agree.
- Re-checked at every new H1 bar: any unfilled pending order is cancelled, then
  a limit order is placed at the latest `InpSwingTF` (default M30) swing low for
  a buy or swing high for a sell. SL = swing -/+ `InpSwingSLBufferATR` x ATR
  (default 0.3); TP1 = the opposite swing; TP2/TP3 from the stored risk
  distance; skipped if TP1 < `InpSwingMinRR` x risk. Uses the existing margin,
  spread and session filters; ignores the breakout and trend-filter inputs.
- HUD open-position section shows the per-timeframe bias and the pending order
  while flat.
- Tested against breakout mode on the same 4 weeks with $500 (see JOURNAL.md):
  1 trade/day vs 15.8 and max drawdown 0.7-3.4% vs 17.8-27.9%, but only 20
  trades -- too few to judge. The stop is too tight (median loser stopped in
  7 min) and 87% of limit orders were cancelled unfilled. Not yet a
  recommended live setting.

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
- **Lines drawn across the HUD — first attempt was wrong, now fixed**: the
  original change set a high `OBJPROP_ZORDER` on HUD objects and claimed that
  kept them above the Entry/SL/TP lines. It doesn't: in MQL5 `OBJPROP_ZORDER`
  is click-event priority only. MT5 draws foreground objects in creation
  order, and the lines are created after the HUD, so they still cut across
  it (user screenshot, M5 tester run). Fixed by drawing the EA's lines in the
  background layer (`OBJPROP_BACK=true`): behind candles and behind the HUD.
- **HUD cut off in tester visual mode**: the tester auto-added the EA's ATR,
  MACD and EMA indicators, and their sub-windows shrank the main chart below
  the panel's height. `OnInit()` now calls `TesterHideIndicators(true)` before
  creating indicator handles. Tester-only; no effect on live charts.
- **MT5's own trade markers drawn over the HUD**: the terminal draws buy/sell
  arrows and dotted entry-to-exit lines for every deal as chart objects
  (names starting with `#`). They're created after the HUD, so full-resolution
  tester captures showed them on top of its title and tabs. The EA now moves
  those objects to the background layer whenever the chart's object count
  changes: still visible on the chart, behind the panel.
  Verified on the user's M5 inputs (2026-08-31 to 09-05, visual mode): the
  EA's exit log counted 621 terminal trade markers, 0 still in the
  foreground, and 0 leftover Entry/SL/TP lines; captures show a clean panel.
- **Market session on the HUD** (requested by the user): a session line under
  the title shows Asia (Tokyo), London, New York, the London + New York
  overlap, the daily gold break, or weekend close, plus a countdown to the
  next open/close. Computed in UTC with UK and US daylight-saving rules.
  Live it uses the PC clock via `TimeGMT()`; in the Strategy Tester
  `TimeGMT()` equals simulated server time, which is UTC on Exness (a broker
  with a non-UTC server clock would show shifted sessions in the tester).
  Verified in visual mode: "London + New York overlap / London closes in
  3h 23m" and "Asia (Sydney), quiet / Tokyo opens in 0h 09m" match
  September UTC session times.
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
