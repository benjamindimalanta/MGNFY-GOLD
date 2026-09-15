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
