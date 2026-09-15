# MGNFY GOLD -- Pro Trader Validation Report, Round 2

- **Date:** 2026-09-15
- **EA build:** v1.17 (user-approved defaults; exit, trail and trade-window variants behind inputs)
- **Data:** MT5 Strategy Tester, every tick based on real ticks, XAUUSDm (Exness demo, hedging,
  1:100), the user's tester inputs (H1 chart, `InpTF`=M15) plus the v1.17 defaults, 12 in-sample
  weeks Jun 22 - Sep 11, 2026, each week a separate test starting at **$5,000** with **1% risk per
  trade**
- **Why $5,000:** at $500, 1% is $5 and XAUUSDm's 0.01 minimum lot moves $1 per 1.00, so lot sizes
  would be 0.01-0.02, partial closes at TP1/TP2 impossible and about half the trades skipped by the
  risk cap (see finding 2). $5,000 lets 1% risk and the TP ladder work as designed. Results in R
  apply to any account where 1% is implementable; $ figures are about $50 per R.
- **Validation (Mar 2 - May 22) and holdout (Jan 5 - Feb 27):** **fresh** -- not run, because no
  variant passed in-sample. Jan 5-7 was used only to count rejected stop modifications.
- **Previous round:** `reviews/2026-09-15-pro-trader-review.md`. Pre-registrations and every
  number below: `JOURNAL.md`, "Review round 2".

## Verdict

**The user's risk controls are in and verified; no edge has been proven, so it is still not ready
for live money.** The new defaults (B2: swing mode, confirmation entry, 1% risk, equity guard,
market-closed fix) made 56 trades in 12 weeks, **+3.37R total (+0.06R per trade), +$115 on $5,000
weeks, PF 1.09, 6 of 12 weeks positive, worst week -4.0%** -- about breakeven. On the exit
question: moving the stop to breakeven at TP1 changes almost nothing (-0.75R). Letting trades run
with a looser trail -- ATR on M30 (+18.92R) or the last M15 swing (+19.27R) -- added about 15.5R,
but almost all of it came from two or three trending weeks, and both were worse than the
current exit in most weeks (paired t = 1.12 and 0.63 against the 2.4 required). That is a lead,
not proof, so **the current exit stays the default**. Your trading hours did not select better
trades: B2's trades inside your windows made -3.20R (24 trades) and those outside +6.57R (32), so
**around the clock stays the default**.

## What the robot actually does (v1.17 defaults)

1. **Bias, every hour:** on M30, H1 and H4, the last closed bar vs a rising/falling EMA50 plus the
   last two fractal swings making higher highs and higher lows (or the bearish mirror); 2 of 3 must
   agree, otherwise WAIT.
2. **Level:** the latest M30 swing low (buy) or high (sell) within 3 x ATR(M30) of price, with the
   opposite swing as TP1. The level is watched ("armed"), not traded with a limit order.
3. **Entry:** after price trades beyond the level (the sweep), the first closed M5 candle back on
   the bias side enters at market. Stop = the extreme of the sweep -/+ 0.3 x ATR(M30); skipped if
   TP1 is less than 1R away or the sweep runs more than 1 x ATR(M30) beyond the level.
4. **Size:** 1% of equity divided by the stop distance, floored to 0.01 lots, so at most 1%. If
   that is below the 0.01 minimum lot, the minimum is used only when it risks no more than 1.5%;
   otherwise the trade is skipped and logged.
5. **Management (unchanged):** at TP1, 33% closed (when the lot allows it) and the stop moves to
   the TP1 price; at TP2, 33% and the stop to the TP2 price; TP3 closes the rest; a 1.5 x ATR(M15)
   trailing stop runs throughout.
6. **Equity guard:** no new entries while equity is 10% or more below its highest value of the
   last 7 days; armed levels and pending orders are dropped; open trades keep their stops; entries
   resume when equity is back inside the limit or the old peak leaves the 7-day window.
   **Assumption:** this is our reading of your "moving 10% weekly drawdown limit".
7. **Market closed:** no stop modifications are sent while the symbol's trade session is closed.
8. Trades around the clock, one position at a time.

## Findings, ranked by money impact

