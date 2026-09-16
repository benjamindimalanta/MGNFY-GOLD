# MGNFY GOLD -- Pro Trader Validation Report, Round 4 (the holdout)

- **Date:** 2026-09-16
- **EA build:** v1.19 (Fridays off by preference; the $100 account made legible; no change to trade
  selection or sizing)
- **Data:** MT5 Strategy Tester, real ticks, XAUUSDm, $5,000 at the start of each week, 1% risk per
  trade, v1.18 defaults
- **Holdout:** Jan 5 - Feb 27, 2026 -- 8 weeks, never used for any decision until this run. It is the
  most abnormal stretch of the year: 10 compressed and 19 expanded days of 47, ATR(D1) ratio 0.44-3.32
- **Status of the data:** in-sample (Jun 22 - Sep 11), validation (Mar 2 - May 22) and now the holdout
  have all been used. **No untouched period remains.**
- Earlier rounds: `reviews/2026-09-15-pro-trader-review.md`, `-round2.md`, `2026-09-16-...-round3.md`

## Verdict

**The strategy's first clean out-of-sample read is positive but small: 41 trades, +$408.78, PF 1.41,
+8.22R (+0.201R per trade), 5 of 8 weeks positive, worst week -$183.48.** That is the most meaningful
number this project has produced, because nothing about these weeks influenced any decision.

**The candidate you chose for the holdout failed.** Halving size on abnormal days cut the worst weekly
drawdown from 3.90% to 2.20% -- exactly what it was built to do -- but it also cut profit from $408.78
to $133.81, keeping only 33% where the pre-registered bar was 60%. On these weeks the abnormal days
*were* the profitable days. It stays off by default.

And the honest conclusion for the project: **there is no clean data left**. Every further claim about
this EA has to come from forward observation on a demo or live account, not from another tester round.

## Task A -- the holdout run

Both runs: 8 weeks, tick data confirmed for all 8, intended inputs in every tester log, Friday rule
**off in both** so the comparison isolates the regime filter.

| Jan 5 - Feb 27 | Trades | Win% | Net $ | PF ($) | Total R | Avg R | Weeks + | Worst week DD | Avg lot | Partial closes |
|---|---|---|---|---|---|---|---|---|---|---|
| v1.18 defaults (baseline) | 41 | 36.6 | **+408.78** | 1.41 | +8.22 | +0.201 | 5/8 | 3.90% | 0.047 | 8 |
| + regime filter at 0.5x risk | 41 | 36.6 | **+133.81** | 1.19 | +8.91 | +0.217 | 5/8 | **2.20%** | 0.033 | 1 |

Pre-registered criteria and outcome:

| Criterion | Required | Actual | |
|---|---|---|---|
| Worst weekly drawdown | <= 3.12% (0.80x baseline) | 2.20% | pass |
| Net $ | >= $245.27 (0.60x baseline) | **$133.81** | **fail** |
| Same trades, not different ones | count +/-10%, total R +/-1.0R | 41 vs 41, +8.91 vs +8.22 | pass |

Weekly net $ (baseline | candidate): +145.89 | +0.22, -30.91 | -30.91, +66.46 | +66.46,
-56.78 | -56.78, +187.23 | +107.43, +38.24 | +11.34, +242.13 | +119.05, -183.48 | **-83.00**.

**Why "no change in R" here is arithmetic, not a failure.** R is a trade's P/L divided by the risk that
trade actually took. Halving the lot halves both, so **risk-shrink mode cannot change R by
construction** -- it can only change dollars, drawdown and the shape of the equity curve. That is why
this candidate was judged on money and drawdown, with R used only to confirm it resized rather than
re-selected (it did: all 41 trades are the same trades). The small R difference (+8.22 -> +8.91) is a
side effect of lot rounding, and it exposes something worth knowing: at 0.033 average lots, a 33%
partial close rounds to zero, so **partial profit-taking collapsed from 8 trades to 1**. Shrink mode
on a small account quietly disables the TP ladder.

**What it would take to call this filter useful:** an account where drawdown, not profit, is the
binding constraint. At 1% risk and a worst week of -4.09R, it is not.

