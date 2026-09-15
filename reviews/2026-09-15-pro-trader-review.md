# MGNFY GOLD -- Pro Trader Validation Report

- **Date:** 2026-09-15
- **EA build:** v1.16 (v1.15 trading logic plus a hedging-account bugfix and new inputs whose
  defaults keep v1.15 behavior)
- **Data:** MT5 Strategy Tester, every tick based on real ticks (`Model=4`), XAUUSDm (Exness
  demo, hedging, 1:100), $500 at the start of each week, fixed 0.01 lot, the user's own tester
  inputs (`ini_runs/visualcheck_H1_20260907.ini`: H1 chart, `InpTF`=M15, H1 EMA200 trend
  filter, SL 1.0 x ATR, TP 1R/2R/3R, stairstep lock, trail 1.5 x ATR)
- **In-sample:** 12 full weeks Jun 22 - Sep 11, 2026
- **Validation:** 12 weeks Mar 2 - May 22, 2026
- **Holdout (Jan 5 - Feb 27, 2026):** **fresh** -- not run, because no candidate passed in-sample. (Only a 2-day data-availability
  run on Jan 5-7 touched it earlier today.) Validation weeks also unused.
- **Lot / risk model:** fixed 0.01 lot (1.00 price move = $1.00), no risk-based sizing

## Verdict

**No edge found yet -- not ready for live.** Over the 12 in-sample weeks the current default
(breakout) made 943 trades, PF 0.93, -$300.18, 6 of 12 weeks positive, worst weekly drawdown
50%; swing mode made 77 trades, PF 0.72, -$55.80, 4 of 12 positive, worst week 4.8%. The code
audit found the reason for each loss: breakout entries are a coin flip on the first tick of each
M15 bar, so the mode pays the spread (~$245) for nothing, and swing limit orders fill while price
runs through the swing (55% of losers stopped within 5 minutes). Two targeted fixes, tested in
the real tester, removed the losses but did not create an edge: a closed-bar regime flip (124
trades, PF 1.01, +$6.88, worst week 12.3%, 7 of 12 positive) and a sweep-and-reclaim
confirmation entry for swing mode (56 trades, PF 1.01, +$2.30, worst week 5.3%, 5 of 12
positive). Both fail the pre-registered bar (PF >= 1.25, better than baseline in 8 of 12 weeks),
so validation and holdout were not run and remain fresh. A third idea (only take flips that agree
with the M30/H1/H4 bias) was screened on the logged in-sample data and showed nothing (23 trades,
PF 1.05), so it was not run. One real bug was found and fixed: on a hedging account a manual gold
trade made the EA copy its TP onto the EA's positions and flood the server with stop changes.

## What the robot actually does

**Breakout mode (default, `InpEntryMode=0`).** At the first tick of every new M15 bar it
compares that tick with the previous bar's close. The "midline" it is supposed to cross is the
forming bar's high/low midpoint, which at that tick equals the previous close in 100% of 54,492
logged evaluations. So "midline breakout" means: first tick above the previous close = buy,
below = sell (a signal on 84% of bars). The H1 EMA200 filter picks the side (buys only above
it, sells only below), one position at a time. Stop = 1.0 x ATR(M15) from entry (average
$8.62 at 0.01 lot, max $27.17). Targets 1R/2R/3R are recomputed from the current ATR on every
tick. When price touches TP1 the stop is moved to the TP1 price itself, i.e. right next to the
market; at 0.01 lot no partial close is possible, so in practice the trade exits at about +1R
on the next tick back unless price keeps running. A 1.5 x ATR(M15) trailing stop runs in
parallel; TP3 closes the rest. After a stop-out it re-enters at the next M15 bar (52% of
re-entries within 15 minutes). Net effect: always in the market in the H1 EMA200 direction,
re-entering on coin-flip timing, about 16 trades a day.

**Swing-pullback mode (`InpEntryMode=1`).** Every hour: bias per timeframe on M30, H1 and H4 =
last closed bar vs a rising/falling EMA50 plus the last two fractal swings making higher highs
and higher lows (or the bearish mirror); 2 of 3 must agree (WAIT 68% of the time). While flat,
a limit order sits exactly at the latest M30 swing low (buy) or high (sell) within 3 x ATR(M30)
of price, stop 0.3 x ATR(M30) beyond it (average $3.49), TP1 at the opposite swing. The order is
kept until the bias flips, the swing level changes or price moves 3 ATR away. It fills whenever
price reaches the level, at any hour, including a push straight through it. Management after
the fill is the same as breakout mode (stairstep lock, ATR(M15) trailing).

