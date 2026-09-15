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
