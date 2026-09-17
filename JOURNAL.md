# MGNFY GOLD -- Backtest Journal

Running log of every backtest batch tried and its result, driven entirely
by MT5's own Strategy Tester (not a custom simulation), so nothing gets
lost between sessions. Newest entries at the bottom. Each entry is
self-contained (dataset, config, full metrics).

**Standard report fields:** Trades / Win / Loss / Win% / Net $ / PF (profit
factor) / MaxDD% (max drawdown) / End Eq (ending equity from $100 start).

**Known facts established so far (don't need to re-test to confirm):**
- The live `MGNFY GOLD.mq5` (v1.11, currently compiled/attached in MT5) has
  a real bug, confirmed twice against MT5's own real-tick Strategy Tester:
  at 0.01 lot (MT5's minimum), the 1R/2R/3R partial take-profit system
  silently fails -- 33%/33% of 0.01 lot rounds to 0.00, so
  `ClosePartial()` refuses and `tp1Hit` never becomes `true`. Because TP3
  requires *both* `tp1Hit` and `tp2Hit`, the entire three-stage ladder is
  dead, not just TP1. **Direct evidence:** of 481 real trades in the
  2026-09-15 batch, every single closed trade exited via stop-loss (477)
  or a forced end-of-test mark-to-market close (4). Zero TP1/TP2/TP3
  exits. The EA is currently running, in practice, as "SL + unconditional
  ATR trailing stop only" -- the trailing stop (a *separate*, unconditional
  mechanism, step 5 in `OnTick()`, not gated by the broken TP ladder) is
  the only thing protecting profit right now, and it engaged on 60-71% of
  trades (moved the stop at least once) depending on timeframe. A v1.12
  fix exists in this repo's source but has not been deployed to the live
  MT5 terminal -- pending the user's explicit go-ahead (a "production
  deploy" the session's safety layer correctly declined to do
  automatically).
