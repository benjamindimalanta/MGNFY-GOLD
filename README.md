# MGNFY GOLD

An MQL5 Expert Advisor for XAUUSD (gold) on MetaTrader 5. **This is the live
source behind the published product:**
[mql5.com/en/market/product/154202](https://www.mql5.com/en/market/product/154202)

- Internal source filename: `XAU_Gold_ATR_Regime_EA.mq5`
- Version in this repo: **1.11** (the version live on the MQL5 Market as of
  the last time this repo was updated)
- Originally built: **November 2025**
- Recovered/archived into version control: **September 2026**, after the
  original author lost track of where the source lived (it was sitting in
  `OneDrive\Pictures\MSB-OB\`, unversioned, alongside unrelated photo
  exports). This repo exists so that doesn't happen again.

> **Where this file was found**, for the record: `MGNFY GOLD.mq5` in that
> OneDrive Pictures subfolder is the only file on the author's machine whose
> `#property link` points at the exact MQL5 Market product URL above, and
> whose preset files (`Conservative` / `Balance` / `Active`) match the
> "Conservative / Balanced / Active profiles" advertised on the product
> page. A separate, unrelated rewrite exists at
> `OneDrive\Desktop\MGNFY GOLD v2\` (different logic entirely — H1/H4/D1
> majority-vote bias system, no partial take-profits) — that is **not**
> this product and was not merged in here.

---

## What it does, in plain terms

The EA trades one direction at a time on whatever chart timeframe it's
attached to (the product listing recommends **M15**). Every new bar, it
re-evaluates a simple ATR-based trend/regime model and decides whether to
buy, sell, or do nothing.

### 1. The regime model
It builds a channel around each bar's high/low midpoint:

```
midline   = (high + low) / 2
upperBand = midline + ATRMultiplier * ATR
lowerBand = midline - ATRMultiplier * ATR
```

It tracks a running "trend" state (+1 up / -1 down) using trailing versions
of those bands (a SuperTrend-style construction) — the trend only flips when
price closes convincingly through the trailing band on the opposite side.

### 2. Entry trigger
Two selectable trigger styles:
- **Midline breakout** (default): a new bar closes on the opposite side of
  the midline from the previous bar. This fires often — it's a
  crossing-the-middle signal, not a full reversal.
- **Band breakout**: price has to close beyond the outer ATR band instead —
  fewer, more extreme signals.

By default (`InpRequireTrendFlip = false`) it trades **every** breakout in
that style, not just ones where the regime state actually just flipped.
Turning that input on restricts entries to genuine trend reversals only.

Optional add-on filters (all off by default except the trend filter):
- **MACD filter** — require MACD above/below zero in the trade direction.
- **Higher-timeframe EMA trend filter** (**on by default**: H4, EMA 200) —
  price must be on the correct side of that EMA to allow the trade; there's
  also an optional "EMA must be sloping the right way" requirement.
- **Session-hour filter** — restrict to a server-time trading window.
- **Spread cap** — refuse entries above a max spread (points).
- **Margin buffer check** — refuses an entry unless free margin covers the
  position with a configurable safety margin (default 20% buffer).

Only one position open at a time by default. Lot size is either a fixed
input value, or sized from a risk-% of equity plus the stop distance.

### 3. Stop-loss
ATR-based by default: `SL = entry - SL_ATR_Mult * ATR` (long) — or a
percent-of-price stop if ATR stops are turned off. All SL/TP prices are
clamped to the broker's minimum stop-distance before being sent.

### 4. Exit — the "1R/2R/3R" partial take-profit system
This is the core of the product's pitch. `R` = the stop-loss distance in
price. The EA scales out in three stages as price moves in its favor:

| Level | Default | Action |
|---|---|---|
| TP1 = 1R | `InpTP1_R_Mult = 1.0` | close 33% of the position, then move SL to breakeven |
| TP2 = 2R | `InpTP2_R_Mult = 2.0` | close another 33% |
| TP3 = 3R | `InpTP3_R_Mult = 3.0` | close whatever remains (~34%) |

Independently of that ladder, an optional **ATR trailing stop** (on by
default) continuously tightens the stop toward price once in profit, which
can lock in more than breakeven before TP2/TP3 are ever reached.

### 5. Small-account mode
If effective capital (account equity, or a manually declared value) is at
or below a threshold (default **$300**), a separate, more conservative rule
kicks in: as soon as floating profit reaches a small fixed $ amount *or* a
% of capital (whichever is larger), the EA closes half the position early
and moves the stop to breakeven + a small buffer. This exists to stop tiny
accounts from giving back small wins to normal volatility before the main
1R/2R/3R ladder would ever trigger.

### 6. On-chart HUD
A dark-panel statistics display (toggle: `InpDrawVisuals`) showing realized
+ floating P/L, win/loss trade counts and win rate, drawdown from balance,
account balance, and all-time realized P/L — plus horizontal lines marking
the current entry, SL, and TP1/TP2/TP3 on the chart.

---

## Presets included (`presets/`)

All five `.set` files found alongside the source are kept here. They differ
only in input values, not logic:

| Preset | ATR mult | SL (ATR mult) | Trend filter | MACD filter | Trend-flip required | Risk sizing | Notes |
|---|---|---|---|---|---|---|---|
| **Conservative** | 2.5 | 1.5 | **on** (H4 EMA200, slope required) | **on** | **required** | 0.5% equity | Tightest filtering — only trades confirmed reversals with the trend |
| **Balance** | 2.0 | 1.0 | off | off | not required | fixed lot | Middle-ground defaults; matches the .mq5's own input defaults |
| **Balance FIXED** | 2.0 | 1.0 | off | off | not required | fixed lot | Same values as Balance — comment says trend filter was disabled here for a testing session |
| **Active** | 1.5 | 0.8 | off | off | not required | fixed lot | Tighter stops, wider spread/slippage tolerance — more, faster trades |
| **TEST Trading** | 1.5 | 0.8 | off | off | not required | fixed lot | Margin check and spread cap both disabled — diagnostic-only, to confirm the EA *can* place trades before re-enabling filters. **Not for live/real-money use.** |

---

## Setup (from the product listing)

| | |
|---|---|
| Symbol | XAUUSD |
| Timeframe | M15 |
| Minimum deposit | $100 / 0.01 lot |
| Recommended deposit | $500 / 0.01 lot (≈10% drawdown headroom) |
| Broker | Any |

No martingale, no grid. Every order is protected by a stop-loss from the
moment it's sent.

---

## Repo contents

```
MGNFY GOLD.mq5     - EA source (v1.11, live on MQL5 Market)
MGNFY GOLD.ex5     - compiled binary matching this source (compiled 2025-10-31,
                      3 days before the final source edit on 2025-11-03 — see
                      Known gaps below)
presets/           - the 5 .set input presets described above
```

## Known gaps / things to double-check before the next update

- The `.ex5` binary predates the `.mq5`'s last save by ~3 days. They're very
  likely in sync (no evidence of a substantive edit in between), but this
  hasn't been verified line-by-line — recompile from source before
  publishing an update rather than trusting this `.ex5`.
- No changelog exists prior to this repo. Version history before 1.11 is
  unknown; treat 1.11 as the baseline going forward and log changes here
  from now on.
- This EA has not yet been backtested by the current project workflow
  (multi-year offline validation, in-sample/out-of-sample split, walk-forward).
  It shipped and has presumably run live/demo, but no rigorous historical
  validation record exists in this repo yet.

---

## Ownership / anti-scam notice

(Carried over from the product listing, unchanged.) This EA is sold only
through MQL5.com. Anyone contacting you elsewhere claiming to sell it is a
scammer — block and report them. Any copy obtained outside MQL5.com is not
the genuine version and will not receive updates or support.
