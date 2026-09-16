# MGNFY GOLD -- Pro Trader Validation Report, Round 3

- **Date:** 2026-09-16
- **EA build:** v1.18 (one validated default change; a new market-context engine, all of it off by default)
- **Data:** MT5 Strategy Tester, every tick based on real ticks, XAUUSDm (Exness demo, hedging, 1:100),
  the user's inputs plus the v1.17/v1.18 defaults, $5,000 at the start of each week, 1% risk per trade
- **Periods:** in-sample Jun 22 - Sep 11 (12 weeks); **validation Mar 2 - May 22 -- used once in this
  round and now spent**; **holdout Jan 5 - Feb 27 -- still untouched**
- **Previous rounds:** `reviews/2026-09-15-pro-trader-review.md`,
  `reviews/2026-09-15-pro-trader-review-round2.md`. Every number here: `JOURNAL.md`, "Review round 3".

## Verdict

**One change earned its place, and the market-context work turned up something more important than an
experiment result.** The M30 trailing stop passed its pre-registered validation run on data it had
never seen (+29.74R vs +17.80R for the old trail) and is now the default. The two context filters the
diagnosis supported -- skip Fridays, skip the Asia hours -- both missed their pre-registered bars and
stay off.

The finding that matters most: **the 12 weeks we have been tuning on contain no abnormal market at
all.** Every one of those 71 days sits between 0.82x and 1.18x the 20-day median of ATR(D1), while the
year as a whole is 13% compressed and 16% expanded. So the market-context features the user asked for
(is this week normal, expanded or dead?) **cannot be judged on the tuning data** -- there is nothing
abnormal in it to react to. They are built, verified to work, and deliberately shipped switched off.

And on the $100 account: the robot **correctly refuses to trade at all** at that balance, because every
setup's stop would risk 3.4-17.2% of equity at the minimum lot. The fix is balance, not a preset.

## Task A -- validation of the M30 trailing stop: PASSED

One batch each, Mar 2 - May 22, same settings, only the trail timeframe differing. All 12 weeks had
tick data and the intended inputs in the tester log; the first validation week traded.

| Mar 2 - May 22 | Trades | Win% | Total R | Avg R | PF (R) | Net $ | PF ($) | Weeks R >= base | Paired dR (t) | Worst week DD |
|---|---|---|---|---|---|---|---|---|---|---|
| Trail 1.5 x ATR(M15) (old default) | 59 | 44.1 | +17.80 | +0.302 | 1.68 | +861.88 | 1.73 | -- | -- | 3.0% |
| Trail 1.5 x ATR(M30) (candidate) | 57 | 38.6 | **+29.74** | **+0.522** | 2.02 | **+1,362.66** | 2.01 | 6/12 | **+0.190 (t 1.26)** | 3.4% |

Pre-registered in round 2, before the run: paired dR > 0, at least half the in-sample +0.179R (so
>= +0.090R), and total R >= the baseline's. All three are met, so the rule is applied as written:
**`InpTrailATRTF` now defaults to M30.**

Stated plainly, because it matters more than the headline: 26 of the 57 paired trades were *worse*
with the M30 trail and only 10 better -- the gain comes from a handful of large winners, t = 1.26 is
not significant, and it beat the old trail in only 6 of 12 weeks. This is a pre-registered pass on
fresh data, not a proven edge. Mar - May is now used; Jan 5 - Feb 27 is the last clean data we have.

## Task B1 -- what "normal" looks like, measured

XAUUSDm, Dec 2025 - Sep 2026, 56,013 M5 bars (`review-scratch/context_diag.py`).

| What | Measured |
|---|---|
| Daily true range | median **71.66**, 10th-90th percentile 26.2-156.9; ATR(14) median 83.0 |
| Busiest hours (median M5 range) | 13:00-15:00 UTC **7.5-7.9**, then 01:00 (6.8), 15:00 (6.7) |
| Quietest hours | 20:00-21:00 **3.2**, 03:00-04:00 3.3-4.0 |
| Tick volume | 13:00-14:00 ~2,050-2,135 per M5 bar vs ~420-820 overnight |
| Weekday | almost flat (median M5 range 4.65 Mon to 4.97 Thu) |
| Spread | 260 points nearly always; >= 2x its hour's median on 0.27% of bars |
| Shocks | M5 range >= 4x its hour's median ~8x a day, >= 6x ~2.9x a day; the 30 min after a 6x bar average 5.9x normal, so shocks cluster |