- MACD filter and H4 trend filter are off in every setting tested so far
  (matches the "Balance" preset / the user's own manual GUI backtest).
- Fixed 0.01-lot sizing on a $100 account regularly triggers a margin
  lockout after a short losing stretch, and -- newly quantified below --
  means the EA's real dollar risk-per-trade scales directly with
  whatever timeframe it's attached to, since stop distance is
  `1.0 x ATR(that timeframe)` but position size never adjusts for it.
- **M15 shorts significantly outperform M15 longs** in this sample (SELL:
  45.8% win / PF 1.47 / net +$244; BUY: 28.8% win / PF 0.65 / net -$219,
  132-142 trades each side -- large enough sample to be a real split, not
  noise). See the direction table and diagnosis section below before
  assuming this is a permanent structural edge rather than a reflection
  of gold's actual direction bias across the specific weeks sampled.

---

## 2026-09-15 (correction) -- previous Python-based journal and backtester were wrong, removed

An earlier session (not this one) built an offline Python bar-stepping
backtester and a `JOURNAL.md` from it. The user correctly identified that
it produced results that don't match MT5's own Strategy Tester on
identical settings. **That entire Python engine, its JOURNAL.md, and all
CSVs derived from it were deleted from this repo.** Going forward, this
journal is built exclusively from MT5's own Strategy Tester
(`terminal64.exe /config:<ini>`, `Model=4` -- real ticks, the same engine
and broker data the user's manual GUI backtest used), automated from the
command line via `mt5_journal.py`.

Two operational gotchas, recorded so they aren't rediscovered: (1) the
terminal must be fully closed before every `/config` launch -- passing
`/config` to an already-running instance silently reuses its last-configured
dates instead of the requested ones; (2) `Report=` in `[Tester]` must be a
flat filename (a subfolder path silently produces no report), and the
report lands in the terminal's data-path root, not `MQL5/Files/`.

15 real Strategy Tester runs (5 random weeks x M15/M30/H1, `SystemRandom`,
printed before any result was seen), 481 real trades, using the exact
same input settings as the user's own manual GUI backtest (the "Balance"
preset: ATR mult 2.0, SL 0.7%/1.0xATR, MACD off, trail 1.5x).

### Full per-run results

| Week | TF | Trades | Wins | Win% | Net $ | PF | MaxDD% | MaxConsecLoss | End Eq (from $100) |
|---|---|---|---|---|---|---|---|---|---|
| 2026-06-22_to_2026-06-28 | M15 | 75 | 25 | 33.3 | -50.92 | 0.87 | 71.7 | 10 | 47.48 |
| 2026-06-22_to_2026-06-28 | M30 | 4 | 0 | 0.0 | -56.99 | 0.00 | 50.6 | 4 | 43.01 |
| 2026-06-22_to_2026-06-28 | H1 | 10 | 4 | 40.0 | -54.33 | 0.43 | 48.4 | 2 | 45.67 |
| 2026-06-29_to_2026-07-05 | M15 | 10 | 2 | 20.0 | -52.71 | 0.13 | 52.3 | 4 | 47.29 |
| 2026-06-29_to_2026-07-05 | M30 | 43 | 17 | 39.5 | 90.06 | 1.36 | 45.2 | 6 | 189.00 |
| 2026-06-29_to_2026-07-05 | H1 | 4 | 0 | 0.0 | -61.25 | 0.00 | 59.3 | 4 | 38.75 |
| 2026-07-13_to_2026-07-19 | M15 | 91 | 33 | 36.3 | 58.54 | 1.15 | 59.8 | 8 | 155.35 |
| 2026-07-13_to_2026-07-19 | M30 | 46 | 17 | 37.0 | 4.52 | 1.02 | 44.4 | 8 | 102.92 |
| 2026-07-13_to_2026-07-19 | H1 | 23 | 9 | 39.1 | -21.50 | 0.88 | 64.5 | 4 | 76.90 |
| 2026-07-27_to_2026-08-02 | M15 | 84 | 40 | 47.6 | 122.33 | 1.51 | 28.3 | 4 | 219.67 |
| 2026-07-27_to_2026-08-02 | M30 | 40 | 18 | 45.0 | 170.24 | 2.08 | 26.4 | 4 | 267.58 |
| 2026-07-27_to_2026-08-02 | H1 | 18 | 6 | 33.3 | -53.65 | 0.64 | 67.6 | 3 | 44.75 |
| 2026-08-17_to_2026-08-23 | M15 | 14 | 3 | 21.4 | -52.21 | 0.25 | 49.4 | 6 | 47.79 |
| 2026-08-17_to_2026-08-23 | M30 | 12 | 4 | 33.3 | -49.86 | 0.28 | 46.0 | 3 | 49.61 |
| 2026-08-17_to_2026-08-23 | H1 | 7 | 1 | 14.3 | -63.81 | 0.07 | 58.0 | 4 | 35.66 |

### Pooled by timeframe -- now with real per-trade risk, R-multiples, and hold time

This is the enriched pass (re-parsed from the same 15 reports, joining
each report's Orders table -- which carries the *initial* SL price sent
with the entry order -- to its Deals table, to compute real R-multiples
and detect whether the stop ever moved from its initial placement):

| TF | Trades | Win% | PF | Net $ | AvgRisk$/trade | MaxRisk$/trade | AvgR(win) | AvgR(loss) | AvgHoldWin(min) | AvgHoldLoss(min) | %SLmoved(trailing) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| H1 | 62 | 32.3 | 0.54 | -254.54 | 17.11 | 28.82 | 0.91 | -0.75 | 608 | 162 | 60 |
| M15 | 274 | 37.6 | 1.02 | 25.03 | 8.52 | 21.26 | 1.39 | -0.79 | 114 | 58 | 65 |
| M30 | 145 | 38.6 | 1.20 | 157.97 | 11.89 | 23.35 | 1.53 | -0.74 | 332 | 90 | 71 |

**This directly answers "why does H1 only win 32.3%, and what's the
drawback":**

1. **It isn't really about win rate being uniquely bad on H1** -- 32.3%
   vs M15's 37.6% and M30's 38.6% is a real gap but not a dramatic one,
   and H1's average winning trade (0.91R) is actually the *weakest* of
   the three, not the strongest, so there's no hidden upside being masked
   by the headline win rate.
2. **The real drawback is dollar risk per trade.** SL distance is
   `1.0 x ATR(signal timeframe)`, and H1's ATR is naturally much wider
   than M15's -- but lot size stays fixed at 0.01 regardless of timeframe.
   Result: H1 risks an average of **$17.11 per trade (17% of the $100
   account)**, peaking at **$28.82 (29% of the account) in a single
   trade** -- roughly double M15's $8.52 average and 35% more than M30's
   $11.89. Every H1 loss is a much bigger bite out of the account than the
   same *logical* 1R loss would be on M15.
3. **Combine a sub-40% win rate with ~2x the dollar risk per trade** and
   the arithmetic explains the -$255 pooled net and the 48-68% max
   drawdown seen in every single H1 run (see the per-run table above --
   all 5 H1 weeks were individually net-negative, not just the pooled
   total). It isn't bad luck concentrated in one week; H1 lost money in
   every week tested.
4. **Sample size compounds the problem**: only 62 H1 trades across 5
   weeks (~12/week) vs 274 on M15. A few consecutive losses (H1 hit 4 in
   a row in 3 of its 5 weeks -- see the streak table below) at
   $17-29 apiece is a large, fast drawdown on a small sample, which is
   also part of why H1's numbers should be trusted less than M15/M30's
   until more weeks are tested.
5. **The BUY side on H1 is a separate, more extreme problem**: 12.5% win
   rate, PF 0.08, -$202 net over just 16 trades. That's a small sample,
   but it's a stark enough split from H1 SELL (39.1% win, PF 0.84) that
   it's worth flagging rather than averaging away -- see the direction
   table below.

### Pooled by timeframe x direction (BUY vs SELL)

| TF | Dir | Trades | Win% | PF | Net $ | AvgR(win) | AvgR(loss) |
|---|---|---|---|---|---|---|---|
| H1 | BUY | 16 | 12.5 | 0.08 | -202.00 | 0.66 | -0.85 |
| H1 | SELL | 46 | 39.1 | 0.84 | -52.54 | 0.94 | -0.70 |
| M15 | BUY | 132 | 28.8 | 0.65 | -218.59 | 1.30 | -0.78 |
| M15 | SELL | 142 | 45.8 | 1.47 | 243.62 | 1.45 | -0.80 |
| M30 | BUY | 61 | 37.7 | 1.14 | 48.77 | 1.57 | -0.74 |
| M30 | SELL | 84 | 39.3 | 1.25 | 109.20 | 1.50 | -0.74 |

M15 and H1 both show a real short-side advantage in this sample; M30 is
close to balanced. Two explanations are both plausible and this data
alone can't distinguish them: (a) a structural asymmetry in how the
regime-channel entry logic generates buy vs. sell signals, or (b) gold
was, net, in a downward-biased regime across enough of these 5 sampled
weeks that shorts were simply more often aligned with the underlying
trend. More weeks (especially weeks with an independently-known uptrend)
would be needed to tell these apart -- flagged as a concrete next step
below, not treated as a settled finding.

### R-multiple distribution (all 481 trades)

| R-multiple bucket | Trades | % of all trades |
|---|---|---|
| < -1.5R | 0 | 0.0% |
| -1.5 to -1R | 157 | 32.6% |
| -1 to -0.5R | 69 | 14.3% |
| -0.5 to 0R | 76 | 15.8% |
| 0 to 0.5R | 53 | 11.0% |
| 0.5 to 1R | 42 | 8.7% |
| 1 to 2R | 44 | 9.1% |
| 2 to 3R | 19 | 4.0% |
| > 3R | 21 | 4.4% |

Reading this: **the single largest bucket (32.6% of all trades) is losses
landing almost exactly at -1R to -1.5R** -- clean, undiluted stop-outs at
close to the original stop distance, with the trailing stop not having
engaged yet. Only 15.8%+14.3%=30% of losing trades were cushioned to
better than -1R by the trailing stop before reversing. On the winning
side, the tail is long: 4.4% of all trades exceeded +3R (these are the
trades where the unconditional ATR trail rode a big move, since the TP
ladder that would otherwise have banked 1R/2R along the way never fires).
That last point is the clearest argument for fixing the TP bug: right now
a winning trade is "all or mostly nothing until the trail eventually
catches up," instead of locking in partial profit at 1R the way the
design intends.

### Worst consecutive-loss streaks (>=4 in a row)

| TF | Week | Consecutive losses | From | To |
|---|---|---|---|---|
| M15 | 2026-06-22_to_2026-06-28 | 10 | 2026-06-25 02:30 | 2026-06-25 13:15 |
| M15 | 2026-07-13_to_2026-07-19 | 8 | 2026-07-13 14:30 | 2026-07-13 23:30 |
| M30 | 2026-07-13_to_2026-07-19 | 8 | 2026-07-16 15:00 | 2026-07-17 04:00 |
| M15 | 2026-08-17_to_2026-08-23 | 6 | 2026-08-17 10:30 | 2026-08-17 13:00 |
| M30 | 2026-06-29_to_2026-07-05 | 6 | 2026-07-02 01:30 | 2026-07-02 10:00 |
| M15 | 2026-06-29_to_2026-07-05 | 4 | 2026-06-29 08:45 | 2026-06-29 10:00 |
| M15 | 2026-07-27_to_2026-08-02 | 4 | 2026-07-28 11:00 | 2026-07-28 13:45 |
| M30 | 2026-06-22_to_2026-06-28 | 4 | 2026-06-22 00:00 | 2026-06-22 01:30 |
| M30 | 2026-07-27_to_2026-08-02 | 4 | 2026-07-27 03:00 | 2026-07-27 10:30 |
| H1 | 2026-06-29_to_2026-07-05 | 4 | 2026-06-29 00:00 | 2026-06-29 10:00 |
| H1 | 2026-07-13_to_2026-07-19 | 4 | 2026-07-15 16:00 | 2026-07-15 19:00 |
| H1 | 2026-08-17_to_2026-08-23 | 4 | 2026-08-17 14:00 | 2026-08-18 02:00 |

M15's Jun 25 stretch (10 losses in under 11 hours) is the single worst
sequence in the whole sample -- worth a closer look at what regime
conditions produced it (all 10 in one calendar day suggests a choppy,
low-conviction session generating repeated false breakouts, which is
exactly the failure mode a session filter or a stricter breakout
confirmation would target).

### Pooled entries by weekday (all 481 trades, all TFs)

| Weekday | Trades | Wins | Win% | Net $ | PF |
|---|---|---|---|---|---|
| Friday | 54 | 24 | 44.4 | 87.74 | 1.44 |
| Monday | 142 | 44 | 31.0 | -257.87 | 0.67 |
| Sunday | 8 | 2 | 25.0 | -42.49 | 0.01 |
| Thursday | 87 | 32 | 36.8 | -99.80 | 0.78 |
| Tuesday | 100 | 34 | 34.0 | -5.94 | 0.99 |
| Wednesday | 90 | 43 | 47.8 | 246.82 | 1.53 |

### Exit-reason confirmation of the min-lot bug

477 stop-loss exits, 4 forced end-of-test closes, **0 TP1/TP2/TP3 exits**
-- out of 481 real trades. Directly confirms the bug via MT5's own tester,
not inference from reading the code.

---

## Diagnosis and recommendations, by aspect

Written for a future data-analysis pass to start from, not just this
session's read -- each item states the specific data behind it so it can
be checked against a larger sample rather than taken on faith.

### 1. Exit / take-profit system -- confirmed broken, highest-confidence fix available
**Finding:** 0 of 481 real trades exited via TP1/TP2/TP3; the entire
partial-close ladder is dead weight at 0.01 lot. Only the independent ATR
trailing stop is doing any profit-protection work.
**Recommendation:** deploy the already-written v1.12 fix (this repo has
it). This is the single highest-confidence improvement available --
it doesn't require guessing at new parameters, it repairs a mechanism
that's supposed to exist and currently doesn't. Re-run this exact journal
methodology against v1.12 once deployed to measure the real effect
(don't assume the effect size without re-testing).

### 2. Position sizing vs. timeframe -- structural risk mismatch on H1
**Finding:** fixed 0.01 lot means dollar risk-per-trade scales with
`ATR(signal timeframe)`, which is why H1 risks ~2x what M15 risks per
trade for a "1R" stop that's logically the same size. This is very
likely the dominant reason H1 underperforms, more than any entry-signal
difference.
**Recommendation:** either (a) restrict this EA to M15/M30 until sizing is
fixed, or (b) turn on `InpUseRiskSizing` (already exists as an input,
currently off in all tested configs) so lot size shrinks automatically on
wider-stop timeframes/instruments, keeping dollar risk per trade roughly
constant regardless of `InpTF`. (b) is the more general fix and should be
tested before writing off H1 entirely -- the entry signal quality on H1
hasn't actually been isolated from the sizing problem yet.

### 3. Direction bias (BUY vs SELL) -- real in-sample split, cause unconfirmed
**Finding:** SELL outperforms BUY on M15 (45.8% vs 28.8% win, PF 1.47 vs
0.65) and H1 (39.1% vs 12.5%); M30 is balanced.
**Recommendation:** don't act on this yet by, e.g., disabling long entries
-- 5 weeks isn't enough to separate "structural signal asymmetry" from
"gold trended down across most of the sampled weeks." Next step: pull
weeks known to be uptrending (check against an independent gold price
chart, not just this EA's own regime state) and see if the split
persists, flips, or disappears.

### 4. Loss streaks / choppy-session vulnerability
**Finding:** 10-loss streak on M15 (Jun 25), several 6-8 streaks
elsewhere, always within a single calendar day. Consistent with the
"midline breakout" entry style (the default, more frequent trigger than
the alternative "band breakout") whipsawing repeatedly in a
low-conviction/ranging session.
**Recommendation:** test `InpUseMidlineBreakout=false` (band breakout
instead -- fewer, more extreme signals) and/or `InpBreakoutConfirmBars=2`
against the same random-week methodology, specifically checking whether
streak length and count drop without a proportional drop in the good
trades. A session filter (`InpUseSessionFilter`, currently off) is
another direct lever worth testing against the specific hours these
streaks clustered in.

### 5. Win rate ceiling (the user's original 85% question)
**Finding:** pooled win rate 37.2% (481 trades), best single-timeframe
pooled figure 38.6% (M30). TP1 sits at exactly 1R -- the same distance as
the stop -- which caps how often a breakout-style entry can "win" before
a full redesign of the exit ladder.
**Recommendation:** treat 85% as off the table for this architecture (see
reasoning already on record from the removed Python journal -- shrinking
TP1 raises win rate only by shrinking each win's size, a trade-off not a
free improvement; worth re-verifying that specific trade-off against the
real MT5 tester before trusting the old numbers again). A credible target
is **PF > 1.3 at 35-45% win rate** -- M30 (pooled PF 1.20, best single
week 2.08) and M15 (pooled PF 1.02, best single week 1.51) are already in
range of that before any changes; H1 is not and shouldn't be the focus
until issue #2 above is addressed.

### 6. Sample size -- everything above needs a bigger batch before being trusted as settled
**Finding:** 5 weeks is enough to surface real signal (e.g., the min-lot
bug, the H1 risk-mismatch) but not enough to treat every number here as
stable -- individual per-run cells range from 4 to 91 trades.
**Recommendation:** the next run of `mt5_journal.py` should widen
`N_WEEKS` substantially (the full 12-week candidate pool is available now;
more will open up as time passes) before drawing final conclusions on the
direction-bias and loss-streak findings specifically.


---

## 2026-09-15 -- v1.13 build, user's exact settings, 4 weeks (Sep 7 + 3 random Aug/Sep weeks)

**Build:** v1.13 (TP-ladder fix, stairstep lock, trailing min step 500 pts,
HUD rewrite). **Settings:** the user's own tester inputs, copied from the
visual-verification run: XAUUSDm, tester chart H1, signal timeframe
`InpTF=M15`, trend filter ON with `InpTrendTF=16385` -- that is PERIOD_H1,
i.e. an **H1 EMA-200** filter (first misreported in chat as H4), midline
breakout, fixed 0.01 lot, SL 1.0xATR, TP 1R/2R/3R, trail 1.5xATR, margin
check 1.2x. $100 deposit, 1:100, real ticks (`Model=4`).

**Weeks:** Sep 7-10 (Mon-Thu, the visual verification run) plus Aug 10-14,
Aug 17-21, Aug 31-Sep 4, drawn with `random.SystemRandom` from the five
remaining full Aug/Sep weeks and printed before any test ran
(`mt5_week_check.py`). Each week starts from a fresh $100. Every trade:
`mt5_weekcheck_v113_trades.csv`.

| Week | Trades | Wins | Losses | Win% | Net $ | PF | End $ | MaxDD% | Avg win $ | Avg loss $ | Worst loss run | Trades/day | SL exits | TP3 exits | Buys/Sells |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Sep 7-10 | 57 | 16 | 41 | 28.1 | -50.93 | 0.80 | 49.07 | 62.5 | 12.79 | -6.23 | 8 | 14.3 | 50 | 7 | 0/57 |
| Aug 10-14 | 62 | 22 | 40 | 35.5 | -52.52 | 0.84 | 46.42 | 75.5 | 12.79 | -8.35 | 7 | 15.5 | 50 | 12 | 62/0 |
| Aug 17-21 | 28 | 8 | 20 | 28.6 | -53.70 | 0.54 | 45.77 | 64.3 | 7.76 | -5.79 | 9 | 14.0 | 26 | 2 | 27/1 |
| Aug 31-Sep 4 | 85 | 32 | 53 | 37.6 | -43.60 | 0.89 | 55.87 | 72.0 | 10.49 | -7.16 | 6 | 17.0 | 75 | 9 | 17/68 |
| **Pooled** | **232** | **78** | **154** | **33.6** | **-200.75** | **0.81** | -- | -- | **11.33** | **-7.04** | -- | **15.5** | **201** | **30** | **106/126** |

("SL exits" includes trailing-stop exits. Pooled End $ / MaxDD / loss run
are omitted because the weeks are separate $100 accounts.)

### Findings

1. **Losing in every week tested (4 of 4).** Win rate 28-38%, PF 0.54-0.89.
2. **The near-identical ~-$50 per week is a margin floor, not a coincidence.**
   A 0.01-lot gold position at ~$4,300-4,450 uses ~$44 margin; with the
   1.2x buffer the EA needs ~$53 free margin to open a trade. Once a $100
   account loses ~$47 it cannot open anything again. From the trade
   timeline: Aug 17-21 dropped below ~$53 on Tue Aug 18 22:04 after 27
   trades and made 1 more trade in the remaining ~74h; Aug 10-14 stopped
   trading Thu Aug 13 18:25 with ~30h left; Sep 7-10 stopped Thu 02:39 with
   ~21h left. Only Aug 31-Sep 4 stayed above the floor and traded to the
   end (and still lost $43.60). So on $100 the weekly loss is capped by
   margin -- the floor limits the damage; it does not hide a recovery.
3. **Below breakeven on the math.** Avg win $11.33 vs avg loss $7.04 means
   breakeven needs ~38.3% wins; actual pooled 33.6%.
4. **Losers are fast, full stop-outs -- the entry signal fires on noise.**
   101 of 154 losers hit roughly the full -1R stop (<= -0.9R); 45 were
   cushioned by the trail; 8 near breakeven. Median loser lasts 23 min;
   61% are stopped within 30 min, 78% within 60 min. Winners hold a
   median 87 min; 41 of 78 reached >= 1R. At ~15 trades/day, the M15
   midline-breakout trigger is overtrading.
5. **Quick re-entry after a loss is common but not the main problem.** 58%
   of post-loss entries came within 15 min; their win rate (32%) is not
   worse than later re-entries (29%).
6. **Time of day (server time), small samples -- a lead, not a conclusion:**

   | Entry block | Trades | Win% | Net $ |
   |---|---|---|---|
   | 00-04h | 65 | 29.2 | -126.1 |
   | 04-08h | 37 | 40.5 | +78.4 |
   | 08-12h | 37 | 21.6 | -73.2 |
   | 12-16h | 54 | 27.8 | -153.1 |
   | 16-20h | 20 | 45.0 | +21.4 |
   | 20-24h | 19 | 63.2 | +51.8 |

7. **No directional flaw.** BUY 106 trades 34.0% win (-$117.4); SELL 126
   trades 33.3% (-$83.3). The H1 trend filter only picks the side --
   Aug 10-14 was all buys, Sep 7-10 all sells.

### Next tests (not yet run)

- **Entry quality first** (targets finding 4): `InpUseMidlineBreakout=false`
  (band breakout), and/or `InpBreakoutConfirmBars=2`, and/or
  `InpRequireTrendFlip=true`. Success = fewer trades/day and fewer <=30-min
  stop-outs without losing the winners.
- **Remove the margin floor from the measurement** (finding 2): rerun the
  same weeks with a $500 deposit (the product page's recommended size) so
  weekly results show the strategy's real P&L instead of stopping at ~-$50.
- **Session filter** (finding 6) only after more weeks -- 19-65 trades per
  block is too thin to pick hours without overfitting.


---

## 2026-09-15 -- v1.14: breakout mode vs new swing-pullback mode, same 4 weeks, $500

**Why:** the 4-week diagnosis above showed the breakout entry overtrading
(~15 trades/day, most losers stopped within 30 min). The user described
their manual method: bias from EMA direction plus higher highs / higher lows
on higher timeframes, pending orders at the previous swing, re-checked every
1-3 hours. v1.14 adds that as `InpEntryMode = ENTRY_SWING_PULLBACK`, using
the user's chosen settings: **2 of 3** timeframes (M30, H1, H4) must agree,
**EMA 50**, entries at **M30** swing points (swing = high/low beyond 2 bars
each side). At every new H1 bar: cancel any unfilled order, re-check bias,
place a limit order at the latest M30 swing low (buy) / high (sell). SL =
swing -/+ 0.3 x ATR(M30); TP1 = opposite M30 swing; TP2/TP3 from the stored
risk; skip if TP1 < 1R. Take-profit ladder, stairstep lock and trailing
unchanged.

**Test:** real MT5 Strategy Tester, real ticks, XAUUSDm, the user's inputs
(`ini_runs/visualcheck_H1_20260907.ini`: H1 chart, `InpTF`=M15, fixed 0.01
lot), full Mon-Fri weeks Aug 10, Aug 17, Aug 31, Sep 7, **$500 deposit** so
the ~$53 margin floor of a $100 account can't cut weeks short. Only
`InpEntryMode` differs. Runner: `mt5_mode_compare.py`; every trade:
`mt5_modecompare_v114_trades.csv`; order-flow counts:
`swing_log_summary.py` over the tester agent log.

| Mode / week | Trades | Wins / Losses | Win% | Net $ | PF | End $ | MaxDD% | Avg win $ | Avg loss $ | Trades/day | Median loser hold |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Breakout Aug 10 | 80 | 28 / 52 | 35.0 | -58.01 | 0.85 | 440.40 | 27.9 | 11.79 | -7.46 | 16.0 | 26 min |
| Swing Aug 10 | 10 | 3 / 7 | 30.0 | +31.46 | 2.31 | 531.46 | 2.3 | 18.46 | -3.42 | 2.0 | 10 min |
| Breakout Aug 17 | 71 | 25 / 46 | 35.2 | +5.52 | 1.02 | 504.46 | 23.2 | 12.49 | -6.67 | 14.2 | 31 min |
| Swing Aug 17 | 5 | 0 / 5 | 0.0 | -16.87 | 0.00 | 483.13 | 3.4 | -- | -3.37 | 1.0 | 6 min |
| Breakout Aug 31 | 85 | 32 / 53 | 37.6 | -43.60 | 0.89 | 455.87 | 23.6 | 10.49 | -7.16 | 17.0 | 20 min |
| Swing Aug 31 | 1 | 0 / 1 | 0.0 | -3.34 | 0.00 | 496.66 | 0.7 | -- | -3.34 | 0.2 | 29 min |
| Breakout Sep 7 | 79 | 26 / 53 | 32.9 | +5.94 | 1.02 | 505.94 | 17.8 | 14.29 | -6.90 | 15.8 | 21 min |
| Swing Sep 7 | 4 | 1 / 3 | 25.0 | +9.65 | 1.87 | 509.65 | 1.4 | 20.72 | -3.69 | 0.8 | 1 min |
| **Breakout, 4 weeks** | **315** | **111 / 204** | **35.2** | **-90.15** | **0.94** | -- | -- | **12.16** | **-7.06** | **15.8** | **25 min** |
| **Swing, 4 weeks** | **20** | **4 / 16** | **20.0** | **+20.90** | **1.38** | -- | -- | **19.03** | **-3.45** | **1.0** | **7 min** |

**Swing-mode order flow** (from the tester log):

| Week | Hourly bias checks | BUY / SELL / WAIT | Orders placed | Filled | Cancelled unfilled | Skips |
|---|---|---|---|---|---|---|
| Aug 10 | 108 | 32 / 11 / 65 | 41 | 10 | 31 | spread 2, R:R 1 |
| Aug 17 | 113 | 36 / 2 / 75 | 38 | 5 | 32 | spread 2 |
| Aug 31 | 112 | 23 / 37 / 52 | 58 | 1 | 56 | spread 3 |
| Sep 7 | 108 | 5 / 22 / 81 | 27 | 4 | 23 | none |
| **Total** | **441** | **96 / 72 / 273** | **164** | **20** | **142** | |

### Findings

1. **The $100 margin floor had distorted the earlier weekly results.** With
   $500, breakout mode's Aug 17 week is +$5.52 (it was -$53.70 on $100, locked
   out from Tuesday) and the full Sep 7 week is +$5.94 (Mon-Thu on $100 was
   -$50.93). Aug 31 never hit the floor and is identical on both deposits
   (-$43.60), which confirms the comparison is like-for-like. Breakout mode
   over 4 weeks: PF 0.94, -$90.15 -- still losing, but close to breakeven
   rather than -50% a week.
2. **Swing mode fixes overtrading.** 1.0 trade/day vs 15.8, and max drawdown
   0.7-3.4% per week vs 17.8-27.9%.
3. **Too few trades to judge swing mode's edge.** 20 trades in 4 weeks. Its
   +$20.90 / PF 1.38 comes almost entirely from one week (Aug 10: +$31.46).
   That is not evidence the strategy works.
4. **The stop is too tight.** 16 of 20 trades lost; the median loser was
   stopped in 7 minutes; avg loss $3.45, i.e. the 0.3 x ATR(M30) buffer
   (about 3-4 price units) below/above the swing. Price routinely wicks
   through a swing by more than that before turning.
5. **Winners are big when they happen.** Avg win $19.03 = 5.5x the avg loss.
   All 20 exits were by stop (initial, stairstep or trailing); 0 reached TP3.
6. **Most orders never fill.** 142 of 164 limit orders (87%) were cancelled
   at the next hourly check; fill rate 12%. Aug 31: 58 placed, 1 filled.
   The hourly cancel-and-replace throws away orders that often sit at the
   same swing price (see repeated prices in the placement log). A visual
   check (swing mode, M5 chart, Sep 1 13:00) showed the other half of the
   problem: after a sharp drop, the latest M30 swing high was 4387.31 while
   price traded near 4340, so the sell limit sat ~47 price units away
   (~11x its stop distance) and could only fill on a full retrace. The
   placement itself was correct -- the order and TP1 (4364.17) sit exactly
   on the M30 swing high and swing low visible on the chart, and the HUD
   showed "Bias M30:down H1:flat H4:down -> SELL" with the pending order.
7. **The bias says WAIT 62% of the time** (273 of 441 checks) with 2-of-3
   agreement.

### Next tests (not yet run)

- **Wider stop buffer:** `InpSwingSLBufferATR` 0.3 -> 0.75 and 1.0 (targets
  finding 4).
- **Keep the order while the plan is unchanged:** only cancel/replace when
  the bias flips or the swing level changes, instead of every hour
  (targets finding 6).
- **Maximum distance from price:** only place the limit when the swing is
  within a set multiple of ATR(M30) from current price; otherwise wait for a
  nearer swing to form (targets the far-away orders in finding 6).
- **More weeks:** all 12 full weeks with tick data (from Jun 22) before
  reading anything into swing mode's PF (finding 3).


---

## 2026-09-15 -- Swing-mode stop buffer and order distance study (v1.14 data)

**Why:** after the v1.14 comparison, the user asked to study the previous trades
before widening swing mode's stop, and approved keeping orders longer and only
using nearby swings (built as v1.15).

**Method:** `study_swing_sl.py`. Inputs: every "Swing: placed" and "Swing bias"
line from the 4 v1.14 swing runs in the tester agent log, the 20 real swing
trades, and real XAUUSDm M1 bars from MT5 (Aug 9 - Sep 11). Orders are replayed
on M1 bars: a buy limit fills when bid low + spread <= entry (the ask reaches
it), a sell limit when bid high >= entry; then stop vs TP1, whichever price
reaches first. A stop and TP1 in the same bar count as a loss, and only the stop
is checked on the fill bar. ATR(M30) at placement is recovered from the logged
risk (risk = 0.3 x ATR). Dollars at 0.01 lot (1 price unit = $1). "Kept" orders
merge consecutive placements with the same direction and entry price into one
order that lives until the bias flips or the level changes -- an approximation
of v1.15's rule.

**Calibration:** replaying the 164 as-run orders (each living one hour) finds
**20 fills -- exactly the 20 trades the tester made.**

### 1. Real trades: would a wider stop have kept the losers alive?

"Against before TP1" = the furthest price moved against the trade (in ATR M30)
before it reached TP1, or before the week ended if it never did.

| Week | Entry time | Dir | Entry | P/L $ | Held (min) | Against before TP1 (ATR) | Later hit TP1 | Hours to TP1 |
|---|---|---|---|---|---|---|---|---|
| Aug 10 | 08-10 00:00 | BUY | 4332.71 | +3.06 | 33.6 | 1.73 | yes | 5.8 |
| Aug 10 | 08-10 13:58 | BUY | 4317.37 | +32.09 | 153.1 | 0.09 | yes | 2.1 |
| Aug 10 | 08-11 04:49 | BUY | 4407.78 | -3.79 | 6.2 | 4.18 | yes | 31.9 |
| Aug 10 | 08-11 05:00 | BUY | 4407.83 | -4.04 | 5.0 | 3.81 | yes | 31.7 |
| Aug 10 | 08-11 16:04 | BUY | 4381.07 | -3.73 | 87.6 | 1.77 | yes | 10.2 |
| Aug 10 | 08-12 12:10 | BUY | 4406.86 | +20.24 | 19.1 | 0.22 | yes | 0.3 |
| Aug 10 | 08-13 04:00 | BUY | 4398.11 | -3.76 | 10.1 | 7.00 | no | -- |
| Aug 10 | 08-13 05:01 | BUY | 4396.01 | -0.48 | 31.1 | 6.71 | no | -- |
| Aug 10 | 08-14 05:51 | SELL | 4328.12 | -3.59 | 4.7 | 5.79 | no | -- |
| Aug 10 | 08-14 17:42 | BUY | 4378.64 | -4.54 | 62.8 | 0.65 | no | -- |
| Aug 17 | 08-18 01:45 | BUY | 4409.72 | -2.71 | 1.8 | 9.37 | yes | 35.1 |
| Aug 17 | 08-18 02:33 | BUY | 4397.77 | -3.02 | 6.7 | 7.16 | yes | 34.3 |
| Aug 17 | 08-18 03:17 | BUY | 4397.81 | -3.04 | 6.4 | 7.31 | yes | 33.6 |
| Aug 17 | 08-21 12:32 | BUY | 4577.75 | -3.99 | 2.7 | 1.09 | yes | 1.9 |
| Aug 17 | 08-21 13:00 | BUY | 4577.82 | -4.11 | 34.9 | 0.34 | yes | 2.4 |
| Aug 31 | 09-02 11:35 | SELL | 4331.72 | -3.34 | 29.2 | 17.37 | no | -- |
| Sep 7 | 09-07 08:02 | SELL | 4413.46 | -3.63 | 1.0 | 0.88 | yes | 3.5 |
| Sep 7 | 09-07 09:01 | SELL | 4413.40 | +20.72 | 188.8 | 0.05 | yes | 2.5 |
| Sep 7 | 09-08 05:29 | BUY | 4421.06 | -3.47 | 26.4 | 11.31 | no | -- |
| Sep 7 | 09-09 15:05 | BUY | 4390.66 | -3.97 | 0.1 | 1.16 | yes | 14.9 |

16 losers; 10 of them reached TP1 later. The buffer each would have needed:
0.34, 0.88, 1.09, 1.16, 1.77, 3.81, 4.18, 7.16, 7.31, 9.37 ATR. A ~1.2 ATR stop
would have saved 4 of the 16; the other 6 went 3.8-9.4 ATR against the trade
first and took ~30-35 hours to reach TP1 -- not realistically holdable.

### 2. Stop-buffer replay (kept orders: 59 distinct, 25 filled)

| Buffer (x ATR) | Trades | Skipped by R:R | Wins | Losses | Still open | Win% | Avg win $ | Avg loss $ | Net $ | Per trade $ | Median minutes to stop |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.30 | 25 | 0 | 2 | 22 | 1 | 8.0 | 31.03 | -3.38 | **+38.61** | +1.54 | 7 |
| 0.50 | 25 | 0 | 2 | 22 | 1 | 8.0 | 31.03 | -5.63 | -10.94 | -0.44 | 23 |
| 0.75 | 25 | 0 | 2 | 21 | 2 | 8.0 | 31.03 | -8.43 | -66.90 | -2.68 | 43 |
| 1.00 | 25 | 0 | 3 | 20 | 2 | 12.0 | 28.66 | -11.18 | -89.51 | -3.58 | 46 |
| 1.25 | 25 | 0 | 4 | 19 | 2 | 16.0 | 27.52 | -13.84 | -104.71 | -4.19 | 89 |
| 1.50 | 23 | 2 | 5 | 16 | 2 | 21.7 | 26.94 | -16.58 | -82.46 | -3.59 | 100 |
| 2.00 | 13 | 12 | 1 | 11 | 1 | 7.7 | 44.67 | -21.89 | -145.26 | -11.17 | 111 |
| 3.00 | 11 | 14 | 1 | 8 | 2 | 9.1 | 44.67 | -31.84 | -170.81 | -15.53 | 358 |

**Conclusion: a wider stop loses more money in this sample.** Wins barely
increase (2 of 25 at 0.3, 3 at 1.0, 5 at 1.5) while every loss grows with the
buffer. The stop stays at 0.3 x ATR. Caveats: 25 trades is small, and the replay
counts a win as reaching TP1 -- the real EA can earn more after TP1 through the
stairstep lock and trailing stop.

### 3. Distance from price when placed vs fill rate

| Distance (ATR M30) | As run (order lives 1 h): orders | filled | fill% | Kept orders: orders | filled | fill% |
|---|---|---|---|---|---|---|
| 0-1 | 29 | 13 | 44.8 | 15 | 9 | 60.0 |
| 1-2 | 56 | 4 | 7.1 | 30 | 12 | 40.0 |
| 2-3 | 30 | 3 | 10.0 | 13 | 4 | 30.8 |
| 3-4 | 33 | 0 | 0.0 | 0 | 0 | -- |
| 4-6 | 15 | 0 | 0.0 | 1 | 0 | 0.0 |
| 6-10 | 1 | 0 | 0.0 | 0 | 0 | -- |

**Conclusion:** orders 3+ ATR from price never filled (0 of 49 as run). Keeping
orders raises the fill rate at every distance (1-2 ATR: 7% -> 40%). v1.15 sets
`InpSwingMaxDistATR = 3.0` and keeps orders until the bias flips, the level
changes, or price moves beyond that distance.


---

## 2026-09-15 -- v1.15 swing mode vs breakout mode, all 12 weeks, $500

**Build:** v1.15 -- swing mode keeps its pending order across hourly checks and
cancels it only when the bias flips, the swing level changes, or price moves more
than 3 x ATR(M30) away; new orders only use swings within 3 x ATR. Stop buffer
kept at 0.3 x ATR (see the study above).

**Test:** `WEEKS=12 TAG=v115 python mt5_mode_compare.py` -- real MT5 Strategy
Tester, real ticks, XAUUSDm, the user's inputs (H1 chart, `InpTF`=M15, fixed
0.01 lot), every full Mon-Fri week with tick data from Jun 22 to Sep 11,
**$500 deposit**, only `InpEntryMode` differs. Every trade:
`mt5_modecompare_v115_12wk_trades.csv`. Order flow: `swing_log_summary.py`
(the runs are in tester agent Agent-127.0.0.1-3001's log -- MT5 switched agents
mid-session after the first agent's log reached 172 MB).

| Week | Breakout trades | Breakout net $ | Breakout PF | Breakout max DD% | Swing trades | Swing net $ | Swing PF | Swing max DD% |
|---|---|---|---|---|---|---|---|---|
| Jun 22 | 82 | +64.36 | 1.15 | 16.7 | 5 | -0.07 | 1.00 | 2.4 |
| Jun 29 | 71 | +43.49 | 1.14 | 19.7 | 6 | +17.52 | 2.79 | 1.0 |
| Jul 6 | 82 | -222.05 | 0.48 | 50.0 | 7 | -14.21 | 0.30 | 2.8 |
| Jul 13 | 79 | +61.65 | 1.20 | 19.5 | 8 | +1.74 | 1.10 | 2.0 |
| Jul 20 | 87 | -150.14 | 0.57 | 31.6 | 4 | -11.29 | 0.00 | 2.3 |
| Jul 27 | 72 | -92.64 | 0.68 | 26.4 | 9 | -10.80 | 0.54 | 4.6 |
| Aug 3 | 78 | +100.84 | 1.29 | 15.2 | 4 | -9.24 | 0.00 | 1.9 |
| Aug 10 | 80 | -58.01 | 0.85 | 27.9 | 10 | +9.68 | 1.37 | 4.8 |
| Aug 17 | 71 | +5.52 | 1.02 | 23.2 | 6 | -19.98 | 0.00 | 4.0 |
| Aug 24 | 77 | -15.54 | 0.96 | 23.2 | 8 | -19.78 | 0.15 | 4.1 |
| Aug 31 | 85 | -43.60 | 0.89 | 23.6 | 3 | -2.93 | 0.55 | 0.7 |
| Sep 7 | 79 | +5.94 | 1.02 | 17.8 | 7 | +3.56 | 1.21 | 2.6 |

| 12 weeks | Trades | Trades/day | Win% | Net $ | PF | Avg win $ | Avg loss $ | Weeks + / - | Median loser hold |
|---|---|---|---|---|---|---|---|---|---|
| Breakout | 943 | 15.7 | 34.4 | -300.18 | 0.93 | 12.34 | -6.94 | 6 / 6 | 29 min |
| Swing v1.15 | 77 | 1.3 | 19.5 | -55.80 | 0.72 | 9.66 | -3.24 | 4 / 8 | 5 min |

**Swing v1.15 order flow (12 weeks):** 1,310 hourly bias checks -> BUY 231, SELL
193, WAIT 886 (68%). 200 orders placed, kept at a check 259 times, **77 filled**,
119 cancelled unfilled (swing level changed 64, too far from price 54, bias
flipped 1). Skips: swing too far 75, spread too wide 18, reward < 1R 5. Fill
rate 38.5% (v1.14: 12%).

### Findings

1. **Both modes lose over 12 weeks.** Breakout: PF 0.93, -$300.18, with swings
   from +$100.84 to -$222.05 a week and up to 50% drawdown. Swing: PF 0.72,
   -$55.80, but never more than 4.8% drawdown in a week.
2. **v1.14's +$20.90 on 4 weeks did not hold.** On those same 4 weeks v1.15 made
   -$9.67. Matching trades: v1.15 took 16 of v1.14's 20 trades with about the
   same result (+$9.42 vs +$7.91), missed 4 worth +$12.99 (including a +$20.24
   winner), and added 10 trades from orders kept open longer that netted -$19.09
   (1 winner). Keeping orders raised fills, but the extra fills mostly lost.
3. **The order handling itself behaves as designed** (259 keeps, 119 cancels
   with logged reasons, fill rate 12% -> 38.5%).
4. **The entry is the weak point.** 62 of 77 swing trades lost; 55 of them lost
   about the full 1R, the median loser lasted 5 minutes, and 34 were stopped
   within 5 minutes of filling. The limit order fills while price is pushing
   through the swing, not bouncing off it -- and the study above showed a wider
   stop only makes each of those losses bigger.
5. **Winners still exist but are smaller than in v1.14:** 15 winners, avg $9.66
   (v1.14: $19.03), 4 of them below 1R; 0 reached TP3.

### Next test (not yet run)

- **Confirmation entry instead of a blind limit order**, closer to the user's
  final step ("go back to 5 mins and find where to enter"): when price reaches
  the swing zone, wait for an M5 candle to close back on the bias side of the
  level (a rejection) before entering, with the stop beyond that candle's wick.
  Aimed at finding 4: the 34 trades stopped within 5 minutes.


---

## 2026-09-15 -- Pro trader review, round 1: data split and pre-registrations

Full review: `reviews/2026-09-15-pro-trader-review.md`.

**Data split, fixed before any run in this round:**
- In-sample (IS): the 12 full weeks Jun 22 - Sep 11, 2026 (already seen many times).
- Validation: the 12 weeks Mar 2 - May 22, 2026 (never analyzed). Only for
  candidates that pass IS.
- Holdout: the 8 weeks Jan 5 - Feb 27, 2026. Touched only by a 2-day
  data-availability run (Jan 5-7) earlier today, no strategy analysis. Run only
  for a candidate that also passes validation.

**Settings for every run:** real ticks (`Model=4`), $500 at the start of each
week, fixed 0.01 lot, the user's inputs (`ini_runs/visualcheck_H1_20260907.ini`),
build v1.16 with new inputs at their defaults unless stated.

**Multiple testing:** at least 5 ideas were already tried on the IS weeks (v1.14
swing mode, stop buffer, order distance, kept orders, session/weekday split), so
the IS bar is raised from PF 1.15 to **PF >= 1.25**.

**Default-behavior check:** v1.16 with default inputs must reproduce the stored
v1.15 trades (`mt5_modecompare_v115_12wk_trades.csv`) on 2 IS weeks (Jun 22,
Jul 6) in both modes before the stored 12-week baseline is used.

### Experiment E1 -- swing confirmation entry, sweep and reclaim (pre-registered 2026-09-15)
- **Hypothesis:** swing-mode limit orders fill while price pushes through the
  swing (v1.15 IS: 56 of 77 trades hit the initial stop after a median 3.9 min,
  -$190.63). Waiting until price sweeps the swing and an M5 candle closes back on
  the bias side filters out the pushes that keep going. It is the user's own
  last step: go back to M5 to find the entry.
- **Change:** `InpSwingEntryStyle=1` (new; default 0 = v1.15 limit orders). Same
  bias, same swing level and keep/cancel rules, but the level is "armed" instead
  of getting a limit order. On each closed M5 bar: once price has traded beyond
  the level (the sweep), the first M5 close back on the bias side enters at
  market. SL = the most extreme price of the sweep -/+ `InpSwingSLBufferATR`
  (0.3) x ATR(M30); TP1 = the planned opposite swing; skipped if TP1 <
  `InpSwingMinRR` (1.0) x risk. The setup is dropped if the sweep goes more than
  `InpSwingSweepMaxATR` (1.0, fixed, not tuned) x ATR(M30) beyond the level.
  Spread/session/margin filters are checked at entry. TP ladder, stairstep lock
  and trailing unchanged.
- **Baseline:** v1.15 swing, IS 12 weeks: 77 trades, PF 0.72, -$55.80, 4 of 12
  weeks positive, worst weekly DD 4.8%.
- **Weeks:** IS; validation only if promoted; holdout untouched.
- **Primary metric:** pooled IS net $ and PF.
- **Pass (promote to validation):** PF >= 1.25 and net > 0; better than the
  baseline's net in >= 8 of 12 weeks; worst weekly DD <= 6.0%; >= 80 trades. If
  it has < 80 trades but passes everything else, the sample is too small to
  judge: run validation and require validation PF >= 1.10 with >= 80 trades
  pooled over IS + validation.
- **Specific target:** losers stopped within 5 minutes fall by at least a third
  (baseline 34 of 62 losers, 55%).
- **Falsified if:** PF < 1.0, or fast stop-outs don't fall.

### Experiment E2 -- closed-bar regime flip for breakout mode (pre-registered 2026-09-15)
- **Hypothesis:** breakout mode's signal is the first tick of each M15 bar vs the
  previous close (verified), a near-random entry in the H1 EMA200 direction. Its
  loss (-$300.18 on 943 trades) is about the spread paid (943 x $0.26 = $245).
  Entering only when the ATR regime channel (ATR 14 x 2.0, SuperTrend-style)
  flips on a closed M15 bar in the H1 EMA200 direction -- a pullback against the
  higher-timeframe trend has ended -- should cut trades by more than 70% and give
  entries that carry information.
- **Change:** `InpBreakoutClosedBar=true` (new; default false = v1.15) with the
  existing `InpUseMidlineBreakout=false` and `InpRequireTrendFlip=true`, so the
  signal is the closed-bar channel flip. The channel is rebuilt from the last 300
  closed M15 bars at every bar. Stop, TP ladder, stairstep lock, trailing and
  trend filter unchanged. (A closed-bar midline cross is also implemented but not
  tested: a bar closing above its own midpoint is still close to random.)
- **Baseline:** v1.15 breakout, IS 12 weeks: 943 trades, PF 0.93, -$300.18, 6 of
  12 weeks positive, worst weekly DD 50.0%.
- **Weeks / primary metric:** as E1.
- **Pass:** PF >= 1.25 and net > 0; better than baseline net in >= 8 of 12 weeks;
  worst weekly DD <= 62.5%; >= 80 trades.
- **Specific target:** <= 5 trades/day.
- **Falsified if:** PF stays <= 1.0 with far fewer trades -- then the loss is not
  only overtrading, and the M15 regime flip has no edge on its own.

### Checks before the experiments (2026-09-15)
- **Default behavior:** v1.16 with default inputs reproduced the stored v1.15 trades exactly
  (entry/exit times, prices, P/L) on Jun 22 and Jul 6 in both modes: breakout 82 + 82 trades
  (+$64.36, -$222.05), swing 5 + 7 trades (-$0.07, -$14.21). The stored 12-week v1.15 results
  are the baseline for E1 and E2.
- **Hedging account (code audit):** a harness build opened a manual SELL (magic 777) before the
  EA traded, Jun 23-24. v1.15: the manual position was never modified or closed, but all 22 EA
  SELL positions got its TP copied onto them, ~4,300 stop modifications were sent and 13 were
  rejected as invalid stops (`MoveSLto()` read the position via `PositionSelect(symbol)`).
  v1.16: 0 copied TPs, 0 failed modifications, same 36 EA entries.
- **Orders without a stop:** 0 of 6,570 logged entries (`sl=0.00`) and 0 of 2,068 stored trades.
- **Small-account capture:** 0 captures in every $100 run (50% of 0.01 lot rounds to 0).
- **Smoke tests (Aug 10, 1 week each):** the tester log showed the overrides applied and the new
  logic running (E1: 19 levels armed, 8 sweeps, 5 entries; E2: 452 closed-bar evaluations, 9
  entries). One week, not evidence.

### E1 result -- swing confirmation entry, IS 12 weeks: FAILED promotion
Tester log: all 12 runs show `InpEntryMode=1 InpSwingEntryStyle=1 InpSwingSweepMaxATR=1.0`, a
ticks line and a final balance. Trades: `review-scratch` batch E1is (summarized here).

| 12 weeks IS | Trades | Win% | Net $ | PF | Avg win / loss $ | Weeks + | Better than baseline | Worst weekly DD | Losers stopped <= 5 min | Median loser hold |
|---|---|---|---|---|---|---|---|---|---|---|
| Baseline swing v1.15 | 77 | 19.5 | -55.80 | 0.72 | 9.66 / -3.24 | 4 | -- | 4.8% | 34 of 62 (55%) | 4.6 min |
| E1 confirm entry | 56 | 33.9 | +2.30 | 1.01 | 11.57 / -5.88 | 5 | 6 of 12 | 5.3% | 4 of 37 (11%) | 34.8 min |

Weekly net $ (Jun 22 ... Sep 7): -19.64, +10.72, -9.08, +13.31, -7.21, -15.32, +8.46, +8.41,
-11.22, +49.97, -14.00, -12.10. Flow over 12 weeks: 191 levels armed, 71 sweeps, 56 entries,
13 dropped as too deep, 2 skipped for reward < 1R.

- The mechanism works as intended: fast stop-outs fell from 55% to 11% of losers, win rate rose
  from 19.5% to 33.9%, and the pooled result went from -$55.80 to +$2.30.
- But the stop is now beyond the sweep (average risk $8.09 vs $3.49), so avg loss doubled, and
  there is no edge: PF 1.01, expectancy +$0.04/trade, better than baseline in only 6 of 12 weeks,
  and +$49.97 of the profit comes from one week (Aug 24). Criteria failed: trades (56 < 80),
  PF (< 1.25), weeks better (6 < 8). Not falsified (PF >= 1.0), but not promoted.
- No session pattern to act on: Asia 21 trades PF 0.90, London 17 PF 0.88, overlap 11 PF 1.03,
  NY afternoon 6 PF 1.78.

### E2 result -- closed-bar regime flip (breakout mode), IS 12 weeks: FAILED promotion
Tester log: all 12 runs show `InpBreakoutClosedBar=true InpUseMidlineBreakout=false
InpRequireTrendFlip=true`, closed-bar evaluations on every M15 bar and a ticks line.

| 12 weeks IS | Trades | Trades/day | Win% | Net $ | PF | Avg win / loss $ | Weeks + | Better than baseline | Worst weekly DD |
|---|---|---|---|---|---|---|---|---|---|
| Baseline breakout v1.15 | 943 | 15.7 | 34.4 | -300.18 | 0.93 | 12.34 / -6.94 | 6 | -- | 50.0% |
| E2 closed-bar flip | 124 | 2.1 | 36.3 | +6.88 | 1.01 | 12.01 / -6.75 | 7 | 7 of 12 | 12.3% |

Weekly net $: +3.91, +18.52, -61.52, -37.40, +5.95, -39.26, +22.97, +99.61, +12.45, +23.18,
-22.48, -19.05. Exits: 48 initial stops -$420.46, 20 TP3 closes +$433.03, 56 trailed/locked
exits -$5.69.

- Trades fell 87% (target met: 2.1/day), the weekly drawdown fell from 50% to 12.3%, and the
  -$300 loss disappeared -- roughly the spread no longer paid.
- The entries still carry no edge: PF 1.01, win rate and payoff almost identical to the random
  baseline (36.3% vs 34.4%; avg win/loss 1.78 vs 1.78). Aug 10 alone made +$99.61 (the 1-week
  smoke result was that week). Criteria failed: PF (< 1.25), weeks better (7 < 8).
- Consistent with the hypothesis's falsification branch: the loss was overtrading, and the M15
  regime flip on its own has no edge.

### E3 -- not run (screening said no)
Candidate: take the E2 regime flip only when the swing-mode M30/H1/H4 bias agrees (the user's
top-down method applied to the breakout trigger). **Screening only, not evidence:** the 124 real
E2 trades split by the hourly bias logged in the E1 runs (same weeks; ignores that skipped trades
could free time for others): bias agrees 23 trades, PF 1.05, +$4.29; bias WAIT 90 trades, PF
1.09, +$35.87; bias against 11 trades, PF 0.40, -$33.28. A bias-aligned version would have ~23
trades in 12 weeks and no sign of edge; dropping only the 11 "against" trades would be fitting
noise. With ~8 ideas now tried on these weeks, no third tester experiment was run this round.

### Round conclusion
- Promoted: none. Validation weeks (Mar 2 - May 22) and the holdout (Jan 5 - Feb 27) remain
  unused for strategy decisions.
- Ideas tried on the IS weeks so far: ~8 (v1.14 swing, stop buffer, order distance, kept orders,
  session/weekday split, E1, E2, E3 screen). The next round needs a clear prior reason and a
  higher IS bar, or new data.
- Kept in the code, default off: `InpSwingEntryStyle`, `InpSwingSweepMaxATR`,
  `InpBreakoutClosedBar`. Kept and verified: the hedging `MoveSLto()` fix.
- Trades: `mt5_review_E1E2_12wk_trades.csv` (mode `swing_confirm_E1` / `breakout_closedbar_E2`).


---

## 2026-09-15 -- Review round 2: user-approved defaults (v1.17) and exit/session experiments

Report: `reviews/2026-09-15-pro-trader-review-round2.md`.

**User's answers to round 1:** no manual trading on the EA's account; 1% risk per trade; a
"moving" 10% weekly drawdown limit, read as *no new entries while equity is 10% or more below
its highest value of the last 7 days (rolling); open trades keep their stops; entries resume when
equity is back inside the limit* (an assumption); trading hours 10:00-14:00, 15:00-17:00 and
19:00-21:00 at UTC+4 = **06:00-10:00, 11:00-13:00, 15:00-17:00 UTC** (server time) all year;
swing mode as default; no news filter this round (future: reduced risk around FOMC/NFP/CPI);
exit management to be decided on evidence; fix the stop-modify flood while the market is
closed; commits stay local.

**Approved defaults in v1.17 (risk controls, not a claim of edge):** `InpEntryMode` = swing;
`InpUseRiskSizing=true`, `InpRiskPercent=1.0` (lot floored to the 0.01 step, so risk never exceeds
1% unless it had to be raised to the 0.01 minimum; then the trade is skipped if that minimum lot
risks more than `InpMaxRiskPercent=1.5`%); equity guard `InpUseEquityGuard=true`, 10%, 7 days
(cancels pending orders and armed levels while active); `InpThrottleClosedMarket=true`.

**My choice: swing entry style = confirmation entry (E1) as default.** Round 1, same 12 weeks:
limit orders 77 trades, -0.23R per trade, 55% of losers stopped within 5 min; confirmation 56
trades, +0.02R per trade, 11%. Neither passed, but the confirmation entry is the better-behaved
one, it is the user's own M5 step, and its entry happens at one moment, which makes the session
rule in X2 clean.

**Test conditions for this round:** the user's ini plus `InpUseRiskSizing=true` (the ini sets it
false explicitly), real ticks, **$5,000 at the start of each week**. Why not $500: at $500, 1% is
$5 and XAUUSDm's 0.01 minimum lot moves $1 per 1.00, so sizing is coarse (0.01 or 0.02 lots),
partial closes at TP1/TP2 are impossible below 0.04 lots, and confirmation-entry stops above
$7.50 would be skipped. At $5,000 the lot is accurate to a few percent and the TP ladder works
as designed; results in R apply to any account where 1% is implementable, and $ are ~$50 per R.
How many trades a $500 / $1,000 account would skip is computed from B2's stop distances.
Weeks: IS Jun 22 - Sep 11 (12); validation Mar 2 - May 22 (12, unused); holdout Jan 5 - Feb 27
(8, unused; Jan 5-7 is also used for the market-closed request count, which is not a strategy
test). Each week is a separate test, so the rolling guard only sees that week's equity.

**Multiple testing:** 8 ideas were tried on the IS weeks before this round; X1a, X1b, X1c and X2
make 12. **Sample size:** the confirmation entry made 56 trades in 12 weeks and X2 will have
roughly a third of that -- below the protocol's 80. Judged in R, with a paired comparison where
entries are shared; nothing in this round can establish an edge on its own.

**Checks before the experiments:** (1) v1.17 with v1.16-equivalent inputs (sizing off, limit
entry, guard off, throttle on) must reproduce the stored v1.15 trades on Jul 6, both modes;
(2) Jan 5-7 breakout run (the one with 7,811 rejected modifies) with the throttle off vs on:
rejected-request count, and trades must be identical.

**B2 (new baseline):** v1.17 defaults -- swing mode, confirmation entry, 1% sizing (max 1.5%),
equity guard, throttle, exit rule 0 (stop to the TP1 price at TP1, to the TP2 price at TP2), ATR
trail 1.5 x ATR(M15), around the clock.

### Experiment X1 -- exit management (pre-registered 2026-09-15)
Three variants on B2's entries; only the exit changes.
- **X1a** `InpExitAtTP1=1`: at TP1 stop to breakeven + spread, at TP2 to the TP1 price; ATR(M15)
  trail unchanged. Hypothesis: the stop at the TP1 price sits at the market the moment TP1 is
  touched, so any retest closes the rest; breakeven lets the trade survive the retest.
- **X1b** `InpExitAtTP1=2`: from TP1 on, the stop follows the last closed M15 swing (strength 2)
  -/+ spread, checked at TP1 and on every new M15 bar, never loosened; no ATR trailing; before TP1
  only the initial stop. Hypothesis: a structure trail exits on real reversals and lets winners
  reach TP2/TP3, where ATR(M15) x 1.5 exits on normal pullbacks.
- **X1c** `InpTrailATRTF=30`: exit rule 0 with the trail at 1.5 x ATR(M30) (the planning
  timeframe) instead of M15. Hypothesis: fewer premature trail exits on M30-planned trades.
- **Metrics:** paired R on trades with the same entry time and direction as B2 (entries stay
  identical until a different exit changes when the next trade can start); total R, average R;
  $ net and PF at 1%; weekly R; worst weekly drawdown.
- **Clear IS pass (-> validation):** paired mean dR >= +0.10R per trade with t >= 2.4 (Bonferroni
  over 3 variants); total R >= B2; weekly R >= B2 in >= 7 of 12 weeks; worst weekly DD <= 1.25 x
  B2. Absolute PF is reported but not required (exits are compared on the same entries).
- **Validation pass:** paired mean dR > 0 and at least half the IS value; total R >= B2.
  Holdout, only then: paired mean dR > 0 and total R >= B2.
- **Falsified if:** mean dR <= 0.
- **Default:** a variant becomes the default only after passing validation (and holdout);
  otherwise exit rule 0 and the M15 trail stay, with the variants behind inputs.

### Experiment X2 -- the user's trade windows (pre-registered 2026-09-15)
- **Change:** `InpUseTradeWindows=true`, `InpTradeWindows=06:00-10:00,11:00-13:00,15:00-17:00`
  (server time = UTC, start inclusive, end exclusive).
- **Rule:** bias checks, arming and sweep tracking continue around the clock; the entry is taken
  only if the confirmation (the first tick after the M5 confirmation bar closes) falls inside a
  window, otherwise the setup is dropped and can be re-armed at the next hourly check. (For the
  limit-order style, not tested: orders are placed only inside a window and cancelled at the first
  tick outside, so fills can only happen inside.) Why: the user only takes entries while at the
  screen in those hours; a setup that completes outside them is one they would not trade.
- **Hypothesis:** entries in the user's hours (London morning, pre-New York, New York open) are
  better than Asia and late-US entries.
- **Clear IS pass:** total R >= B2's; average R >= B2's + 0.15R; PF in R >= 1.25; weekly R >= B2 in
  >= 7 of 12 weeks; worst weekly DD <= 1.25 x B2; and B2's trades outside the windows have mean
  R < 0. With ~20 trades this can at best justify a validation run.
- **Validation pass:** total R >= B2 and average R >= B2's + 0.075R.
- **Falsified if:** X2's average R <= B2's.
- **Default:** trade windows are switched on by default only if X2 passes validation (and
  holdout); otherwise around the clock stays, with the windows behind the input.

### Round 2 checks (results)
- **Regression:** v1.17 with v1.16-equivalent inputs reproduced the stored v1.15 trades exactly on
  Jul 6 (breakout 82 trades -$222.05, swing 7 trades -$14.21).
- **Market-closed fix:** Jan 5-7 breakout run with the user's inputs: `InpThrottleClosedMarket=false`
  7,811 rejected "Market closed" stop modifications, `=true` 0. Trades identical (28, +$81.63, final
  balance $581.63 in both).
- **Parser:** identical output to the stored CSV on the 0.01-lot Jul 6 reports. First parse of the
  $5,000 runs showed a bug -- balances of $1,000+ are written as "5 080.46" and became NaN (weekly
  drawdown read 0%); fixed and all round-2 reports re-parsed.
- **Every IS batch** (B2, X1a, X1b, X1c, X2): 12 runs, the intended inputs in each tester log, a ticks
  line per week. Sizing at $5,000: 0.02-0.14 lots, 0.68-1.04% of the week's starting balance
  (equity at entry can be higher), 0 trades skipped by the 1.5% cap, 0 equity-guard activations in
  any round-2 run (worst weekly closed-balance drawdown 4.6%).
- **Equity guard, functional test** (Jun 22 week, B2 with the guard set to 1% / 1 day so it must
  fire): paused at 15:04 on Jun 22 (equity $5,022.44 vs 1-day peak $5,073.55), 46 hourly checks
  skipped planning, 3 entries instead of B2's 5, resumed on Jun 26 once the old peak left the
  window. It flapped: with a trade open, equity crossed the limit on tick after tick (76 pause + 76
  resume log lines). Fixed by logging at most one line per minute with a count of the unlogged
  crossings; the guard state itself is unchanged. Re-run: same 3 trades and $5,025.87, 14 log lines.
- **1.5% cap, functional test** (same week at $500): all 5 setups skipped with a log line each
  (0.01 lot would have risked 1.59%-3.45%); 0 trades. The parser crashed on the zero-trade report;
  fixed.
- **Small accounts (from B2's 56 stop distances, median 7.19, range 3.44-17.23):** at $500 the 0.01
  minimum lot would be needed for 43 trades and 26 would be skipped (> 1.5%); at $1,000, 5 skipped;
  at $2,000, none.

### B2 result (v1.17 defaults, IS 12 weeks, $5,000/week, 1% risk)
56 trades (the same 56 entries as E1), win 33.9%, **+3.37R total, +0.060R per trade, PF 1.12 in R;
+$115.35, PF 1.09 in $**, 6 of 12 weeks positive, worst weekly drawdown 4.0%. Weekly R: -1.74,
+1.87, -2.48, +3.04, -1.01, -2.25, +0.57, +5.29, -2.51, +2.72, -1.48, +1.34. Six trades took a
partial close at TP1. Inside the user's windows B2 made -3.20R on 24 trades; outside +6.57R on 32.

### X1 results -- exits (IS): none is a clear pass; no validation run

| Run | Trades | Win% | Total R | Avg R | PF (R) | Net $ | PF ($) | Weeks R >= B2 | Paired dR per trade (t) | Better / worse / same | Worst week DD |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B2 stop to TP1 price, ATR(M15) trail | 56 | 33.9 | +3.37 | +0.060 | 1.12 | +115.35 | 1.09 | -- | -- | -- | 4.0% |
| X1a breakeven + spread at TP1 | 56 | 33.9 | +2.62 | +0.047 | 1.09 | +77.96 | 1.06 | 11/12 | -0.013 (t -1.00) | 0 / 1 / 55 | 4.0% |
| X1b M15 structure trail after TP1 | 55 | 30.9 | +19.27 | +0.350 | 1.52 | +951.71 | 1.55 | 4/12 | +0.153 (t +0.63) | 13 / 26 / 15 | 4.6% |
| X1c ATR trail on M30 | 57 | 38.6 | +18.92 | +0.332 | 1.60 | +901.36 | 1.60 | 6/12 | +0.179 (t +1.12) | 11 / 26 / 19 | 4.1% |

- **X1a: rejected (falsified, dR <= 0).** Only 1 of 56 trades changed: TP1 (the opposite swing) is
  rarely reached before the ATR trail has already pulled the stop past breakeven.
- **X1b: not a clear pass.** +15.9R more than B2, but from three trending weeks (Jun 29 +11.65R,
  Aug 10 +13.52R, Aug 24 +14.52R = +39.69R); the other nine weeks lost 20.41R (B2 in those nine
  weeks: -6.51R). 26 trades worse, 13 better. t = 0.63 against 2.4 required; weeks better 4 < 7.
- **X1c: not a clear pass.** +15.6R more than B2, mostly Aug 10 (+14.34R) and Aug 24 (+12.34R);
  the other ten weeks -7.77R (B2 there: -4.64R). t = 1.12 < 2.4; weeks better 6 < 7.
- Reading: a looser trail (M30 ATR or M15 structure) gives back more on most trades and catches the
  occasional trend leg much better. In 12 weeks that is two or three trends -- not enough to tell a
  real effect from luck, and in the choppy weeks it costs. **Exit decision: keep the TP1-price
  stairstep and the 1.5 x ATR(M15) trail as default;** X1b/X1c stay behind `InpExitAtTP1` /
  `InpTrailATRTF`. The best-supported next step is a single pre-registered confirmatory run of X1c
  on the unused validation weeks.

### X2 result -- the user's trade windows (IS): rejected
27 trades (all entries inside the windows), win 29.6%, **+0.97R, +0.036R per trade, PF 1.07 in R;
+$46.57**; weeks R >= B2 6 of 12; worst weekly drawdown 1.9%. Falsified: average R below B2's
(+0.060R), and the B2 trades the windows remove were the better ones (32 trades, +6.57R, +0.21R
per trade). 24 of X2's trades are identical to B2 trades; 3 are new setups the windows made room
for. Trading around the clock stays the default; the windows stay behind `InpUseTradeWindows`.

### Round 2 conclusion
- Promoted: none. Validation (Mar 2 - May 22) and holdout (Jan 5 - Feb 27) still unused.
- Defaults in v1.17 are the approved risk controls plus the confirmation entry; exit rule 0 with the
  ATR(M15) trail; no trade windows.
- Ideas tried on the IS weeks: 12 (X1a, X1b, X1c, X2 added).
- Trades: `mt5_review_round2_12wk_trades.csv` (modes `B2`, `X1a_breakeven`, `X1b_structure`,
  `X1c_atr_m30`, `X2_windows`).


---

## 2026-09-16 -- Review round 3

Report: `reviews/2026-09-16-pro-trader-review-round3.md`.

**User's answers:** live account is **$100 and stays on demo** until it can carry 1% risk (so the
small-account behaviour has to be explained, not patched around); **yes to the validation run of the
M30 ATR trail**; round-3 focus is **market context** -- the robot should know whether the week is
moving normally, and should skip or shrink trades when the market is abnormal (including the
market's own reaction to FOMC/NFP/CPI, detected from price, not a date list). Earlier answers stand:
1% risk, rolling 10% equity guard (still our interpretation, unconfirmed), around the clock,
confirmation entry.

### Experiment X1c-V -- validation of the M30 ATR trail (pre-registered 2026-09-16, before the run)
- **What:** the round-2 candidate `InpTrailATRTF=30` (trail 1.5 x ATR(M30) instead of ATR(M15)),
  against B2 (v1.17 defaults) on the **validation weeks Mar 2 - May 22, 2026** (12 full weeks),
  same settings as round 2: real ticks, $5,000 at the start of each week, 1% risk, confirmation
  entry, `EXTRA_INPUTS="InpUseRiskSizing=true;InpSwingEntryStyle=1"` plus the trail override.
  Both runs are new: B2 has never been run on these weeks either.
- **Criteria, exactly as pre-registered in round 2** (not re-invented now): paired mean dR > 0 **and
  at least half the in-sample value** (IS was +0.179R per trade, so **>= +0.090R**), **and** total R
  >= B2's total R on the same weeks.
- **If it passes:** `InpTrailATRTF=30` becomes the default exit trail, and the holdout
  (Jan 5 - Feb 27) is the only untouched data left for a final candidate.
- **If it fails:** the default exit stays as it is (ATR on the working timeframe), the variant stays
  behind the input, and Mar - May counts as used from now on.
- **Falsified by:** paired mean dR <= 0, or below +0.090R, or total R below B2's.
- Sample note: ~56 trades per run on 12 weeks. This is a confirmatory test of one pre-registered
  candidate, not a search; it still cannot establish an edge on its own.

### X1c-V result -- PASSED its pre-registered criteria; M30 trail becomes the default
Runs `r3valB2` and `r3valX1c`: 12 runs each, the intended inputs in every tester log
(`InpTrailATRTF=30` in all 12 candidate runs), a ticks line for all 12 weeks, and the first
validation week (Mar 2) traded (B2: 4 trades, 2,106,089 ticks).

| Validation, Mar 2 - May 22 | Trades | Win% | Total R | Avg R | PF (R) | Net $ | PF ($) | Weeks R >= base | Paired dR (t) | Worst week DD |
|---|---|---|---|---|---|---|---|---|---|---|
| B2, trail 1.5 x ATR(M15) | 59 | 44.1 | +17.80 | +0.302 | 1.68 | +861.88 | 1.73 | -- | -- | 3.0% |
| X1c, trail 1.5 x ATR(M30) | 57 | 38.6 | +29.74 | +0.522 | 2.02 | +1,362.66 | 2.01 | 6/12 | +0.190 (t +1.26) | 3.4% |

Criteria as written in round 2: paired dR > 0 (**+0.190R**), at least half the in-sample +0.179R
(**>= +0.090R**), total R >= B2's (**+29.74 vs +17.80**). All three met, so **`InpTrailATRTF`
defaults to M30 in v1.18**, applying the rule as pre-registered rather than re-judging it now.

Caveats stated plainly: 26 of the 57 paired trades were *worse* and only 10 better -- the gain comes
from a handful of large winners; t = 1.26 is not statistically significant; it beat B2 in only 6 of
12 weeks. Both tested periods may simply have suited a looser trail. Mar - May is now used data;
Jan 5 - Feb 27 remains the only untouched set.

### Round 3 diagnosis -- what "normal" looks like (existing data only, no new runs)
Bars pulled from the terminal (`review-scratch/fetch_bars.py`), analysis in
`review-scratch/context_diag.py` / `context_diag.txt`.

- **Normal movement (Dec 2025 - Sep 2026):** D1 median true range **71.66** (10th-90th percentile
  26.2-156.9), ATR(D1) median 83.0. Median M5 range by hour (UTC) peaks at 13:00-15:00
  (7.5-7.9) and 01:00 (6.8); the quiet hours are 20:00-21:00 (3.2) and 03:00-04:00 (3.3-4.0).
  Median M5 tick volume peaks 13:00-14:00 (~2,100) against ~420-820 overnight. Weekday medians are
  flat (M5 range 4.65-4.97). Spread sits at 260 points almost always.
- **Volatility states per period** (ATR(D1) known at the open vs its own 20-day median):

  | Period | Days | Ratio min / med / max | Compressed <0.8 | Normal | Expanded >1.25 |
  |---|---|---|---|---|---|
  | In-sample Jun 22 - Sep 11 | 71 | 0.82 / 0.99 / 1.18 | **0** | **71** | **0** |
  | Validation Mar 2 - May 22 | 70 | 0.60 / 0.98 / 1.36 | 18 | 44 | 8 |
  | Holdout Jan 5 - Feb 27 | 47 | 0.44 / 1.12 / 3.32 | 10 | 18 | 19 |
  | All 403 days | 403 | 0.44 / 1.00 / 3.32 | 52 | 255 | 63 |

  **The 12 in-sample weeks contain no abnormal days at all.** A daily regime filter is therefore
  *untestable in-sample*: it would never fire once in 12 weeks. That is a fact about the tuning
  period, not evidence that regime filtering is useless -- and it explains why every previous round
  found "the market" undifferentiated.
- **M30 ATR state at entry: no consistent sign.** Compressed entries are +23.2R over 110 trades in
  the v1.11 set but -18.9R over 52 trades in the v1.13 set; expanded is +4.8R/139 (v1.15 breakout)
  against -3.2R/15 (E2). Nothing to act on.
- **Hour of day:** the Asia block 00:00-06:00 is negative in 5 of 6 datasets (v1.15 breakout
  -15.5R/299 trades, v1.13 -13.2R/84, v1.11 -17.0R/162, v1.15 swing -12.6R/28, B2 -1.3R/18;
  E2 +5.4R/34 is the exception). The best block differs per dataset, so only the negative side
  repeats.
- **Weekday:** Friday is negative in **all six** datasets (-9.5R/166, -14.0R/14, -6.3R/11,
  -6.4R/11, -10.5R/25, -3.4R/16). **Caveat: these datasets overlap heavily in time and are
  different builds over mostly the same weeks -- six datasets, not six independent samples.**
- **Shocks:** an M5 bar with range >= 4x its own hour's median happens ~8 times a day (2.8% of
  bars), >= 6x about 2.9 times a day; after a 6x bar the next 30 minutes average 5.9x the usual
  range, so shocks really do cluster. But only **2 of B2's 56** in-sample trades were entered
  within 30 minutes of a >= 4x shock (3 within 60 minutes), so a shock pause **cannot be judged
  in-sample either**. Spread spikes are rare: >= 2x its hour median on 0.27% of M5 bars, >= 3x on
  7 of 56,013 bars.

### Experiments, pre-registered 2026-09-16 (before any run)
**Baseline B3 = v1.18 defaults** = round-2 B2 plus the now-default M30 trail, i.e. the existing IS
run `r2X1c`: 57 trades, +18.92R, +$901.36, PF 1.60, worst week 4.1%, 6 of 12 weeks positive. A
default-behavior check must first reproduce that run with v1.18 defaults.
Ideas tried on these 12 weeks: 12 before this round, 14 after.

- **X3 -- no new entries on Friday** (`InpSkipWeekdays="5"`, default ""): the only pattern that
  repeats across every dataset, and the user's own rule ("careful on Monday, Friday and news days").
- **X4 -- no new entries 00:00-06:00 UTC** (`InpUseSessionFilter=true`, `InpSessionStartHour=6`,
  `InpSessionEndHour=24`; existing integer inputs, so no string-override risk): the Asia block is the
  most consistently negative hour range.
- **Pass criteria for both** (IS 12 weeks, raised bar): total R >= baseline + 3.0R; avg R >=
  baseline + 0.15R; weekly R >= baseline in >= 7 of 12 weeks; worst weekly DD <= 1.25 x baseline;
  and the baseline trades the filter removes must have mean R < 0.
- **A pass does not flip a default this round.** With ~57 trades and a filter chosen from these same
  weeks, a pass only makes it a **holdout candidate for a later round**; Jan 5 - Feb 27 stays
  untouched in round 3.
- **Falsified if** total R <= baseline.
- **Not run as experiments** (untestable in-sample, functional checks only): the daily regime filter
  (no abnormal days) and the shock pause (2-3 affected trades). Both are built, default off, and
  verified to fire in forced settings.

### Round 3 checks and results

**Default behaviour:** v1.18 with default inputs reproduced the stored `r2X1c` trades exactly on
Jun 22 (5 trades, -$130.06) and Aug 24 (6 trades, +$560.37), so B3 = `r2X1c` is a valid baseline.

**Two tool/EA defects found and fixed before judging anything:**
1. `mt5_mode_compare.py` wrote string overrides as `InpSkipWeekdays=5||5||0||5||N`, and the EA
   received that whole text as the string (it would also have matched the "0" = Sunday). Fixed with
   an explicit `Name=str:value` form; verified in the log (`InpSkipWeekdays=5`) and in trades (Jun 22
   week 5 trades -> 4, the Friday entry gone).
2. The new breakout context gate ran on every tick in swing mode, because the raw breakout signals
   are still computed there: **1,591,589 log lines in one week**. Trades were unaffected (the swing
   path re-evaluates the gate), but the logs were unusable. Fixed: the gate is asked only on a new
   bar in breakout mode, and the risk-scaling line is limited to one an hour. Re-run: 5 log lines,
   identical trades, lots and R.

**Functional checks (Jun 22 week, forced settings so the mechanisms must fire):**

| Check | Setting | Result |
|---|---|---|
| Shock pause | `InpUseShockPause=true`, 3x range/ticks, 60 min | 4 of the 5 trades taken (the Monday 00:30 entry was inside a cooldown), R -2.00 vs -3.00 |
| Regime skip | band forced to 1.00-1.05 | **no trades at all** -- every setup skipped, as intended |
| Regime risk shrink | same band, `InpRegimeRiskFactor=0.5` | same 5 trades at half size (lots 0.01-0.03 vs 0.02-0.06; risk $17-24 vs $34-48; R identical -3.00, $ -58.48 vs -130.06) |

**X3 -- no Friday entries: FAILED (narrowly), default unchanged**

| IS 12 weeks | Trades | Win% | Total R | Avg R | PF (R) | Net $ | Weeks R >= B3 | Worst week DD |
|---|---|---|---|---|---|---|---|---|
| B3 (v1.18 defaults) | 57 | 38.6 | +18.92 | +0.332 | 1.60 | +901.36 | -- | 4.1% |
| X3 (`InpSkipWeekdays="5"`) | 46 | 39.1 | +22.00 | +0.478 | 1.87 | +1,056.60 | 11/12 | 3.1% |

Criteria: total R >= 21.92 ✓ (22.00), **avg R >= 0.482 ✗ (0.478)**, weeks >= 7 ✓ (11), DD <= 5.1% ✓,
removed trades mean R < 0 ✓ (-0.279 over 11 trades). One of five criteria missed, by 0.004R -- a miss
is a miss. And the result is circular anyway: all 46 surviving trades are *bit-identical* to the
baseline (paired dR = 0.000), so the "gain" is exactly the 11 Friday trades that were negative in
these same weeks.

**X4 -- no entries 00:00-06:00 UTC: FAILED, default unchanged**

| IS 12 weeks | Trades | Win% | Total R | Avg R | PF (R) | Net $ | Weeks R >= B3 | Worst week DD |
|---|---|---|---|---|---|---|---|---|
| X4 (session filter 06-24) | 41 | 41.5 | +21.43 | +0.523 | 2.00 | +1,004.62 | 9/12 | 2.6% |

Criteria: **total R >= 21.92 ✗ (21.43)**, avg R >= 0.482 ✓ (0.523), weeks >= 7 ✓ (9), DD ✓, removed
trades mean R < 0 ✓ (-0.197 over 18 trades). Of the 39 shared trades 38 are identical and one is
worse; the filter also let 2 new setups through. Same circularity as X3.

**Round 3 conclusion**
- Promoted: only the M30 ATR trail (on its pre-registered validation pass). X3 and X4 stay off.
- The context features (profile, regime, shock pause, weekday skip) ship **off**, verified to work,
  explicitly **not** shown to make money -- the in-sample weeks cannot test them.
- Ideas tried on the IS weeks: 14. The IS weeks are exhausted for tuning, and they are also the
  wrong data for context work: they contain no abnormal day at all.
- Jan 5 - Feb 27 remains untouched. It is the most abnormal stretch of the year (19 of 47 days
  expanded, ratio up to 3.32), which makes it the natural place to judge a context-aware candidate
  once one exists -- not another filter fitted to the summer.
- Trades: `mt5_review_round3_trades.csv` (modes `val_B2_trail_m15`, `val_X1c_trail_m30`,
  `IS_B3_default_m30`, `IS_X3_no_friday`, `IS_X4_no_asia`).

### The $100 account: what balance the demo needs, and why there is no honest "small-account preset"
B3's 57 in-sample trades have stops of 3.44 to 17.23 price units, i.e. **$3.44-$17.23 of risk at the
0.01 minimum lot** (median $7.10). Against the 1% target and the 1.5% hard cap:

| Demo balance | Trades skipped by the cap | Trades taken | Mean risk of taken trades | Forced to the 0.01 minimum |
|---|---|---|---|---|
| $100 | **57 of 57** | **0** | -- | 57 |
| $500 | 26 | 31 | 1.08% | 43 |
| $1,000 | 5 | 52 | 0.84% | 13 |
| $2,000 | 0 | 57 | 0.83% | 0 |
| $5,000 (tested) | 0 | 57 | 0.93% | 0 |

So on the user's $100 the robot correctly **never trades**, and on $500 it would show roughly half of
its setups -- a robot that looks broken while it is in fact obeying the risk rule.

**Would a "small-account preset" be honest? No.** If the cap were lifted so a $100 account always
used 0.01 lot, the real risk per trade would be **3.4% to 17.2% of equity** (median 7.1%), with 43 of
57 trades risking more than 5%. Two to eleven losing trades would halve the account. That is not a
preset, it is 1% risk in name only, so the cap stays and the answer is the balance, not the input:
**fund the demo with $2,000 to see the tested behaviour** (or $1,000 and accept ~9% of setups
skipped). This is also the honest precondition for going live later.


---

## 2026-09-16 -- Review round 4: the holdout

**User's answers:** demo stays at **$100** (they accept it will sit idle -- so the EA must *show* why
it is idle); the equity-guard reading stays an unconfirmed assumption; the holdout candidate is the
**regime filter in risk-shrink mode**; **Fridays off by default** as their own preference, knowing the
test failed and was circular; shock detector and HUD context display stay open questions.

### Experiment H1 -- regime risk-shrink on the holdout (pre-registered 2026-09-16, before the run)
- **Weeks:** Jan 5 - Feb 27, 2026, the last untouched data -- 8 full weeks (Mondays Jan 5, 12, 19, 26,
  Feb 2, 9, 16, 23). The most abnormal stretch of the year: 10 compressed and 19 expanded days of 47,
  ATR(D1) ratio 0.44 to 3.32.
- **Runs:** both at $5,000 per week, 1% risk, real ticks, v1.18 defaults, confirmation entry.
  - Baseline: `EXTRA_INPUTS="InpUseRiskSizing=true"`.
  - Candidate: `+ "InpUseRegimeFilter=true;InpRegimeRiskFactor=0.5"` -- band left at the input
    defaults **0.80 - 1.30**, factor **0.5**, both fixed before seeing any holdout result.
  - **The Friday skip is off in both runs** so the comparison isolates the regime filter. What the
    Friday rule would have done on these weeks is reported separately as an observation, not a test.
- **What this can and cannot show:** halving the lot halves profit *and* risk, so **R per trade is
  unchanged by construction**. This tests a risk control, not an edge: the question is whether cutting
  size on abnormal days gives up little profit for a real cut in drawdown. R is reported only as a
  check that the filter changed size rather than trade selection.
- **Primary metrics:** net $ and worst weekly drawdown %.
- **Pass criteria:**
  - worst weekly drawdown <= **0.80 x** the baseline's, **and**
  - if the baseline's net $ is positive, candidate net $ >= **0.60 x** baseline net $; if the
    baseline's net $ is negative, candidate net $ **better (less negative)** than the baseline's, **and**
  - trade count within **+/-10%** of the baseline's and total R within +/-1.0R (evidence that it
    resized rather than re-selected).
