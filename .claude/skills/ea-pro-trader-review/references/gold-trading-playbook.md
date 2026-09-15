# Gold (XAUUSD) trading playbook

What an experienced gold trader knows, organized so each idea can be checked against the EA and, if
useful, turned into a testable rule. Times are UTC (Exness MT5 server time is UTC). Summer = US/UK
daylight saving in effect (roughly mid-March to late October / early November).

## Contents
1. The user's own method
2. How gold moves: sessions and daily rhythm
3. What moves gold: news and drivers
4. Market structure and multi-timeframe bias
5. Liquidity: why stops at obvious swings get hit
6. Entries
7. Stops
8. Targets and trade management
9. Risk management
10. What realistic results look like
11. Turning discretionary rules into code

---

## 1. The user's own method

As the user described it (keep the EA aligned with this; it is the reason the robot exists):

1. Look at **M5** for a first read.
2. Decide the **bias**, then confirm it on **M30, H1 and H4** using **EMA direction** and
   **higher highs / higher lows** (lower highs / lower lows for bearish).
3. If bullish, only buys (and the reverse).
4. On **M30 and H1**, mark where to enter, stop and take profit, using the **previous swing low/high**
   (trendlines by eye).
5. Go back to **M5** to find the exact entry, anticipating a pullback into the level.
6. **Pre-set pending orders** rather than entering at market.
7. Treat a bias as valid for **1-3 hours**, then re-check and place new orders.
8. Focus on the **London and New York sessions**, where gold moves most.
9. Be extra careful on **Mondays, Fridays and major news days**; on those days ride the prevailing flow
   instead of fighting it.
10. SL and TP "depend on market movement" -- i.e. placed at structure, not fixed distances.

Settings the user chose for the EA's swing mode: 2 of 3 timeframes must agree, EMA 50, entries at M30
swings.

Answers the user gave on 2026-09-15 (they refine points 7-10):
- **Hours:** 10:00-14:00, 15:00-17:00 and 19:00-21:00 local time (UTC+4, no daylight saving) =
  **06:00-10:00, 11:00-13:00, 15:00-17:00 UTC**: London morning, the hour before the US data window,
  and the New York open. In the EA: `InpTradeWindows`.
- **Risk:** 1% per trade; a "moving" weekly drawdown limit of 10%, implemented as no new entries while
  equity is 10% or more below its rolling 7-day peak (interpretation). In the EA: `InpRiskPercent`,
  `InpEquityGuardPct`, `InpEquityGuardDays`.
- **News:** FOMC, NFP and CPI are traded, more carefully -- not avoided. A reduced-risk rule around
  them is a future candidate (needs a schedule file for the tester).
- **Exits:** left to evidence ("decide the best exit management").
- **Manual trading:** not on the EA's account.
- Wants swing mode as the EA's default.

## 2. How gold moves: sessions and daily rhythm

| Window (UTC, summer) | Character | Implication |
|---|---|---|
| 22:00-00:00 | Market reopens after the daily break (NY 17:00-18:00); thin, spreads wide | Avoid new entries; Sunday open can gap |
| 00:00-07:00 Asia | Lower volume, ranges form, false breaks common | Breakout entries get chopped; mark the Asia high/low |
| 07:00-08:00 London open | Volatility jumps; London often sweeps one side of the Asia range, then picks a direction | Classic stop-hunt window; wait for the sweep and reclaim |
| 08:00-12:00 London | Trend legs develop | Pullback entries in the London direction |
| 12:00-12:30 | NY pre-open; US data at 12:30 (08:30 ET) | Spreads widen, spikes of $10-40 in seconds |
| 12:00-16:00 London + NY overlap | Highest volatility and volume of the day | Best moves, also the most violent stop runs |
| 16:00-20:00 NY afternoon | Moves continue or reverse after London close (16:00) | Profit-taking, fading late moves |
| 20:00-21:00 | NY close approaches, liquidity drops | Close or tighten; avoid new trades |

In winter every London and NY time shifts one hour later in UTC.

Typical XAUUSD daily range in 2026 prices is roughly $30-60; an M30 ATR of $8-14 is common. A single
M5 candle during news can exceed a normal hour's range.

Weekdays: Monday often waits for London to set direction after the weekend; Tuesday-Thursday usually
carry the cleanest trends; Friday afternoon (after ~16:00) sees position squaring and random reversals,
worse before a US jobs report.

## 3. What moves gold: news and drivers

- **Tier-1 US data**: NFP (first Friday, 12:30), CPI, PCE, retail sales, ISM, jobless claims (Thursday).
- **FOMC** rate decision (18:00 summer) and press conference; Fed speakers.
- **US dollar and real yields**: gold usually falls when the dollar and US real yields rise.
- **Risk-off events** (geopolitics, banking stress): sudden spikes up.

Professional habit: no new entries from ~15 minutes before to ~15-30 minutes after tier-1 releases;
widen or remove tight stops around them, or be flat. Spreads can widen several times normal.