**Neither mode uses:** session or weekday windows (the session filter is off), news, a
confirmation of the reaction at the level, or position sizing from the stop.

## Findings, ranked by money impact

| # | Finding | Evidence | $ impact | Confidence | Severity |
|---|---|---|---|---|---|
| 1 | **Breakout entries are random timing; the loss is the spread.** | 943 trades, PF 0.93, -$300.18, win 34.4%. Spread at 0.26 x 943 = ~$245, so before spread the mode made about -$55, i.e. ~0.00R per trade. 99.9% of entries in the first 60 s of an M15 bar; mid == previous close in 100% of 54,492 evaluations; 383 trades hit the full initial stop (-$3,275, median hold 16 min). Losing in all sessions except the 21-24 UTC block (48 trades, too few). | The whole breakout loss, ~-$25/week at 0.01 lot | High | High |
| 2 | **Swing limit orders fill during the push through the swing.** | 77 trades, PF 0.72, -$55.80. 56 hit the initial stop (-$190.63) after a median 3.9 min; 34 of 62 losers stopped within 5 min. Fills in Asia (00-07 UTC): 34 trades, PF 0.34, -$58.90 -- more than the whole loss; London + overlap (07-16): 32 trades, +$16.78. Friday: 14 trades, 0 winners, -$45.59. The session and weekday splits are small samples. | The whole swing loss | High for the mechanism, low for the splits | High |
| 3 | **Exit management was never validated in MT5.** | The stairstep lock (stop to TP1 price) and trail 1.5 were chosen in v1.12 with the Python simulator that was later found to disagree with MT5 and removed. Breakout exits: TP3 closes 127 trades +$3,004.88 (avg 2.80R); stop moved and closed in profit 191 trades +$963.88 (0.59R); stop moved and closed at a loss 236 trades -$1,021.76 (-0.50R). Swing trades trail on ATR(M15) although planned on M30 structure. | Unknown; could be either sign | Medium | Medium |
| 4 | **Hedging account: a manual trade corrupts the EA's own stop management (fixed in v1.16).** | Tester harness that opens a manual SELL (other magic) before the EA trades, Jun 23-24: v1.15 copied the manual TP onto all 22 EA SELL positions, sent ~4,300 stop modifications in 2 days (the 500-point step guard compared against the manual stop) and got 13 invalid-stop rejections. The manual position was never modified or closed: `CTrade`'s symbol overloads filter by magic. Same harness on v1.16: 0 EA positions with the manual TP, 0 failed modifications, no modify requests carrying a TP, manual position untouched, same 36 EA entries. | Live only, when the user trades gold manually on the same account: wrong TPs on EA trades, request flooding | High | High (live) |
| 5 | **Stop modifications spam the server while the market is closed.** | 7,811 failed "Market closed" modify requests in a single 2-day run (Jan 5, 21:00 UTC daily break). No P/L effect in the tester. Not fixed in this round. | None in tests; broker may throttle live | High | Low-medium |
| 6 | **No order was sent without a stop.** | `ClampSLForOrder()` can return 0 (send without SL), but 0 of 6,570 logged entries had `sl=0.00` and 0 of 2,068 trades in the four trade CSVs lack an initial stop. | None observed | High | Low |
| 7 | **Small-account profit capture never works at 0.01 lot.** | Closes 50% of 0.01 = 0.00 lot, which `ClosePartial()` refuses; 0 captures in every $100 run in the logs (Sep 14-15). | None; misleading feature | High | Low |
| 8 | **`InpOnlyOnePosition=false` disables breakout entries entirely.** | Entry block requires `InpOnlyOnePosition && posDir == 0`. | None with the user's settings | High (code) | Low |
| 9 | **Dollar risk is not controlled.** | Fixed 0.01 lot: breakout risks $3.30-$27.17 per trade (1.7% of $500 on average), swing $2.14-$7.39 (0.7%). A $100 account hits the ~$53 margin floor. | Scales every other number | High | Medium |

Also checked and fine: entries happen at `InpTF` (M15) bar opens even on an H1 chart (99.9%);
swing-mode swings and bias use closed bars only; pending orders carry their stop.

## Alignment with a professional gold trader and the user's method