- **Falsified if:** drawdown is not reduced, or net $ falls below 60% of a positive baseline.
- **The separate, bigger question this run answers:** the baseline is the **first out-of-sample read
  of the v1.18 defaults**. Its trades, R, net $ and weekly spread are reported as the project's honest
  out-of-sample result, whatever they say.
- **After this run no untouched data remains.** Any further judgement has to come from demo-forward or
  live-forward observation, not from more tester rounds on these same weeks.

### H1 result -- regime risk-shrink on the holdout: FAILED its criteria
Both runs: 8 weeks, 8 ticks lines each, the intended inputs in every tester log
(`InpUseRegimeFilter=true InpRegimeRiskFactor=0.5` in all 8 candidate runs, `InpSkipWeekdays=` empty
in both).

| Jan 5 - Feb 27 (holdout) | Trades | Win% | Net $ | PF ($) | Total R | Avg R | Weeks + | Worst week DD | Avg lot | Partial closes |
|---|---|---|---|---|---|---|---|---|---|---|
| v1.18 defaults (baseline) | 41 | 36.6 | **+408.78** | 1.41 | +8.22 | +0.201 | 5/8 | **3.90%** | 0.047 | 8 |
| + regime 0.5x on abnormal days | 41 | 36.6 | **+133.81** | 1.19 | +8.91 | +0.217 | 5/8 | **2.20%** | 0.033 | 1 |

