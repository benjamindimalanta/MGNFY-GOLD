# MQL5 EA code audit checklist

Use this in Phase 1. For each item: find the code, form a suspicion, then prove or disprove it with
tester evidence (logs, trades) and estimate its money impact. A plausible-looking bug that the data
doesn't show is not a finding.

## Contents
1. How to prove a suspicion
2. Checklist
3. Verified issues in MGNFY GOLD
4. Unverified risks to check next

---

## 1. How to prove a suspicion

- Find an existing `Print`/`PrintFormat` at the decision point, or add one behind no input (logging
  only). The EA already logs every new-bar evaluation (`NB state: ...`), trend filter values, entries,
  swing-mode bias checks and order handling.
- Run a short Strategy Tester batch (one or two weeks) and parse the tester agent logs. They are UTF-16
  and can be split across several `Tester\<hash>\Agent-127.0.0.1-300N\logs\<yyyymmdd>.log` files; read
  all of them.
- Quantify: "X% of N evaluations show Y", "Z trades affected, net $W".

## 2. Checklist

1. **Forming bar vs closed bar.** Index 0 is the bar still forming. At the first tick of a new bar its
   high = low = open = the current price, so anything computed from bar 0's high/low/close at new-bar
   time is not the bar the chart later shows. Signals should normally use closed bars (shift 1, 2...).
2. **New-bar detection across timeframes.** `IsNewBar()` watches `InpTF`, which may differ from the
   chart period. Higher-timeframe series may not be synchronized yet: check `CopyX` return counts and
   `Bars()`, and don't treat "no data" as a valid zero.
3. **Series direction and buffer shifts.** `ArraySetAsSeries`, `CopyBuffer(handle, buffer, start_pos,
   count)` -- `start_pos` 0 is the forming bar.
4. **Levels that move while a trade is open.** Targets or stops recomputed every tick from a live ATR
   drift away from what was planned at entry.
5. **Volume rounding.** Partial closes at the minimum lot round to zero (33% of 0.01 = 0.00) and
   silently fail.
6. **Broker constraints.** Stops level, freeze level, filling mode, allowed expiration types; stop
   clamping functions that return 0 may send an order **without a stop**.
7. **Pending-order lifecycle.** Placement, duplicates, cancellation reasons, fills through gaps, the
   stop attached to the order, behavior after an EA restart.
8. **Position selection on hedging accounts.** `PositionSelect(symbol)` and
   `CTrade::PositionClose(symbol)` act on *a* position for that symbol, not necessarily the EA's own
   (magic number). Manual trades on the same symbol can be modified or closed.
9. **Trade-request frequency.** Modifying stops on every tick floods the broker and slows testing.
10. **Spread and slippage.** Units (points vs price), filters applied at the right moment.
11. **Time.** `TimeCurrent()` = server time; `TimeGMT()` in the Strategy Tester equals simulated server
    time; session filters in server hours; UK/US daylight saving.
12. **Margin and sizing.** `OrderCalcMargin`, margin buffers, and account sizes where the minimum lot
    already exceeds the intended risk.
13. **Tester-only differences.** `OnChartEvent` is not called in the tester; the economic calendar is
    unavailable; `TesterHideIndicators`; visual vs non-visual runs.
14. **Global state on re-init.** Flags like `tp1Hit`, plan prices, last bar time -- what happens when
    the EA is re-attached with an open position or pending order.
15. **Side logic that changes trades.** E.g. small-account partial capture active below an equity
    threshold.
16. **Comments and descriptions vs code.** The product description and inline comments have been wrong
    before; trust execution.

## 3. Verified issues in MGNFY GOLD

1. **Breakout entry is effectively "first tick vs previous close" (v1.11-v1.15, breakout mode).**
   `CopyLatest()` takes `close0`, `high`, `low` from bar 0 and `OnTick()` evaluates entries only at the
   new-bar tick, so `hlMid` (the "midline") is the new bar's opening price, which equals the previous
   bar's close in the tester data. Evidence (tester agent logs, 2026-09-15, 54,492 new-bar evaluations):
   `mid == close1` in **100%** of them; **97.9%** of buy breaks had `close0 > close1` and **98.0%** of
   sell breaks had `close0 < close1`; a break fired on **84.3%** of bars. The signal is close to a coin
   flip on the first tick's direction, limited only by the one-position rule -- consistent with ~16
   trades/day, ~34% win rate and PF 0.93 over 943 trades in 12 weeks. A fix (evaluate the midline and
   crossing on closed bars) is a *behavior change* that must be tested like any other experiment.
2. **Take-profit ladder never fired at 0.01 lot (v1.11).** Fixed in v1.12: TP levels count as reached
   even when the partial close can't be split off. Confirmed: 0 TP exits in 481 v1.11 trades; TP3 exits
   appear from v1.12 on.
3. **Breakout-mode TP1-TP3 are recomputed from the current ATR on every tick**, so target distances
   drift while a trade is open (visible as TP3 exits between +1.3R and +3.3R).
4. **ATR trailing uses `InpTF`'s ATR (M15 in the user's settings) x 1.5** for all trades, including
   swing-mode trades planned on M30 structure; it can tighten well inside the structural stop.
5. **Swing-mode limit orders fill while price pushes through the swing.** v1.15, 12 weeks: 62 of 77
   trades lost, 55 about a full 1R, 34 stopped within 5 minutes of filling. A wider stop was tested by
   replay and lost more money at every width (see JOURNAL.md, stop-buffer study).
6. **Chart-object issues fixed in v1.13** (per-bar line objects never cleaned up; HUD background
   compiled out by `#ifdef OBJPROP_BGCOLOR`; HUD rebuilt every tick). Not trading logic, listed so they
   aren't rediscovered.

## 4. Unverified risks to check next

- `MoveSLto()` selects with `PositionSelect(InpSymbol)` and the TP3 exit calls
  `Trade.PositionClose(InpSymbol)`; the account runs in **hedging mode**. If the user trades gold
  manually on the same account, the EA may move the stop of, or close, the manual position. Verify with a
  tester run that opens a second position with a different magic, or by code inspection plus a demo test.
- `ClampSLForOrder()` returns 0 when the proposed stop is on the wrong side or too close, and the order is
  then sent **without a stop loss**. Count how often this happens in logs (`Enter BUY ... sl=0.00`).
- Small-account partial capture (`InpSmallCapThreshold`, the user's tests use 100) closes half the
  position at a small dollar profit when equity is at or below the threshold; check whether it fires in
  $100 runs and how it interacts with the TP ladder.
- `IsNewBar()` on `InpTF` while the tester chart is H1 or M5: confirm entries happen at the intended
  timeframe's bar opens only.
