"""Real-MT5-Strategy-Tester journal runner for MGNFY GOLD.

Unlike the removed Python offline engine, this drives MT5's OWN Strategy
Tester (terminal64.exe /config:<ini>, Model=4 "every tick based on real
ticks") -- the exact same engine + data the user's manual GUI backtest
used. Every trade comes straight from the tester's own Deals table; no
custom bar-stepping simulation is involved.

Requires the MT5 terminal to be fully closed before each run (a config
passed to an already-running instance silently ignores the requested
dates -- confirmed empirically this session) -- this script kills any
running terminal64.exe/metatester64.exe before every launch.
"""
import os
import random
import subprocess
import time
from datetime import datetime, timedelta

import pandas as pd

TERMINAL_EXE = r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe"
DATA_PATH = r"C:\Users\Benja\AppData\Roaming\MetaQuotes\Terminal\53785E099C927DB68A545C249CDBCE06"
INI_DIR = r"C:\Users\Benja\AppData\Local\Temp\claude\C--Users-Benja-OneDrive-Pictures-MSB-OB\c739d792-d8b9-4d83-b2a2-028661b569de\scratchpad\ini_runs"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Same input block as the user's own manual GUI backtest (Balance-preset-equivalent --
# ATRMultiplier=2.0, StopLossPercent=0.7, MACD off -- confirmed by matching the on-chart
# HUD readout in the user's screenshot). Only InpTF changes between runs.
TESTER_INPUTS_TEMPLATE = """InpSymbol=XAUUSDm
InpTF={tf_code}||0||0||49153||N
InpLots=0.01||0.01||0.001000||0.100000||N
InpATRPeriod=14||14||1||140||N
InpATRMultiplier=2.0||2.0||0.200000||20.000000||N
InpStopLossPercent=0.7||0.7||0.070000||7.000000||N
InpUseMACDFilter=false||false||0||true||N
InpMACDFast=12||12||1||120||N
InpMACDSlow=26||26||1||260||N
InpMACDSignal=9||9||1||90||N
InpCloudLength=20||20||1||200||N
InpDrawVisuals=false||false||0||true||N
InpShowCloud=false||false||0||true||N
InpSlippagePoints=30||30||1||300||N
InpMagic=20251029||20251029||1||202510290||N
InpTP1CloseFrac=0.33||0.33||0.033000||3.300000||N
InpTP2CloseFrac=0.33||0.33||0.033000||3.300000||N
InpMoveToBEafterTP1=true||false||0||true||N
InpOnlyOnePosition=true||false||0||true||N
InpEnableMarginCheck=true||false||0||true||N
InpMarginBuffer=1.2||1.2||0.120000||12.000000||N
InpMaxSpreadPoints=400||400||1||4000||N
InpUseATRStops=true||false||0||true||N
InpSL_ATR_Mult=1.0||1.0||0.100000||10.000000||N
InpTP1_R_Mult=1.0||1.0||0.100000||10.000000||N
InpTP2_R_Mult=2.0||2.0||0.200000||20.000000||N
InpTP3_R_Mult=3.0||3.0||0.300000||30.000000||N
InpUseRiskSizing=false||false||0||true||N
InpRiskPercent=1.0||1.0||0.100000||10.000000||N
InpRequireTrendFlip=false||false||0||true||N
InpBreakoutConfirmBars=1||1||1||10||N
InpUseMidlineBreakout=true||false||0||true||N
InpUseTrendFilter=false||false||0||true||N
InpTrendTF=16385||0||0||49153||N
InpTrendEMALength=200||200||1||2000||N
InpUseSessionFilter=false||false||0||true||N
InpSessionStartHour=12||12||1||120||N
InpSessionEndHour=22||22||1||220||N
InpUseATRTrailing=true||false||0||true||N
InpTrail_ATR_Mult=1.5||1.0||0.100000||10.000000||N
InpVisualKeepBars=1||1||1||10||N
InpStatsAccountWide=false||false||0||true||N
InpStatsTodayOnly=true||false||0||true||N
InpStatsFromAttach=false||false||0||true||N
InpStatsWindowMinutes=0||0||1||10||N
InpResetHUD=false||false||0||true||N
InpTrendRequireSlope=false||false||0||true||N
InpDeclaredCapital=0.0||0.0||0.000000||0.000000||N
InpSmallCapThreshold=300||300.0||30.000000||3000.000000||N
InpSmallProfitAbs=2.0||2.0||0.200000||20.000000||N
InpSmallProfitPct=0.5||0.5||0.050000||5.000000||N
InpSmallPartialFrac=0.5||0.5||0.050000||5.000000||N
InpSmallMoveToBE=true||false||0||true||N
InpSmallBEBufferPts=10||10||1||100||N
"""