Criteria: worst weekly DD <= 3.12% ✓ (2.20%); net $ >= 0.60 x 408.78 = $245.27 **✗ (+$133.81, only
33%)**; same trades ✓ (41 vs 41, total R +8.91 vs +8.22, all 41 paired). **Failed on net $.**

Reading: it did exactly what it was built to do -- drawdown fell 44% -- but on these weeks **the
abnormal days were where the profit was**, so halving size there cost 67% of the profit to buy that
protection. Weekly: Jan 5 +$145.89 -> +$0.22, Feb 16 +$242.13 -> +$119.05, and the worst week improved
from -$183.48 to -$83.00.

Two honest notes:
1. **R is unchanged by construction** (halving the lot halves P/L and risk alike), so the small R
   difference (+8.22 -> +8.91) is not an edge: it comes from lot rounding. At half size the average
   lot fell to 0.033, and 33% of that rounds to 0.00, so **partial closes at TP1/TP2 collapsed from 8
   to 1** -- trades ran to their full exit instead of banking part. That is a real side effect of
   shrink mode on a small account, worth knowing.
2. The candidate is judged on money and drawdown only, exactly as pre-registered.

### The holdout's bigger answer -- first clean out-of-sample read of the v1.18 defaults
**41 trades, +$408.78, PF 1.41, +8.22R (+0.201R per trade), 5 of 8 weeks positive, worst week
-$183.48 (-4.09R), worst weekly drawdown 3.90%.** Weekly net $: +145.89, -30.91, +66.46, -56.78,
+187.23, +38.24, +242.13, -183.48.

