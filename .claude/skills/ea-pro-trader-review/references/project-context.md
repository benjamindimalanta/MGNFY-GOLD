# MGNFY GOLD project context

Everything needed to work on this EA without rediscovering it. Facts here were verified on 2026-09-15;
if something contradicts the current repo, trust the repo and update this file.

## Contents
1. Where things are
2. EA architecture (v1.15)
3. The user's test settings
4. Tooling: compile, run, parse
5. MT5 gotchas (each cost real time to learn)
6. Data inventory and which weeks are clean
7. Current baseline results
8. Experiments already done -- don't repeat
9. History

---

## 1. Where things are

| What | Location |
|---|---|
| GitHub repo | `benjamindimalanta/MGNFY-GOLD` (branch `main`) |
| EA source | repo `MGNFY GOLD.mq5` (the committed `.ex5` is an old binary; always compile from source) |
| User's local copy | `C:\Users\Benja\OneDrive\Pictures\MSB-OB\MGNFY GOLD.mq5` plus `.set` presets |
| MT5 install | `C:\Program Files\MetaTrader 5 EXNESS\` (`terminal64.exe`, `MetaEditor64.exe`) |
| MT5 data folder | `C:\Users\Benja\AppData\Roaming\MetaQuotes\Terminal\53785E099C927DB68A545C249CDBCE06` |
| Compiled EA the tester uses | data folder `MQL5\Experts\MGNFY GOLD.mq5` / `.ex5` |
| Tester reports (`.htm`) | data folder root (flat filenames) |
| Tester agent logs | `C:\Users\Benja\AppData\Roaming\MetaQuotes\Tester\53785E099C927DB68A545C249CDBCE06\Agent-127.0.0.1-300N\logs\<yyyymmdd>.log` |
| Journal / changelog | repo `JOURNAL.md`, `CHANGELOG.md` |
| Older data-analysis skill | repo `.claude/skills/mgnfy-journal-analysis/` |

Account: Exness demo `Exness-MT5Trial15`, **hedging mode**, leverage 1:100, symbol **XAUUSDm**
(point 0.001; at 0.01 lot, a 1.00 price move = $1.00; minimum lot 0.01; typical spread 260 points =
0.26). Server time is UTC.

Repo scripts:

| Script | Purpose |
|---|---|
| `mt5_mode_compare.py` | Main runner: entry modes side by side on chosen weeks through the real tester |
| `mt5_week_check.py` | Helpers `run_test()` / `make_ini()`, plus random-week checks with the user's inputs |
| `mt5_deep_parse.py` | `parse_one(report.htm)` -> per-trade DataFrame (entry/exit, initial SL, R, hold, exit kind) |
| `swing_log_summary.py` | Swing-mode order flow per run from tester logs (bias checks, placed/kept/filled/cancelled, skips) |
| `study_swing_sl.py` | Example calibrated replay study (stop buffer, order distance) on M1 bars |
| `mt5_journal.py` | First real-tester batch runner (v1.11, Balance preset) -- historical |
| `ini_runs/visualcheck_H1_20260907.ini` | The user's exact tester inputs; base for all current runs |

## 2. EA architecture (v1.15)

Entry mode is chosen by `InpEntryMode`:
- `ENTRY_REGIME_BREAKOUT` (0, default) -- market orders from an ATR "regime channel" midline/band cross.
- `ENTRY_SWING_PULLBACK` (1) -- multi-timeframe bias plus limit orders at M30 swings.

`OnInit()`: `TesterHideIndicators(true)`, removes leftover line objects, creates indicator handles
(`EnsureHandles()`), builds the HUD.

`OnTick()` flow:
1. `UpdateHUD()`, push MT5's own trade markers behind the HUD.
2. `IsNewBar()` on `InpTF`; `CopyLatest()` reads close0/close1 and bar-0 high/low (see audit: bar 0 is
   the forming bar), ATR, MACD, EMA cloud.
3. Regime channel `up1/dn1` (SuperTrend-like trailing bands from `hlMid +/- InpATRMultiplier*ATR`) and
   `trend`.
4. Breakout signals: midline (`InpUseMidlineBreakout`) or band cross, optional 2-bar confirm, optional
   trend-flip requirement, optional MACD filter.
5. Filters: margin (`InpEnableMarginCheck`, `InpMarginBuffer`), spread (`InpMaxSpreadPoints`), session
   hours (`InpUseSessionFilter`, server time), one position (`InpOnlyOnePosition`), higher-TF EMA trend
   filter (`InpUseTrendFilter`, `InpTrendTF`, `InpTrendEMALength`).
6. Swing mode block: at each new H1 bar, `ComputeBias()` then `PlanSwingEntry()` if flat (breakout
   signals are forced off in this mode).
7. Breakout entries (new bar only): market buy/sell, SL = `InpSL_ATR_Mult * ATR` (or percent),
   lot = fixed `InpLots` or risk-based (`InpUseRiskSizing`), margin-adjusted.
8. Small-account partial capture when equity <= `InpSmallCapThreshold`.
9. Management of the open position: TP1/TP2/TP3 at `InpTP*_R_Mult` x R (breakout: R from current ATR;
   swing: R from the stored planned SL, TP1 = planned opposite swing); partial closes; **stairstep lock**
   (SL moves to TP1, then TP2); ATR trailing `InpTrail_ATR_Mult * ATR(InpTF)`; TP3 closes the rest.
   `MoveSLto()` skips changes under 500 points.

Swing mode functions: `FindSwings()` (fractal, `InpSwingStrength` bars each side, last 300 bars),
`TimeframeBias()` (last closed bar vs rising/falling EMA `InpBiasEMALength` + HH/HL or LH/LL),
`ComputeBias()` (`InpBiasMinAgree` of M30/H1/H4), `BuildSwingPlan()` (latest swing on the right side
within `InpSwingMaxDistATR` x ATR(`InpSwingTF`), SL = swing -/+ `InpSwingSLBufferATR` x ATR, TP1 =
opposite swing, skip if reward < `InpSwingMinRR` x risk), `PlanSwingEntry()` (keeps an existing order
unless the bias flipped, it turned neutral with `InpSwingCancelOnWait`, price is too far, or the level
changed), `SwingTargets()`.

HUD: STATS and RISK CALC tabs, session line (Tokyo/London/NY/overlap/break/weekend, UTC with DST),
bias and pending order in swing mode. `OnChartEvent` (tab clicks, calculator edits) does not run in the
tester.

## 3. The user's test settings

From `ini_runs/visualcheck_H1_20260907.ini` (the user's own Strategy Tester inputs): tester chart H1,
`InpTF` = M15, fixed 0.01 lot, ATR 14, `InpATRMultiplier` 2.0, `InpSL_ATR_Mult` 1.0, TP at 1R/2R/3R
closing 33%/33%, move-to-BE (stairstep) on, midline breakout on, confirm bars 1, trend flip off, MACD
filter off, **trend filter on with `InpTrendTF` = H1 (16385), EMA 200**, session filter off, ATR trailing
1.5, max spread 400, margin buffer 1.2, `InpSmallCapThreshold` 100. Swing inputs not in the ini use EA
defaults (EMA 50, 2 of 3 agree, M30 swings, strength 2, SL buffer 0.3 ATR, min RR 1.0, max distance
3 ATR, cancel on wait off).

The user also runs visual tests on M5 with `InpTF` = M5.

## 4. Tooling: compile, run, parse

**Compile** (use PowerShell; Git Bash rewrites `/compile:` arguments and nothing happens):

```powershell
$me  = "C:\Program Files\MetaTrader 5 EXNESS\MetaEditor64.exe"
$dir = "C:\Users\Benja\AppData\Roaming\MetaQuotes\Terminal\53785E099C927DB68A545C249CDBCE06\MQL5\Experts"
$src = Join-Path $dir "MGNFY GOLD.mq5"
Copy-Item "<repo>\MGNFY GOLD.mq5" $src -Force
$log = "<scratch>\compile_<time>.log"   # a new file each time; avoid Remove-Item near Program Files paths
Start-Process -FilePath $me -ArgumentList "/compile:`"$src`" /log:`"$log`"" -Wait
Get-Content $log -Encoding Unicode | Select-String "Result:|error|warning"
```

**Run a batch** (from the repo root; closes MT5, runs each test with `ShutdownTerminal=1`, parses):

```bash
# weeks: WEEKS=4 (Aug 10, Aug 17, Aug 31, Sep 7), WEEKS=12 (Jun 22 - Sep 11), or any Monday + count
WEEK_START=2026-03-02 WEEK_COUNT=12 TAG=holdoutA python mt5_mode_compare.py swing
# override EA inputs for this batch (semicolon-separated; replaces the base ini value or appends it)
EXTRA_INPUTS="InpSwingSLBufferATR=0.5;InpUseSessionFilter=true" TAG=expX WEEKS=12 python mt5_mode_compare.py swing
```

Outputs: per-week and pooled stats table on stdout, `mode_compare_trades<TAG>.csv` in the repo root,
reports `cmp<TAG>_<mode>_<week>__M15sig.htm` in the MT5 data folder. After a batch, check the tester
log's "started with inputs" list to confirm overrides took effect. A 12-week pair takes ~15 minutes.

**Swing order flow:** `python swing_log_summary.py HH:MM [HH:MM] [YYYYMMDD]` (runs started in that
real-time window).

**Tester ini input format:** `Name=value||start||step||stop||N`; inputs not listed use EA defaults; enums
as integers (`InpEntryMode` 0/1); timeframes as MT5 codes: M1=1, M5=5, M15=15, M30=30, H1=16385,
H4=16388, D1=16408.

## 5. MT5 gotchas

- **Close the terminal before every `/config` launch.** A `/config` sent to an already-running
  terminal is merged into it and silently reuses its last settings. `run_test()` kills `terminal64.exe`
  first.
- **`Report=` must be a flat filename**; a subfolder path silently produces no report. Reports land in
  the data folder root.
- **Tester logs are UTF-16 and split across agents.** MT5 moved to agent `3001` mid-session when agent
  `3000`'s daily log reached ~170 MB. Read every `Agent-*` log. When waiting on a running test, read
  new bytes from a saved file offset -- the log grows by hundreds of lines per second, so tail-based
  checks miss lines.
- **Only one tester batch at a time.**
- **Visual runs:** `Visual=1`, `ShutdownTerminal=0`; the visualization window belongs to
  `metatester64.exe` (title starts "Strategy Tester Visualization"). Stop it and `terminal64.exe` before
  the next run.
- **$100 deposit** hits a ~$53 margin floor with 0.01 lot at ~$4,400 gold and stops trading mid-week.
  Use $500 for strategy evaluation.
- **Weeks:** `FromDate` Monday, `ToDate` Saturday (the runner uses start + 5 days).
- **Time:** Exness server time = UTC; in the tester `TimeGMT()` = simulated server time.
- **Safety checks** in this environment have blocked commands that look like deploying or deleting near
  protected paths. If a compile or copy is blocked, ask the user rather than working around it.

## 6. Data inventory and which weeks are clean

Real tick data (tester `Model=4`) confirmed for: **2026-01-05/06** (831,659 ticks, trades executed),
**2026-04-06/07** (812,799 ticks), and continuously **2026-06-15 to 2026-09-15**. Assume Jan-Sep 2026 is
available but check each new week's report has trades and the log has a ticks line.

| Weeks | Status |
|---|---|
| Jun 22 - Sep 11, 2026 (12 full weeks) | **Seen** -- used repeatedly in diagnosis and tuning. In-sample only. |
| Aug 1 - Sep 14, 2026 | Seen -- the user's original GUI backtest |
| Jan 5 - Jun 12, 2026 (~23 full weeks) | **Never analyzed** -- use as validation and holdout |

Suggested split: in-sample = Jun 22 - Sep 11; validation = Mar 2 - May 22 (12 weeks); holdout =
Jan 5 - Feb 27 (8 weeks), run once for final candidates only.

Trade data already in the repo (one row per trade):

| File | Batch | Trades |
|---|---|---|
| `mt5_journal_trades.csv` | v1.11, Balance preset, $100, 5 random weeks x M15/M30/H1 | 481 |
| `mt5_weekcheck_v113_trades.csv` | v1.13, user's inputs, $100, 4 weeks | 232 |
| `mt5_modecompare_v114_trades.csv` | v1.14 breakout vs swing, $500, 4 weeks | 335 |
| `mt5_modecompare_v115_12wk_trades.csv` | v1.15 breakout vs swing, $500, 12 weeks | 1,020 |

The raw `.htm` reports behind these and the tester logs exist only on the user's PC.

## 7. Current baseline results

v1.15, user's inputs, $500, real ticks, 12 weeks (Jun 22 - Sep 11):

| Mode | Trades | Trades/day | Win% | Net $ | PF | Avg win / loss $ | Weeks + / - | Worst weekly DD | Median loser hold |
|---|---|---|---|---|---|---|---|---|---|
| Breakout | 943 | 15.7 | 34.4 | -300.18 | 0.93 | 12.34 / -6.94 | 6 / 6 | 50% | 29 min |
| Swing | 77 | 1.3 | 19.5 | -55.80 | 0.72 | 9.66 / -3.24 | 4 / 8 | 4.8% | 5 min |

Neither mode is profitable. Breakout's entry is close to random (see `ea-code-audit.md`, verified issue
1). Swing's orders fill as price pushes through the level and most losers are stopped within minutes.

## 8. Experiments already done -- don't repeat

| Question | Answer | Where |
|---|---|---|
| Does the TP ladder fire at 0.01 lot? | No in v1.11; fixed in v1.12 | JOURNAL, CHANGELOG 1.12 |
| $100 vs $500 deposit | $100 hits a margin floor; use $500 | JOURNAL v1.14 entry |
| Breakout vs swing (4 weeks) | Swing +$20.90 on 20 trades -- small sample | JOURNAL v1.14 |
| Swing stop buffer 0.3-3.0 x ATR (replay, calibrated) | Every wider buffer lost more; keep 0.3 | JOURNAL stop study |
| Swing order distance vs fill rate | 3+ ATR away: 0 of 49 filled; limit 3 ATR | JOURNAL stop study |
| Keep swing orders across hourly checks | Fill rate 12% -> 38.5%, but extra fills mostly lost | JOURNAL v1.15 |
| Breakout vs swing (12 weeks) | Both lose (table above) | JOURNAL v1.15 |
| Session / weekday patterns (232 trades) | Worst: London+NY overlap and Asia; too few trades to act | JOURNAL 4-week diagnosis |
| v1.16 defaults = v1.15? | Yes, trades identical on Jun 22 + Jul 6, both modes | JOURNAL review round 1 |
| Manual trade on a hedging account (v1.15) | Manual position untouched; EA copied its TP and spammed modifies; fixed in v1.16 | JOURNAL review round 1, harness in review report |
| E1 swing confirmation entry (sweep + M5 reclaim), 12 wk IS | 56 trades, PF 1.01, +$2.30; fast stop-outs 55% -> 11%; not promoted | JOURNAL review round 1 |
| E2 closed-bar regime flip (breakout), 12 wk IS | 124 trades, PF 1.01, +$6.88, DD 12.3%; not promoted | JOURNAL review round 1 |
| E3 flip only with M30/H1/H4 bias (screen of E2 trades) | agree 23 trades PF 1.05; not run | JOURNAL review round 1 |

v1.16 (2026-09-15) added `InpBreakoutClosedBar`, `InpSwingEntryStyle`, `InpSwingSweepMaxATR` (all default
off) and the hedging `MoveSLto()` fix. Validation (Mar 2 - May 22) and holdout (Jan 5 - Feb 27) weeks are
still unused for strategy decisions. About 8 ideas have been tried on the Jun 22 - Sep 11 weeks.

Ideas raised but **not yet tested**: exit management in MT5 (stairstep lock to TP1 price and trail 1.5 were
chosen with the rejected Python simulator), structure-based trailing, session filter to London/NY (E1's
session split showed nothing), news blackout from an imported schedule, risk-based sizing comparison,
throttling stop modifications while the market is closed (7,811 rejected requests in one 2-day run).

## 9. History

- v1.11 (2025-11): original Market product; TP ladder dead at 0.01 lot.
- A previous AI session built a Python bar simulator and journal; the user showed it disagreed with MT5;
  removed 2026-09-15. Only real-tester data since.
- v1.12: TP ladder fix, stairstep lock, trail 1.5, XAUUSDm symbol.
- v1.13: HUD rewrite (tabs, risk calculator), chart line cleanup, trailing min step (2,756 -> 232
  modify requests), HUD visibility fixes, MT5 trade markers behind HUD, session line.
- v1.14: swing-pullback entry mode.
- v1.15: swing orders kept across checks, nearby swings only.