TF_CODES = {"M15": "15", "M30": "30", "H1": "16385"}


def build_ini(period_label, tf_code, from_date, to_date, report_name):
    return f"""[Tester]
Expert=MGNFY GOLD.ex5
Symbol=XAUUSDm
Period={period_label}
Optimization=0
Model=4
FromDate={from_date:%Y.%m.%d}
ToDate={to_date:%Y.%m.%d}
ForwardMode=0
Deposit=100
Currency=USD
ProfitInPips=0
Leverage=100
ExecutionMode=0
OptimizationCriterion=0
Visual=0
Report={report_name}
ReplaceReport=1
ShutdownTerminal=1
[TesterInputs]
{TESTER_INPUTS_TEMPLATE.format(tf_code=tf_code)}"""


def kill_mt5():
    subprocess.run(["taskkill", "/IM", "terminal64.exe", "/F"], capture_output=True)
    time.sleep(2)


def run_test(period_label, from_date, to_date, run_id):
    tf_code = TF_CODES[period_label]
    ini_path = os.path.join(INI_DIR, f"{run_id}.ini")
    report_name = run_id
    with open(ini_path, "w") as f:
        f.write(build_ini(period_label, tf_code, from_date, to_date, report_name))

    report_path = os.path.join(DATA_PATH, f"{report_name}.htm")
    if os.path.exists(report_path):
        os.remove(report_path)

    kill_mt5()
    t0 = time.time()
    subprocess.run([TERMINAL_EXE, f"/config:{ini_path}"], timeout=600)
    elapsed = time.time() - t0

    # ShutdownTerminal should close it, but confirm and force-kill as a safety net
    time.sleep(1)
    kill_mt5()

    if not os.path.exists(report_path):
        print(f"  [FAIL] {run_id}: no report produced after {elapsed:.1f}s")
        return None
    return report_path


def parse_report(report_path, run_id, period_label, week_label):
    tables = pd.read_html(report_path, flavor="lxml")
    deals = tables[1]
    hdr_idx = deals.index[deals[0] == "Deals"][0]
    deals = deals.iloc[hdr_idx + 2:].copy()
    deals.columns = ["time", "deal", "symbol", "type", "direction", "volume",
                      "price", "order", "commission", "swap", "profit", "balance", "comment"]
    deals = deals.dropna(subset=["time"])
    deals["time"] = pd.to_datetime(deals["time"], errors="coerce")
    deals = deals.dropna(subset=["time"])
    deals["profit"] = pd.to_numeric(deals["profit"], errors="coerce")
    deals["balance"] = pd.to_numeric(deals["balance"], errors="coerce")

    ins = deals[deals["direction"] == "in"].reset_index(drop=True)
    outs = deals[deals["direction"] == "out"].reset_index(drop=True)
    n = min(len(ins), len(outs))
    ins, outs = ins.iloc[:n], outs.iloc[:n]

    trades = pd.DataFrame({
        "run_id": run_id, "week": week_label, "signal_tf": period_label,
        "entry_time": ins["time"].values, "dir": ins["type"].str.upper().values,
        "entry_price": pd.to_numeric(ins["price"], errors="coerce").values,
        "exit_time": outs["time"].values,
        "exit_price": pd.to_numeric(outs["price"], errors="coerce").values,
        "exit_comment": outs["comment"].values,
        "volume": pd.to_numeric(ins["volume"], errors="coerce").values,
        "pnl": outs["profit"].values,
        "balance_after": outs["balance"].values,
    })
    return trades