**Volatility state by period** (ATR(D1) known at the open vs its own 20-day median):

| Period | Days | min / median / max | Compressed <0.8 | Normal | Expanded >1.25 |
|---|---|---|---|---|---|
| In-sample Jun 22 - Sep 11 | 71 | 0.82 / 0.99 / 1.18 | **0** | **71** | **0** |
| Validation Mar 2 - May 22 | 70 | 0.60 / 0.98 / 1.36 | 18 | 44 | 8 |
| Holdout Jan 5 - Feb 27 | 47 | 0.44 / 1.12 / 3.32 | 10 | 18 | 19 |
| Whole year | 403 | 0.44 / 1.00 / 3.32 | 52 (13%) | 255 | 63 (16%) |

**Where the losses actually sit** (R-multiples; trade counts in brackets):

| Split | What the data says |
|---|---|
| Daily regime | Untestable in-sample: all 56-943 trades in every in-sample dataset fall in "normal" days |
| M30 volatility at entry | **No consistent sign.** Compressed: +23.2R (110 trades, v1.11) but -18.9R (52, v1.13). Expanded: +4.8R (139, v1.15) but -3.2R (15, E2) |
| Hour of day | Asia 00:00-06:00 negative in 5 of 6 datasets (-15.5R/299, -13.2R/84, -17.0R/162, -12.6R/28, -1.3R/18; E2 +5.4R/34 is the exception). The *best* block differs per dataset |
| Weekday | **Friday negative in all six datasets** (-9.5R/166, -14.0R/14, -10.5R/25, -6.4R/11, -6.3R/11, -3.4R/16) |
| Shocks | Only **2 of B2's 56** in-sample trades were entered within 30 min of a >= 4x shock (3 within 60 min) -- so a shock pause changes almost nothing in-sample |

Caveat on the "six datasets": they are different builds over heavily overlapping weeks, so this is
six views of much the same period, not six independent samples.

## Task B2 -- what was built (all off by default, all measured at runtime)

| Input | What it does |
|---|---|
| `InpUseContext`, `InpContextDays` | Median M5 range, tick volume and spread for each weekday/hour, rebuilt daily from the last 30 days. No hardcoded tables |
| `InpUseRegimeFilter`, `InpRegimeMinRatio/MaxRatio`, `InpRegimeRiskFactor` | Today's ATR(D1) against its own 20-day median; outside the band either skip the trade or trade it at a fraction of normal risk |
| `InpUseShockPause`, `InpShockRangeMult/VolMult/SpreadMult`, `InpShockCooldownMin` | An M5 bar far outside what *that hour* normally does, or a spread spike, pauses new entries for a cooldown. This is the backtestable answer to the news question: the Strategy Tester has no economic calendar |
| `InpSkipWeekdays` | No new entries on the listed weekdays (server time) |

**Verified in the tester with forced settings** (Jun 22 week), since none of them fires at sensible
settings in-sample:

| Check | Result |
|---|---|
| Shock pause at 3x, 60 min | 4 of 5 trades taken; the Monday 00:30 entry fell inside a cooldown |
| Regime band forced to 1.00-1.05, skip mode | **No trades at all** -- every setup skipped |
| Same band, risk factor 0.5 | Same 5 trades at half size (lots 0.01-0.03 vs 0.02-0.06; risk $17-24 vs $34-48) |

Two defects were found and fixed while checking, not assumed away: string inputs were reaching the EA
with the tester's optimization suffix attached (`InpSkipWeekdays=5||5||0||5||N`), and the new breakout
gate ran on every tick in swing mode, writing **1,591,589 log lines in one week** (trades unaffected;
now 5 lines, identical trades).

## Task B3 -- experiments

In-sample, 12 weeks, $5,000 per week, 1% risk. Baseline **B3 = v1.18 defaults** (which v1.18 reproduces
exactly on the checked weeks). Pre-registered bar: total R >= baseline + 3.0R, avg R >= baseline
+ 0.15R, weekly R >= baseline in >= 7 of 12, worst weekly DD <= 1.25x baseline, and the removed trades
negative. Ideas tried on these weeks: **14**.