### Friday on the holdout -- observation, not a test
The six Friday trades in the holdout made **+$173.70 (+3.48R)**. Removing them would have cut the
baseline from +$408.78 to +$235.08. Together with the failed and circular in-sample test, the record
is: **no data supports the Friday rule, and the only clean data argues against it.** It is on by
default because you asked for it, and it is labelled everywhere as a preference.

## Task B -- Fridays off by default

`InpSkipWeekdays` now defaults to `"5"`. The input comment, the CHANGELOG and this report all record
it as your preference with the failed test noted, so a later reader cannot mistake it for a validated
edge. Set it to `""` to trade every day.

Verified on two in-sample weeks that contain Friday entries: Jun 22 went from 5 trades to 4 and
Aug 17 from 4 to 2, removing exactly the Friday entries, with **every remaining trade identical**.

## Task C -- making the $100 account legible

At $100 the robot refuses every setup: its stops cost $3.44-$17.23 at the 0.01 minimum lot, i.e.
3.4%-17.2% of the balance against a 1.5% cap. That is the risk rule working, but on screen it looks
like a broken robot. Without touching the cap, v1.19 now explains itself.

- **In the log, once per refused setup:**
  `Swing: setup skipped -- SELL at 3993.112, 0.01 lot would risk 17.2% of $100.00 (cap 1.5%, stop 17.23); this setup needs about $1149 balance`
- **On the HUD (SYSTEM block, two new lines):** the market state (`Market: expanded (ATR D1 1.42x its
  20-day median)`) together with why entries are off (`Entries: paused (equity guard)`, `Entries:
  paused (shock, ~18 min left)`, `Entries: off today (weekday rule)`), and the last refused setup in
  the same words as the log.

**Verified** on a $100 tester week: 0 trades taken and 4 explanatory lines written, with the balances
each setup needed ($530, $572, $662, $1,149). **Limitation to be honest about:** that run verified the
log text and the code path; the HUD panel itself was not captured visually this round, so the
rendering is verified by construction (same strings, same build-once/update-in-place pattern as the
rest of the panel), not by screenshot.

## What the whole project looks like now

| Period | Role | Trades | Avg R | Net $ (at $5,000 weeks) |
|---|---|---|---|---|
| Jun 22 - Sep 11 | in-sample, tuned on, ~14 ideas tried | 57 | +0.332 | +901 |
| Mar 2 - May 22 | validation, used once for the trail | 57 | +0.522 | +1,363 |
| Jan 5 - Feb 27 | holdout, used once, now spent | 41 | **+0.201** | **+409** |

The ranking is consistent and the effect is small -- expectancy shrinks as the data gets cleaner,
which is exactly what an honest, weak-but-possibly-real edge looks like. 155 trades across all
periods is still far below the 200+ the protocol wants before recommending a demo-forward test, and
the in-sample figure is inflated by the tuning.

## Recommended settings

Unchanged from v1.18 except the Friday preference: swing mode with the M5 confirmation entry, 1% risk
with the 1.5% cap, equity guard (10% over a rolling 7 days, still an unconfirmed interpretation of
your rule), market-closed throttle, ATR(M30) trail, **Fridays off**, and the market-context features
(profile, regime filter, shock pause) **off**.

## What I would do next, given that no clean data is left

1. **Stop tuning.** More runs on these weeks can only fit them better.
2. **Forward-observe.** Run v1.19 on the demo as it is. At $100 it will not trade, and the log and HUD
   will now tell you why -- which is itself the thing to watch: every skipped setup is a trade the
   strategy wanted, with the balance it needed.
3. **Collect the same numbers forward** that the tester produced: per-trade R, weekly R, worst week.
   After ~40 forward trades there is something to compare against the +0.201R holdout figure.
4. **Revisit the regime filter only if drawdown becomes the binding constraint**, and the shock pause
   only if a forward shock actually hits a trade -- in 12 in-sample weeks it would have touched 2 or 3.

## Open questions for the user

1. The equity guard is still an unconfirmed reading of your "moving 10% weekly" rule and has never
   fired in any test. Is the reading right?
2. Is the shock detector an acceptable stand-in for news (the tester has no calendar), and do you want
   it on for forward observation even though it is untested?
3. Do you want a HUD screenshot check on your $100 demo chart, so the new status lines are confirmed
   visually rather than by log?
4. When the balance does allow 1% risk, do you want to start at 0.5% for the first forward weeks?