| # | Finding | Evidence | $ impact | Confidence |
|---|---|---|---|---|
| 1 | **The trailing stop is the only lever that moved money -- and it is unproven.** | Same entries, looser trail: ATR(M30) +18.92R vs +3.37R; M15 structure trail +19.27R. ATR(M30): +26.7R in Aug 10 and Aug 24, -7.8R in the other ten weeks (current exit there: -4.6R); 26 trades worse, 11 better; paired +0.18R per trade, t 1.12. Structure: +39.7R in three weeks, -20.4R in the other nine (current: -6.5R); t 0.63. | About +$780 over 12 weeks at $5,000 in-sample, from 2-3 trend weeks; cost in choppy weeks | Low: consistent with a real "let trends run" effect and with luck |
| 2 | **Small accounts cannot run 1% risk on these stops.** | B2's stops: median 7.19, range 3.44-17.23 price. At 0.01 lot a 7.19 stop is $7.19. With the 1.5% cap, $500 skips 26 of 56 trades (tester check: 5 of 5 setups skipped in one week), $1,000 skips 5, $2,000 none. | Decides whether the EA trades at all on a small account | High |
| 3 | **Your trading hours did not pick the better trades (in-sample).** | X2: 27 trades, +0.97R. B2 inside 06-10/11-13/15-17 UTC: 24 trades -3.20R; outside: 32 trades +6.57R. By block: 13-15 UTC +6.42R (6 trades), 11-13 -2.87R (8), 15-17 -2.03R (2). | -2.4R vs around the clock | Low (27 vs 56 trades) |
| 4 | **Stop to breakeven at TP1 does nothing.** | 55 of 56 trades identical; TP1 (the opposite swing) is rarely reached before the 1.5 x ATR(M15) trail has already moved the stop past breakeven. Only 6 of 56 trades reached TP1 with a partial close. | -0.75R | High |
| 5 | **Market-closed fix works and changes no trades.** | Jan 5-7 breakout run: 7,811 rejected "Market closed" modifications before, 0 after; the 28 trades and final balance ($581.63) identical. | None in tests; removes live request flooding | High |
| 6 | **The equity guard works but never fires at 10% on these weeks.** | Worst weekly closed-balance drawdown 4.0% (B2), 4.6% (any variant); 0 activations in 65 runs. Forced test (1% / 1 day): paused, skipped 46 hourly checks, 3 entries instead of 5, resumed when the peak aged out. It flapped with a trade open (152 log lines in one week); logging now capped to one line per minute (14 lines, same trades). Each test week starts fresh, so the 7-day window only ever saw one week. | Protection only | High for the mechanics |
| 7 | **Tool bugs found and fixed.** | The trade parser read balances of $1,000+ ("5 080.46") as missing, which zeroed weekly drawdowns in the first pass, and crashed on a week with no trades. All round-2 reports re-parsed. | Would have hidden drawdowns | High |

## Alignment with a professional gold trader and your method

| Topic | Now in v1.17 | Comment |
|---|---|---|
| Top-down bias on M30/H1/H4, swing levels, M5 entry | Yes (default) | Matches your steps 1-5. |
| Risk 1% per trade, sized from the stop | Yes (default) | Needs an account of roughly $1,000-2,000+ for these stops (finding 2). |
| "Moving" 10% weekly drawdown limit | Yes (default), as a rolling 7-day equity peak | Our interpretation; please confirm. |
| London / New York hours only | Available (`InpUseTradeWindows`), off | In-sample the hours removed the better trades (finding 3). If you want the robot to trade only while you are watching, that is a valid operational choice, but it is not supported as an edge. |
| Take care around FOMC/NFP/CPI | Not built | Future candidate: reduced risk around them (needs a date list). |
| Exits "depend on market movement" | Current: stop to TP1/TP2 price + ATR(M15) trail | A pro would trail by structure on trends. The data leans that way (finding 1) but is not proven. |

## Experiments

Pre-registered in `JOURNAL.md` before running. Bar for a clear in-sample pass (exits): paired mean
dR >= +0.10R per trade with t >= 2.4 (3 variants), total R >= B2, weekly R >= B2 in >= 7 of 12
weeks, worst weekly drawdown <= 1.25 x B2. Trade windows: average R >= B2 + 0.15R, PF(R) >= 1.25,
the removed trades negative. **Sample-size limit:** 55-57 trades per exit run and 27 for the
windows, below the protocol's 80 -- nothing here can prove an edge. Ideas tried on these 12 weeks
so far: 12.

All: 12 weeks in-sample, $5,000 per week, 1% risk, confirmation entry.