This is the first time the strategy has been measured on data never used for any decision, and it is
positive. It is **not** proof: 41 trades over 8 weeks, one regime (an unusually volatile stretch), and
the project has tried ~14 ideas to get here. Compare with the tuning periods: in-sample +0.332R per
trade, validation +0.302R (old trail) / +0.522R (new), holdout +0.201R -- the ranking is consistent
and the size is small, which is what an honest, weak-but-real result looks like.

### Friday on the holdout -- observation, not a test
The user asked for Fridays off as a personal rule. On the holdout weeks that rule would have **cost**
money: 6 Friday trades made **+$173.70 (+3.48R)**; without them the baseline falls from +$408.78 to
+$235.08. Combined with the failed, circular in-sample test, the record is: no data supports the
Friday rule, and the only clean data argues against it. It ships on by default because the user asked
for it, clearly labelled as a preference.

### After this round
**No untouched data remains.** In-sample, validation and holdout have all been used. Any further
claim about this EA has to come from demo-forward or live-forward observation. More tester rounds on
these weeks can only produce better-fitted numbers, not better evidence.

## 2026-09-17 -- the user's decisions after reading round 4 (v1.20)

No experiment, no tester batch: three settings decided by the user once the round-4 evidence was in
front of them.

1. **Fridays are traded again** (`InpSkipWeekdays=""`). Shown that the holdout's 6 Friday trades made
   +$173.70 -- about 42% of the holdout's +$408.78 -- and that the in-sample skip test had failed by
   0.004R and was circular, the user dropped their own preference in favour of the evidence. This is
   worth recording as a decision *against* a rule the user had asked for a day earlier: the only
   clean data we have argues for trading Fridays.
2. **The equity guard is confirmed**, not assumed: pause new entries while equity is 10% or more
   below its highest value of the last 7 days, resume once back inside or when that peak ages out.
   That is what the code already did (`InpEquityGuardPct=10`, `InpEquityGuardDays=7`); it is no
   longer flagged as an interpretation. It has still never fired in any test.
3. **The shock pause stays off** for forward observation, so demo results remain comparable with the
   build that produced the holdout numbers.

Compiled v1.20 from the committed source: 0 errors, 0 warnings. The only behavioural difference from
v1.19 is that Friday entries are allowed again, so the holdout figure (+$408.78, 41 trades, PF 1.41)
is the number that describes the current defaults -- v1.19's Friday rule would have reduced it to
+$235.08.