| User's method / pro practice | What the EA does | Gap | Codeable? |
|---|---|---|---|
| Bias from EMA direction + HH/HL on M30, H1, H4 | Swing mode does this (EMA50 slope, last two fractal swings, 2 of 3) | Aligned. Breakout mode uses only H1 EMA200 side. | Done |
| Mark the previous swing on M30/H1 for entry, stop, target | Swing mode: M30 swing, stop 0.3 ATR beyond, TP1 at opposite swing | Aligned | Done |
| Go back to M5 to find the exact entry | Limit order sits blindly at the swing | Missing: no reaction/confirmation, fills during stop runs (finding 2) | Yes -- E1 |
| Pending orders, re-check every 1-3 hours | Hourly re-check, orders kept while the plan holds | Aligned | Done |
| Trade London and New York | Trades 24 h; 44% of swing fills and 37% of breakout trades are in Asia, and they lose most | Missing | Yes -- existing session filter; E3 |
| Careful on Monday, Friday, news days | Nothing | Missing; Friday 0/14 swing winners (small sample); news needs an imported calendar (MT5's calendar is unavailable in the tester) | Weekday yes; news with a schedule file |
| SL/TP "depend on market movement" (structure) | Swing: structure. Breakout: fixed 1 ATR(M15) | Breakout mode has no counterpart in the user's method | -- |
| Pro: stop beyond the swept liquidity, size from the stop | Fixed 0.01 lot, stop at the obvious swing | Missing | Yes (`InpUseRiskSizing` exists, untested) |
| Pro: trail by structure, partials at TP1 | Stop jumps to TP1 price (near-market exit), ATR(M15) trail | Partly misaligned (finding 3) | Yes |
| Pro: 0.5-1% risk, 2-3% daily loss limit, stop after a losing streak | None | Missing | Yes |

## Experiments

All on the 12 in-sample weeks, real ticks, $500 each week, 0.01 lot, the user's inputs; new
inputs at default unless listed. Pre-registrations and full per-week results: `JOURNAL.md`
(2026-09-15, "Pro trader review, round 1"). Promotion bar raised to PF >= 1.25 because ~5 ideas
had already been tried on these weeks. Every run's tester log was checked for the applied inputs,
a ticks line and a final balance.

| ID | Hypothesis | Change | In-sample result | Validation / holdout | Decision |
|---|---|---|---|---|---|
| Check | v1.16 defaults = v1.15 | none | Jun 22 + Jul 6, both modes: 176 trades identical to the stored v1.15 trades | -- | Stored v1.15 baseline valid |
| Base B | -- | v1.15 breakout | 943 trades, PF 0.93, -$300.18; 15.7/day; worst week DD 50.0%; 6/12 weeks + | not run | Baseline |
| Base S | -- | v1.15 swing | 77 trades, PF 0.72, -$55.80; worst week DD 4.8%; 4/12 weeks +; 55% of losers stopped <= 5 min | not run | Baseline |
| E1 | Waiting for a sweep of the swing and an M5 close back on the bias side filters out pushes through the level | `InpEntryMode=1`, `InpSwingEntryStyle=1` (sweep limit 1.0 ATR, stop 0.3 ATR beyond the sweep) | 56 trades, PF 1.01, +$2.30; win 33.9%; avg loss -$5.88 (was -$3.24); worst week DD 5.3%; 5/12 weeks +; better than baseline 6/12; losers stopped <= 5 min 11% (target met); one week = +$49.97 | not run (failed IS) | **Rejected**: PF, trades, weeks-better criteria failed |
| E2 | Entering only on a closed-bar regime flip in the H1 EMA200 direction removes random overtrading and adds information | `InpBreakoutClosedBar=true`, `InpUseMidlineBreakout=false`, `InpRequireTrendFlip=true` | 124 trades, PF 1.01, +$6.88; 2.1/day (target met); win 36.3%; worst week DD 12.3%; 7/12 weeks +; better than baseline 7/12; Aug 10 alone +$99.61 | not run (failed IS) | **Rejected**: PF, weeks-better criteria failed; loss removed, no edge |
| E3 | Take the E2 flip only when the M30/H1/H4 bias agrees | none -- screening split of the 124 E2 trades by the bias logged in the E1 runs | agree 23 trades PF 1.05; WAIT 90 PF 1.09; against 11 PF 0.40 | -- | **Not run**: no sign of edge, sample far below 80 |

Reading the two failures together: both new entries end up at the same place as a random entry
with this exit ladder -- win rate 34-36% against an average win of about 1.6-1.8x the average
loss, which is breakeven. Cutting overtrading and fast stop-outs removed costs, not the lack of
an edge. Trade lists: `mt5_review_E1E2_12wk_trades.csv`.

## Recommended changes

**Trading settings: none proven.** No candidate passed in-sample, so nothing reached validation
or holdout. Keep the live inputs as they are until something does.

**Code fix (verified, not a strategy change): deploy v1.16 when you are ready** (your decision --
it replaces the EA on the live chart). `MoveSLto()` now selects and modifies the EA's own
position by magic number and ticket. With no manual trades it trades identically to v1.15
(4 of 4 week/mode runs identical); with a manual XAUUSDm trade open it no longer copies that
trade's TP or floods the server (harness test, finding 4).

**Not proven, available behind inputs that default off:**
- `InpSwingEntryStyle=1` (confirmation entry): removes swing mode's fast stop-outs; PF 1.01 in-sample.
- `InpBreakoutClosedBar=true` with `InpUseMidlineBreakout=false`, `InpRequireTrendFlip=true`:
  removes breakout mode's overtrading; PF 1.01 in-sample. If breakout mode stays on a demo
  chart for observation, these settings lost far less in-sample (+$6.88 vs -$300.18, worst week
  12% vs 50%), but that is not evidence of profit and it has not seen validation data.

**Candidates for a next round (pre-register first; none tested):**
1. Exit management in the real tester: the stairstep lock to the TP1 price and the 1.5 x ATR(M15)
   trail were chosen with the rejected Python simulator (finding 3). Compare against a stop to
   breakeven or to the last M15 structure, on the E1/E2 entries.
2. Risk-based sizing (`InpUseRiskSizing`, 0.5-1%) so R-multiples translate into equal dollars.
3. A news blackout from a user-supplied release schedule.
4. Throttle stop modifications after a "Market closed" rejection (finding 5; live-only effect).

## Risk and live-deployment guidance

- **No live money on either mode.** Nothing in this round has passed validation (see Verdict).
- **Breakout mode is not safe to demo-forward as a money-maker:** on $500 at 0.01 lot its worst
  in-sample week was -$222.05 (50% drawdown) and it pays ~$20 a week in spread for no edge.
- **If the robot keeps running on demo** for observation, prefer swing mode (worst weekly
  drawdown 4.8% on $500, ~0.7% risk per trade at 0.01 lot), with a hard stop rule: switch it off
  after a 3% daily loss ($15 on $500), 4 losses in a row, or a 6% weekly drawdown, and review.
- **Account size:** at least $500 for 0.01 lot. A $100 account hits the ~$53 margin floor and
  cannot control risk per trade at all.
- **Manual trading on the same account:** v1.15 (currently on the chart) copies a manual
  trade's TP onto its own positions and floods the server with stop modifications when a manual
  gold trade was opened first. Until v1.16 is deployed, don't trade XAUUSDm by hand on the
  account the EA runs on, or use a separate account.
- **Before any live money:** a candidate must pass in-sample, validation and the untouched
  holdout, then run 4-6 weeks demo-forward with weekly results inside the tester's range.
  Targets from the protocol: 200+ trades over all periods, PF >= 1.3, positive in >= 55% of
  weeks, weekly drawdown <= 10% at 1% risk per trade.

## Open questions for the user

1. Do you trade XAUUSDm by hand on the same account the EA runs on? If yes, the v1.16 fix
   should go on the chart soon -- say when you want it deployed (it replaces the live EA).
2. What account size and risk per trade do you intend live, and what weekly drawdown would
   make you switch the robot off?
3. Which exact hours do you trade (in UTC or your local time)? The London/New York window used
   here (07:00-20:00 UTC in summer) is an assumption.
4. Breakout mode is not part of your method and has no edge in any test so far. Should swing
   mode become the default (a default change, so your decision)?
5. Can you provide a list of the news events you avoid (e.g. NFP, CPI, FOMC dates and times)?
   MT5's calendar does not work in the Strategy Tester, so a news filter needs a schedule file.
6. When TP1 is reached, do you want the stop moved to the TP1 price (today's behavior: the
   trade usually closes right there), to breakeven, or to the last M5/M15 structure? This was
   chosen with the rejected Python simulator and needs a real tester run.
7. May I add a fix for the stop-modification spam while the market is closed (7,811 rejected
   requests in one 2-day test)? It does not change backtest results but changes live requests.
8. OK to push v1.16 to GitHub? (Committed locally only.)