| ID | Change | Trades | Win% | Total R | Avg R | PF (R) | Net $ | PF ($) | Weeks R >= B2 | Paired dR (t) | Worst week DD | Validation / holdout | Decision |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B2 | v1.17 defaults: stop to TP1/TP2 price, 1.5 x ATR(M15) trail, around the clock | 56 | 33.9 | +3.37 | +0.060 | 1.12 | +115.35 | 1.09 | -- | -- | 4.0% | not run | Baseline, kept |
| X1a | Stop to breakeven + spread at TP1, TP1 price at TP2 | 56 | 33.9 | +2.62 | +0.047 | 1.09 | +77.96 | 1.06 | 11/12 (55 trades identical) | -0.013 (t -1.00) | 4.0% | not run | **Rejected** (falsified) |
| X1b | From TP1, stop trails the last closed M15 swing; no ATR trail | 55 | 30.9 | +19.27 | +0.350 | 1.52 | +951.71 | 1.55 | 4/12 | +0.153 (t +0.63) | 4.6% | not run | **Not proven** (t, weeks) |
| X1c | ATR trail on M30 instead of M15 | 57 | 38.6 | +18.92 | +0.332 | 1.60 | +901.36 | 1.60 | 6/12 | +0.179 (t +1.12) | 4.1% | not run | **Not proven** (t, weeks) |
| X2 | Entries only 06-10, 11-13, 15-17 UTC | 27 | 29.6 | +0.97 | +0.036 | 1.07 | +46.57 | 1.07 | 6/12 | 24 shared trades unchanged | 1.9% | not run | **Rejected** (falsified) |

Weekly R (Jun 22 ... Sep 7):
- B2: -1.74, +1.87, -2.48, +3.04, -1.01, -2.25, +0.57, +5.29, -2.51, +2.72, -1.48, +1.34
- X1b: -5.06, +11.65, -3.54, +2.69, -3.04, -4.07, -2.03, +13.52, +0.75, +14.52, -3.03, -3.08
- X1c: -3.00, +2.64, -3.49, +3.40, -2.30, -1.96, +2.35, +14.34, -3.07, +12.34, -1.84, -0.50

Checks behind these runs: v1.17 with old inputs reproduced the v1.15 trades exactly; every batch's
tester log showed the intended inputs and a ticks line for all 12 weeks; lot sizes 0.02-0.14,
risk 0.68-1.04% of the week's starting balance; 0 trades skipped by the cap and 0 guard activations
at $5,000. Trade lists: `mt5_review_round2_12wk_trades.csv`.

## Recommended changes

**In v1.17 as defaults (approved risk controls, not a claim of edge):** swing mode with the
confirmation entry; `InpUseRiskSizing=true`, `InpRiskPercent=1.0`, `InpMaxRiskPercent=1.5`;
`InpUseEquityGuard=true`, 10%, 7 days; `InpThrottleClosedMarket=true`.

**Exit rule -- decision: keep the current one** (`InpExitAtTP1=0`: stop to the TP1 price, then the
TP2 price; `InpTrailATRTF` = the working timeframe, i.e. 1.5 x ATR(M15)). Breakeven at TP1 was
tested and does nothing. The looser trails earned more in 12 weeks but only through a few trend
weeks and lost more in most other weeks, which fails the pre-registered bar. They stay available
(`InpExitAtTP1=2`, `InpTrailATRTF=30`), not proven.

**Trade windows: not proven, off.** `InpUseTradeWindows=true` uses your hours if you want the robot
to trade only while you watch.

**Next step (needs your OK):** one pre-registered confirmatory test of the M30 ATR trail (the
simpler of the two) on the unused validation weeks, Mar 2 - May 22, against B2 on the same weeks.
It is the only idea from this round with a plausible mechanism and a large in-sample effect, and a
single test keeps the validation weeks meaningful.

## Risk and live-deployment guidance

- **No live money yet.** B2 is near breakeven in-sample and nothing has passed validation.
- **Demo-forward** the v1.17 defaults for 4-6 weeks on a demo account sized like your intended live
  account, and compare weekly R with the in-sample range (worst week -2.5R, best +5.3R).
- **Account size:** with 1% risk and these stops (median ~$7 per 0.01 lot), use at least $1,000,
  better $2,000. On $500 about half of the setups are skipped by the 1.5% cap (by design: taking
  them would risk up to 3.5%).
- **Stop rules:** the equity guard pauses entries at -10% from the 7-day peak; also switch the robot
  off and review after 6 consecutive losses or if a week falls below -5R (worse than anything seen
  in-sample).
- **News:** the EA trades through FOMC/NFP/CPI; widen nothing and do not add size around them until
  a reduced-risk rule is tested.

## Open questions for the user

1. What is the live account size? It decides whether 1% risk works (see finding 2).
2. Is the equity guard reading right: pause new entries while equity is 10% or more below the
   highest equity of the last 7 days, resume once back inside or when that peak is older than 7
   days?
3. We made the M5 confirmation entry the default for swing mode (better than the limit order in
   round 1, and your own M5 step). OK?
4. May we run the single confirmatory test of the M30 ATR trail on the Mar 2 - May 22 weeks?
5. Do you still want the robot limited to your hours for practical reasons, even though the test
   did not show better trades inside them? (`InpUseTradeWindows=true`)
6. For a future reduced-risk rule around FOMC, NFP and CPI: how much less risk, and from how long
   before to how long after the release?