Note: MT5's built-in economic calendar (`CalendarValueHistory`) works live but not in the Strategy
Tester, so a news filter can only be backtested from an imported schedule of release times.

## 4. Market structure and multi-timeframe bias

- **Swing high / swing low**: a candle whose high (low) is beyond the N candles on each side.
- **Uptrend**: higher highs (HH) and higher lows (HL). **Downtrend**: lower highs and lower lows.
- **Break of structure (BOS)**: price closes beyond the last swing in the trend direction (continuation).
- **Change of character (CHoCH)**: price closes beyond the last swing *against* the trend -- the
  first sign the trend may be ending.
- **Top-down**: H4 sets the context, H1 the working trend, M30 the setup, M5 the trigger. A trader
  usually trades only when at least the working and setup timeframes agree with the context, or waits.
- **EMA as a filter**: price on the right side of a sloping EMA (e.g. 50) confirms trend; a flat EMA
  with price chopping around it means range -- trend entries fail there.

## 5. Liquidity: why stops at obvious swings get hit

Obvious swing highs and lows, equal highs/lows and the Asia range edges are where many traders place
stops. Large participants push price through those levels to fill orders, then price often snaps back.
This is why:

- a limit order placed exactly at the last swing, with a stop just beyond it, tends to fill *during*
  the push through the level and get stopped out minutes later;
- a trader instead waits for the **sweep and reclaim**: price trades through the swing, then an M5
  or M15 candle closes back on the bias side of it -- that close is the entry signal;
- or places the stop beyond the whole liquidity area with a volatility buffer and reduces size so the
  risk in dollars stays the same.

The evidence in this project matches: swing mode's losers were stopped in a median of ~5 minutes, and
most losers that later reached TP1 first went several ATR against the entry.

## 6. Entries

What distinguishes a professional pullback entry:
- **Zone, not a price**: the area around the swing / prior structure / EMA, defined with some width.
- **Confluence**: the zone lines up with more than one reason (swing level + EMA + session high/low).
- **Confirmation**: a rejection candle (long wick back out of the zone, close on the bias side), an
  engulfing candle, or an M5 CHoCH in the bias direction.
- **Momentum check**: do not buy into a fast, large-bodied push down through the zone; wait for it to
  stall.
- **Timing**: prefer London and NY; avoid the last hour before the daily break and minutes around news.
- **One good trade beats five mediocre ones**: skipping is a position.

## 7. Stops

- Place the stop at the **invalidation point**: the price where the trade idea is proven wrong (beyond
  the swept low for a buy, beyond the confirmation candle's wick), plus a buffer for spread and noise.
- Size the position from the stop distance so every trade risks the same percent.
- If the stop needed to be at invalidation makes the reward-to-risk too small, **skip the trade** rather
  than tightening the stop.
- Never widen a stop after entry.

## 8. Targets and trade management

- **First target** at the nearest opposing structure (last swing high for a buy) or ~1-1.5R.
- Take partial profit there and move the stop to **structure** (below the most recent higher low),
  not blindly to breakeven.
- **Trail by structure** on the entry timeframe (new higher lows) in trends; trailing by a fixed ATR on
  a small timeframe tends to exit good trades on normal pullbacks.
- Let a runner go toward higher-timeframe targets when the bias is strong; close before major news if
  the trade has not paid.

## 9. Risk management

- Risk **0.5-1%** of equity per trade; **2-3% max daily loss**, then stop for the day.
- Stop after a set number of consecutive losses (e.g. 3-4) and re-check conditions.
- Know the margin: at 1:100 leverage, 0.01 lot gold needs ~$44 margin at $4,400 -- a $100 account
  cannot control risk percent at all with the minimum lot.
- Correlated exposure: one gold position at a time for a small account.

## 10. What realistic results look like

- Pullback / trend-following systems: roughly **35-50% win rate** with average winners of **1.5-3R**.
- A realistic, tradeable profit factor is **1.3-2.0** after costs; above 3 on a small sample usually
  means overfitting or too few trades.
- At least ~**100 trades** before trusting a win rate or PF; several hundred and multiple market
  regimes (trend, range, high and low volatility) before going live.
- Very high win rates (80%+) come from tiny targets and big stops; they blow up on the losses.

## 11. Turning discretionary rules into code

Codeable and testable:
- swing highs/lows (fractal with N bars each side), HH/HL structure, BOS/CHoCH as closes beyond swings;
- EMA side and slope per timeframe; agreement across timeframes;
- session and weekday windows (in UTC, with daylight saving);
- zones as swing +/- a fraction of ATR; sweep-and-reclaim as "low below the level, close back above";
- rejection candles (wick-to-body ratios), engulfing patterns, M5 CHoCH;
- stops at invalidation + buffer; position size from stop distance; targets at opposing swings;
- news blackout windows from an imported release schedule.

Hard to code faithfully:
- hand-drawn trendlines (approximate with lines through consecutive swings, or skip);
- "the market feels heavy", discretionary skipping.

Every translation is a hypothesis. Test it against the current behavior on the same weeks before
calling it an improvement.