def summarize(trades, deposit=100.0):
    if trades.empty:
        return dict(trades=0, wins=0, losses=0, win_rate=0.0, net=0.0, pf=0.0,
                     max_dd_pct=0.0, avg_win=0.0, avg_loss=0.0, max_win=0.0, max_loss=0.0,
                     max_consec_wins=0, max_consec_losses=0, end_eq=deposit)
    pnl = trades["pnl"].to_numpy()
    wins, losses = pnl[pnl > 0], pnl[pnl <= 0]
    bal = trades["balance_after"].to_numpy()
    peak = pd.Series(bal).cummax().to_numpy()
    dd = (peak - bal) / peak * 100

    def streak(mask):
        best = cur = 0
        for m in mask:
            cur = cur + 1 if m else 0
            best = max(best, cur)
        return best

    return dict(
        trades=len(pnl), wins=len(wins), losses=len(losses),
        win_rate=len(wins) / len(pnl) * 100, net=pnl.sum(),
        pf=(wins.sum() / abs(losses.sum())) if len(losses) and losses.sum() != 0 else float("inf"),
        max_dd_pct=dd.max() if len(dd) else 0.0,
        avg_win=wins.mean() if len(wins) else 0.0, avg_loss=losses.mean() if len(losses) else 0.0,
        max_win=wins.max() if len(wins) else 0.0, max_loss=losses.min() if len(losses) else 0.0,
        max_consec_wins=streak(pnl > 0), max_consec_losses=streak(pnl <= 0),
        end_eq=bal[-1] if len(bal) else deposit,
    )


def candidate_mondays(earliest, latest_full_week_end_excl):
    d = earliest
    d += timedelta(days=(7 - d.weekday()) % 7)
    out = []
    while d + timedelta(days=7) <= latest_full_week_end_excl:
        out.append(d)
        d += timedelta(days=7)
    return out


def main():
    earliest = datetime(2026, 6, 16)  # first Monday after confirmed M1/tick data floor (2026-06-15)
    now = datetime.now()
    candidates = candidate_mondays(earliest, now)
    rng = random.SystemRandom()
    n_weeks = int(os.environ.get("N_WEEKS", "5"))
    weeks = sorted(rng.sample(candidates, k=min(n_weeks, len(candidates))))

    print(f"Candidate weeks: {len(candidates)} ({candidates[0].date()} .. {candidates[-1].date()})")
    print("RANDOMLY SELECTED (SystemRandom, pre-registered before any result seen):")
    for w in weeks:
        print(f"  {w.date()} -> {(w + timedelta(days=6)).date()}")
    print()

    all_trades = []
    summary_rows = []

    for week_start in weeks:
        week_end = week_start + timedelta(days=7)
        week_label = f"{week_start.date()}_to_{(week_end - timedelta(days=1)).date()}"
        for period_label in ["M15", "M30", "H1"]:
            run_id = f"{week_label}__{period_label}"
            print(f"Running {run_id} ...", flush=True)
            report_path = run_test(period_label, week_start, week_end, run_id)
            if report_path is None:
                summary_rows.append(dict(run_id=run_id, week=week_label, signal_tf=period_label,
                                          trades=0, wins=0, losses=0, win_rate=0, net=0, pf=0,
                                          max_dd_pct=0, avg_win=0, avg_loss=0, max_win=0, max_loss=0,
                                          max_consec_wins=0, max_consec_losses=0, end_eq=100.0,
                                          status="FAILED"))
                continue
            trades = parse_report(report_path, run_id, period_label, week_label)
            stats = summarize(trades)
            stats.update(run_id=run_id, week=week_label, signal_tf=period_label, status="OK")
            summary_rows.append(stats)
            all_trades.append(trades)
            print(f"  trades={stats['trades']:>4} win%={stats['win_rate']:>6.1f} "
                  f"PF={stats['pf']:>6.2f} net$={stats['net']:>9.2f} maxDD%={stats['max_dd_pct']:>6.1f} "
                  f"end_eq={stats['end_eq']:>8.2f}")

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(os.path.join(OUT_DIR, "mt5_journal_summary.csv"), index=False)
    if all_trades:
        trades_df = pd.concat(all_trades, ignore_index=True)
        trades_df.to_csv(os.path.join(OUT_DIR, "mt5_journal_trades.csv"), index=False)
        print(f"\nWrote {len(summary_rows)} run rows, {len(trades_df)} trades total.")
    else:
        print("\nNo trades collected.")


if __name__ == "__main__":
    main()
