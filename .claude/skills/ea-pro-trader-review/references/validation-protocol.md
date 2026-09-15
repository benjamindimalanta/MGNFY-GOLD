# Validation protocol

How to decide whether a change to the EA is real. The point is to separate an actual edge from noise
and from the patterns you create by trying many settings on the same few weeks.

## Contents
1. Data split
2. Pre-registration template
3. Metrics to report
4. Promotion and acceptance criteria
5. Robustness checks
6. Multiple testing
7. Costs and account settings
8. Screening studies (replays) and when they are allowed
9. Walk-forward (optional, for final candidates)

---

## 1. Data split

Use three sets and write down which weeks are in each before running anything:

- **In-sample (IS)**: weeks used to explore, diagnose and tune. You may look at these as often as needed.
- **Validation**: weeks used once per round to confirm IS winners before promoting them. After you use
  them to reject or pick candidates, they become effectively in-sample for later rounds.
- **Holdout**: weeks nobody has looked at for this strategy. Run the final candidate once. If you change
  anything after seeing the holdout result, the holdout is spent; report that and find fresh data.

Check `references/project-context.md` for which weeks have real tick data and which have already been
looked at. Weeks already analyzed in `JOURNAL.md` are *not* a clean holdout.

Always use full Monday-Friday weeks (tester `FromDate` = Monday, `ToDate` = Saturday) so results are
comparable, and keep a baseline run on exactly the same weeks and settings.

## 2. Pre-registration template

Add this to `JOURNAL.md` before running the experiment:

```markdown
### Experiment <ID> -- <short name> (pre-registered <date>)
- Hypothesis: <what should change and why, in trading terms>
- Change: <exact inputs / code change; default behavior unchanged?>
- Baseline: <build + inputs>
- Weeks: IS <list>; validation <list or "later">; holdout <untouched>
- Primary metric: <e.g. pooled net $ and PF on IS>
- Pass criteria: <see section 4, plus any experiment-specific target, e.g. "losers stopped within
  5 minutes fall by at least a third">
- What would falsify it: <result that means the idea is wrong>
```

Then add the result under the same heading, whether it passed or failed.

## 3. Metrics to report

Always pooled across weeks and per week, for baseline and candidate side by side:

| Metric | Why |
|---|---|
| Trades, trades/day | Sample size and overtrading |
| Win rate | Context for R:R |
| Avg win $, avg loss $, avg R of winners and losers | Where the edge or leak is |
| Net $, expectancy $/trade | The actual money |
| Profit factor | Gross won / gross lost |
| Max drawdown % per week (and over the full span if compounding) | Survivability |
| Positive weeks / negative weeks | Consistency |
| Median hold time of losers and winners | Stop-hunt vs trend-riding behavior |
| Exit reasons (SL, TP levels, trailing, end of test) | Whether management features fire |
| For pending-order modes: placed / kept / filled / cancelled, skip reasons | Whether logic works as designed |

Give the trade count wherever a rate or PF appears.

## 4. Promotion and acceptance criteria

These are defaults; tighten them if many experiments have been tried (section 6).

**Promote from IS to validation** only if all hold:
- at least **80 trades** pooled (or state clearly that the sample is too small to judge);
- **PF >= 1.15** and positive net $ after costs;
- better than baseline on **net $ in at least 60% of weeks**, not just on the pooled total;
- max weekly drawdown not worse than baseline by more than 25% (relative).

**Accept after validation / holdout** only if:
- **PF >= 1.10** on validation/holdout with a reasonable trade count;
- expectancy per trade keeps **at least half** of its IS value;
- no single week contributes more than **50%** of total net profit.

**Ready to recommend for a live demo-forward test** only if, across IS + validation + holdout:
- **200+ trades**, **PF >= 1.3**, positive in **>= 55%** of weeks, max weekly drawdown within the user's
  tolerance at the intended risk (default target: <= 10% at 1% risk per trade);
- it survived at least one clearly trending and one choppy/ranging period.

Live money comes only after a demo-forward period of several weeks that behaves like the tests.

## 5. Robustness checks

- **Neighborhood test**: for any tuned numeric input, also run values ~25-50% below and above. Accept the
  setting only if at least 2 of the 3 (value and neighbors) pass the IS criteria. A lone spike is noise.
- **Regime split**: check trending vs ranging weeks and high vs low volatility weeks separately.
- **Direction split**: long vs short should not rely entirely on one side unless the hypothesis is
  directional.
- **Cost stress**: rerun the finalist with wider spread (e.g. the tester's spread setting or a simple
  per-trade cost deduction in analysis) to make sure the edge isn't only a few cents per trade.

## 6. Multiple testing

Every experiment tried makes it more likely that one looks good by chance. Keep a running count in the
journal. After roughly 5 experiments on the same IS weeks, require a clearer margin (e.g. PF >= 1.25 on
IS) and lean harder on validation/holdout results. Report failed experiments with the same detail as
successful ones.

## 7. Costs and account settings

- `Model=4` (every tick based on real ticks) only; it carries the broker's real spread.
- **$500 deposit** for strategy evaluation: a $100 account with 0.01 lot hits a margin floor around $53
  and stops trading mid-week, which distorts results.
- State the sizing model. Fixed 0.01 lot makes dollar risk vary with stop distance; when stops differ a
  lot between modes, also compare in R or with `InpUseRiskSizing`.
- Leverage 1:100, XAUUSDm, same symbol settings as the user's account.

## 8. Screening studies (replays)

Replaying logged orders on M1 bars (e.g. `study_swing_sl.py`) is a fast way to rank ideas such as stop
sizes. Allowed when:
- the replay is **calibrated**: re-running the as-traded orders reproduces the tester's fills/outcomes
  closely (the swing-stop study reproduced the tester's 20 fills exactly);
- same-bar conflicts are resolved conservatively (stop first);
- the conclusion is labeled "screening" until confirmed by a tester run.

## 9. Walk-forward (optional, for final candidates)

Roll a window across the available weeks: tune on 8 weeks, test on the next 4, move forward 4 weeks,
repeat. Report the concatenated out-of-sample results only. A strategy that needs different settings in
every window has no stable edge.