| ID | Change | Trades | Win% | Total R | Avg R | PF (R) | Net $ | Weeks R >= B3 | Worst week DD | Decision |
|---|---|---|---|---|---|---|---|---|---|---|
| B3 | v1.18 defaults (M30 trail) | 57 | 38.6 | +18.92 | +0.332 | 1.60 | +901.36 | -- | 4.1% | Baseline |
| X3 | No Friday entries | 46 | 39.1 | +22.00 | +0.478 | 1.87 | +1,056.60 | 11/12 | 3.1% | **Failed**: avg R +0.478 < +0.482 required |
| X4 | No entries 00:00-06:00 UTC | 41 | 41.5 | +21.43 | +0.523 | 2.00 | +1,004.62 | 9/12 | 2.6% | **Failed**: total R +21.43 < +21.92 required |

X3 missed by 0.004R and X4 by 0.49R. Even a pass would have meant little: in both runs **every
surviving trade is identical to the baseline** (paired dR = 0.000), so the entire "improvement" is the
removal of trades that were negative in these same weeks -- the definition of the filter, not
evidence about the future. The regime filter and shock pause were not run as experiments at all,
because in-sample they would have changed 0 and 2-3 trades respectively.

## The $100 account -- and why there is no honest "small-account preset"

B3's stops are 3.44-17.23 price units, i.e. **$3.44-$17.23 risk at the 0.01 minimum lot** (median
$7.10).

| Demo balance | Skipped by the 1.5% cap | Taken | Mean risk of taken trades |
|---|---|---|---|
| $100 | **57 of 57** | **0** | -- |
| $500 | 26 | 31 | 1.08% |
| $1,000 | 5 | 52 | 0.84% |
| $2,000 | 0 | 57 | 0.83% |

At $100 the robot never trades -- that is the risk rule working, not a fault. If the cap were lifted so
$100 always traded 0.01 lot, real risk per trade would be **3.4%-17.2% of equity** (median 7.1%), 43 of
57 trades above 5%; two to eleven losers would halve the account. **So: fund the demo with $2,000 to
watch the tested behaviour** (or $1,000, accepting ~9% of setups skipped). No preset will make $100
behave like the tests, and any preset that appears to would simply be risking 3-17% per trade.

## Recommended changes

- **Adopted:** `InpTrailATRTF = PERIOD_M30` (validated).
- **Not adopted, available as inputs, all off:** `InpSkipWeekdays`, the session window, the regime
  filter, the shock pause, the movement profile.
- **For the demo-forward run:** v1.18 defaults, $2,000 demo balance, nothing else switched on, so the
  next round has a clean comparison.
- **Next round:** the holdout (Jan 5 - Feb 27) is the only untouched data, and it is the most abnormal
  stretch of the year (19 of 47 days expanded, up to 3.32x). That makes it the right place to judge a
  *context-aware* candidate -- for example the regime filter in risk-shrink mode -- and the wrong place
  to spend on another filter fitted to a calm summer. One candidate, pre-registered, one run.

## Risk and live-deployment guidance

- **Still no live money**, and the user's own plan (stay on demo until the account can carry 1% risk)
  is exactly right.
- **Demo balance $2,000**; expect roughly 4-5 trades a week, average +0.3R per trade in-sample and
  +0.5R on validation -- both on 57-trade samples, which is far too small to promise anything.
- **Stop rules:** the equity guard pauses entries at -10% from the rolling 7-day peak; switch the robot
  off and review after 6 consecutive losses or a week below -5R.
- **News:** the EA trades through FOMC/NFP/CPI. The shock pause is the only tested-to-work protection
  available in a backtest, and it is off by default because in-sample it has almost nothing to act on.

## Open questions for the user

1. Will you fund the demo to **$2,000** (or $1,000) so the robot behaves as tested? At $100 it will sit
   idle and that is correct behaviour, not a bug.
2. Is the equity-guard reading still right (pause while equity is 10%+ below its rolling 7-day peak)?
   It has never actually fired in any test, so it remains an unconfirmed interpretation.
3. For the holdout run next round, which single candidate do you want: the regime filter in
   **risk-shrink** mode (half size on abnormal days), the **shock pause**, or plain v1.18 defaults as a
   clean out-of-sample read?
4. Do you want Fridays off anyway as a personal rule? The test does not support it (it failed by a
   hair, and circularly), but `InpSkipWeekdays="5"` is there if you prefer it.
5. Is a **shock detector** an acceptable stand-in for your news concern -- "the market just moved 6x
   what this hour normally does, wait 30 minutes" -- given the tester has no calendar?
6. Should the HUD show the context state (normal / compressed / expanded, shock cooldown) once you
   start watching it on a funded demo?
