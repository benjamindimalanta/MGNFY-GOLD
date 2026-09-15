//+------------------------------------------------------------------+
//|                                                XAU_Gold_ATR_Regime_EA.mq5
//|   ATR regime flip entries with SL and 1R/2R/3R partial TPs, visuals, MACD filter
//+------------------------------------------------------------------+
//| v1.12 (2026-09-15) changes, backtested against 2 years of real   |
//| XAUUSDm broker data (see MGNFY_GOLD_LIVE/JOURNAL.md for the full |
//| trace of every test that led here):                              |
//|                                                                  |
//|  1. BUGFIX: at min lot size (0.01), a 33% partial close rounds   |
//|     to 0.00 and ClosePartial() silently fails. tp1Hit/tp2Hit     |
//|     previously never became true in that case, so the whole     |
//|     breakeven-move / TP2 / TP3 chain never fired. Now the level  |
//|     always counts as "hit" once price reaches it, regardless of  |
//|     whether a partial close was physically possible.             |
//|  2. Stairstep stop lock replaces flat breakeven: SL now moves to |
//|     TP1's price (not flat entry) after TP1, and to TP2's price   |
//|     after TP2 — instead of parking at entry the whole time.      |
//|     Tested: profit factor 0.70 -> 0.87 vs the old behavior.      |
//|  3. InpTrail_ATR_Mult default raised 1.0 -> 1.5 — tested as the  |
//|     best pairing with the stairstep lock (too tight combined     |
//|     with stairstep cuts winners short; 1.5x gave the best        |
//|     result of the values tried).                                 |
//+------------------------------------------------------------------+
//| v1.13 (2026-09-15) changes:                                      |
//|  1. Full HUD rewrite: tabbed panel (STATS / RISK CALCULATOR)      |
//|     instead of one static block. Stats tab now shows balance,     |
//|     equity, floating & realized P/L, win rate, win/loss counts,   |
//|     profit factor, max drawdown, and the currently open           |
//|     position's direction/entry/SL/TP1-TP2 status -- none of that  |
//|     existed before except win/loss counts and floating P/L.       |
//|  2. Risk Calculator tab: editable entry price / lot size / TP     |
//|     price / SL price, computed via the broker's own               |
//|     OrderCalcProfit() (not hand-rolled pip math), showing $ gain  |
//|     at TP, $ loss at SL, and the resulting risk:reward ratio.     |
//|  3. Dark, high-contrast, gold-accent theme (previous panel was a  |
//|     plain white box, which the file's own #property description  |
//|     had claimed was "dark-themed" without actually being so).     |
//|  4. Entry/SL/TP lines are drawn in the chart background so they  |
//|     no longer cut across the HUD (MT5 draws foreground objects   |
//|     in creation order; OBJPROP_ZORDER is click priority only).   |
//|     Tester visual mode no longer adds indicator sub-windows,     |
//|     which had shrunk the chart and cut off the bottom of the HUD.|
//+------------------------------------------------------------------+
//| v1.14 (2026-09-15): optional swing-pullback entry mode           |
//|  (InpEntryMode). Bias per timeframe = price vs a rising/falling  |
//|  EMA plus higher highs/lows (or lower) on M30, H1, H4, and       |
//|  InpBiasMinAgree of them must agree. At each new H1 bar any       |
//|  unfilled pending order is cancelled and a limit order is placed |
//|  at the latest M30 swing low (buy) / high (sell), SL beyond it   |
//|  by a fraction of ATR, TP1 at the opposite swing, TP2/TP3 from   |
//|  the stored risk distance. Default mode is unchanged.            |
//+------------------------------------------------------------------+
#property copyright "Visit product page"
#property link      "https://www.mql5.com/en/market/product/154202"
#property version   "1.14"
#property description "ATR Regime Breakouts with EMA midline and ATR bands. Tabbed HUD: live stats + risk calculator."
#property description "Entries: regime flip or breakout with 1–2 bar confirmation."
#property description "Risk: ATR-based SL/TP (1R/2R/3R), partial exits, stairstep lock at TP1/TP2."
#property description "Management: optional ATR trailing; spread/margin/session filters."
#property description "Trend filter: higher‑timeframe EMA (+ optional slope)."
#property description "HUD: tabbed panel -- live stats and a risk calculator."
#property description "Optional small-account mode: partial capture + BE buffer."
#include <Trade/Trade.mqh>
CTrade Trade;

enum ENUM_ENTRY_MODE
{
  ENTRY_REGIME_BREAKOUT = 0, // Regime breakout (market orders)
  ENTRY_SWING_PULLBACK  = 1  // Swing pullback (limit orders, M30/H1/H4 bias)
};

//-------------------- Inputs --------------------
input string   InpSymbol               = "XAUUSDm";        // Symbol to trade
input ENUM_TIMEFRAMES InpTF            = PERIOD_CURRENT;  // Working timeframe
input double   InpLots                 = 0.01;            // Fixed lot size
input int      InpATRPeriod            = 14;              // ATR Length
input double   InpATRMultiplier        = 2.0;             // Sensitivity/ATR Multiplier
input double   InpStopLossPercent      = 0.7;             // SL % of price (0.7% default). 0 disables
input bool     InpUseMACDFilter        = false;           // Require MACD line > 0 for longs and < 0 for shorts
input int      InpMACDFast             = 12;
input int      InpMACDSlow             = 26;
input int      InpMACDSignal           = 9;
input int      InpCloudLength          = 20;              // EMA(high/low) cloud length (visual)
input bool     InpDrawVisuals          = true;            // Draw Entry/SL/TP lines and EMA cloud
input bool     InpShowCloud            = false;           // If true, draw EMA(high/low) cloud levels
input int      InpSlippagePoints       = 30;              // Max slippage in points
input int      InpMagic                = 20251029;        // Magic number
input double   InpTP1CloseFrac         = 0.33;            // Close 33% at TP1
input double   InpTP2CloseFrac         = 0.33;            // Close 33% at TP2 (rest at TP3)
input bool     InpMoveToBEafterTP1     = true;            // Move SL to BE after TP1
input bool     InpOnlyOnePosition      = true;            // Only one open position at a time

// Risk and infrastructure
input bool     InpEnableMarginCheck    = true;            // Block entries if margin is insufficient
input double   InpMarginBuffer         = 1.20;            // Required margin buffer multiplier (e.g. 1.20 = 20%)
input int      InpMaxSpreadPoints      = 400;             // Disallow entries if spread > this (points). 0 = disabled

// Adaptive risk & stops
input bool     InpUseATRStops          = true;            // Use ATR-based SL/TP instead of percent
input double   InpSL_ATR_Mult          = 1.0;             // SL = k * ATR
input double   InpTP1_R_Mult           = 1.0;             // TP1 = 1R
input double   InpTP2_R_Mult           = 2.0;             // TP2 = 2R
input double   InpTP3_R_Mult           = 3.0;             // TP3 = 3R
input bool     InpUseRiskSizing        = false;           // Size lots by risk % of equity
input double   InpRiskPercent          = 1.0;             // Risk percent of equity per trade
input bool     InpRequireTrendFlip     = false;           // If false, enter on direct band/midline break (more entries)
input int      InpBreakoutConfirmBars  = 1;               // Bars to confirm breakout (1 = close1 inside, close0 outside)
input bool     InpUseMidlineBreakout   = true;            // If true, use hlMid breakout instead of band breakout

// Entry style
input ENUM_ENTRY_MODE InpEntryMode     = ENTRY_REGIME_BREAKOUT; // Entry style (swing pullback ignores the breakout and trend-filter inputs)
input int      InpBiasEMALength        = 50;              // Swing mode: EMA length for the bias on M30/H1/H4
input int      InpBiasMinAgree         = 2;               // Swing mode: how many of M30/H1/H4 must agree (1-3)
input ENUM_TIMEFRAMES InpSwingTF       = PERIOD_M30;      // Swing mode: timeframe of the swing points used for entry and TP1
input int      InpSwingStrength        = 2;               // Swing mode: bars on each side that define a swing high/low
input double   InpSwingSLBufferATR     = 0.3;             // Swing mode: SL beyond the entry swing by this x ATR(swing TF)
input double   InpSwingMinRR           = 1.0;             // Swing mode: skip if TP1 distance < this x SL distance

// Trend/time filters
input bool     InpUseTrendFilter       = true;            // Trade only with higher-timeframe EMA trend
input ENUM_TIMEFRAMES InpTrendTF       = PERIOD_H4;       // Trend timeframe
input int      InpTrendEMALength       = 200;             // Trend EMA length
input bool     InpUseSessionFilter     = false;           // Restrict trading hours (server time)
input int      InpSessionStartHour     = 12;              // Start hour (inclusive)
input int      InpSessionEndHour       = 22;              // End hour (exclusive)

// Trailing stop
input bool     InpUseATRTrailing       = true;            // Trail stop using ATR
input double   InpTrail_ATR_Mult       = 1.5;             // Trail distance in ATRs (was 1.0; 1.5 tested best with stairstep lock)
input int      InpVisualKeepBars       = 1;               // Unused since v1.13 (Entry/SL/TP lines are now one persistent object each, moved not re-created -- see DrawLine/CleanupOldVisuals). Kept only so old presets referencing it still load.
// Stats options
input bool     InpStatsAccountWide     = false;           // If true, HUD profit uses all symbols/magics (account-wide)
input bool     InpStatsTodayOnly       = true;            // Sum realized profit for today only (matches MT5 'Today')
input bool     InpStatsFromAttach      = false;           // Start stats from the moment EA is (re)attached
input int      InpStatsWindowMinutes   = 0;               // Rolling window in minutes (0 = disabled)
input bool     InpResetHUD             = false;           // Set to true and recompile/apply to reset HUD baseline

// Trend slope requirement
input bool     InpTrendRequireSlope    = false;           // If true, EMA must slope with trade

// --- Small-account profit capture settings
input double   InpDeclaredCapital      = 0.0;   // 0 = use account equity; else declared capital
input double   InpSmallCapThreshold    = 300.0; // <= this => small-account behaviour active (USD)
input double   InpSmallProfitAbs       = 2.0;   // absolute USD floating profit to capture
input double   InpSmallProfitPct       = 0.5;   // percent of capital (0.5%) to capture
input double   InpSmallPartialFrac     = 0.50;  // fraction to close when small profit condition met
input bool     InpSmallMoveToBE        = true;  // after partial close, move SL to BE + buffer
input int      InpSmallBEBufferPts     = 10;    // BE buffer in points

//-------------------- State ---------------------
int    hATR = INVALID_HANDLE;
int    hEMAHigh = INVALID_HANDLE;
int    hEMALow = INVALID_HANDLE;
int    hMACD = INVALID_HANDLE;
int    hTrendEMA = INVALID_HANDLE;

// Swing-pullback mode state
ENUM_TIMEFRAMES kBiasTFs[3] = {PERIOD_M30, PERIOD_H1, PERIOD_H4};
int      hBiasEMA[3] = {INVALID_HANDLE, INVALID_HANDLE, INVALID_HANDLE};
int      hSwingATR = INVALID_HANDLE;
datetime g_lastBiasBar = 0;   // H1 bar of the last bias check
int      g_bias = 0;          // combined bias: 1 buy, -1 sell, 0 wait
int      g_biasTF[3];         // per-timeframe bias (M30, H1, H4)
double   g_planSL = 0.0;      // SL of the last placed swing order (initial risk reference)
double   g_planTP1 = 0.0;     // TP1 of the last placed swing order

datetime lastBarTime = 0;
double prevUp1 = 0.0, prevDn1 = 0.0;
int    prevTrend = 0;     // -1, 1; 0 means uninitialized
bool   tp1Hit = false;
bool   tp2Hit = false;
ulong  lastTicket = 0;
datetime g_statsStart    = 0;

bool   smallProfitTaken = false; // per-trade flag for small-account partial capture

//-------------------- HUD v2 (tabbed panel: Stats / Risk Calculator) ---------------------
// 2026-09-15: full HUD rewrite. Every object below uses the HUD_PREFIX naming convention so
// OnDeinit can clean up with a single ObjectsDeleteAll(0, HUD_PREFIX) instead of a hand-kept
// list. HUD_Z is the objects' click priority (so the tab buttons win clicks); it does NOT
// affect what is drawn on top. Keeping the Entry/SL/TP lines off the panel is done in
// DrawLine() by putting those lines in the background layer.
#define HUD_PREFIX "MSB_HUD_"
#define HUD_Z      500
int      g_hudTab      = 0;    // 0 = Stats tab, 1 = Risk Calculator tab
bool     g_hudBuilt    = false;
bool     g_calcIsBuy   = true; // risk-calculator direction toggle

// Dark, high-contrast, opaque theme (gold accent -- matches the product name) so the panel reads
// clearly regardless of what candles/colors are behind it.
#define HUD_BG        C'16,18,23'
#define HUD_BORDER    C'201,162,39'
#define HUD_HEADER    C'230,196,90'
#define HUD_TEXT      C'225,228,232'
#define HUD_SUBTEXT   C'140,146,155'
#define HUD_GREEN     C'55,199,120'
#define HUD_RED       C'224,84,84'
#define HUD_TABBG_OFF C'32,36,44'
#define HUD_TABBG_ON  C'201,162,39'
#define HUD_TABFG_OFF C'160,166,175'
#define HUD_TABFG_ON  C'16,18,23'
#define HUD_FIELDBG   C'26,29,36'

int HUD_PanelX = 10;
int HUD_PanelY = 75;   // below the terminal's own toolbar
int HUD_PanelW = 300;
int HUD_PanelH = 460; // fits the taller Stats tab content plus the session lines, with margin

string StatsGlobalName()
{
  return StringFormat("MSB_OB_STATS_START_%s_%d", InpSymbol, InpMagic);
}

// --- Helpers for broker stop levels
int GetStopsLevelPoints()
{
  int lvl = (int)SymbolInfoInteger(InpSymbol, SYMBOL_TRADE_STOPS_LEVEL);
  if(lvl < 0) lvl = 0;
  return lvl;
}

double ClampSLForOrder(int dir, double proposedSL)
{
  double point = SymbolInfoDouble(InpSymbol, SYMBOL_POINT);
  double bid   = SymbolInfoDouble(InpSymbol, SYMBOL_BID);
  double ask   = SymbolInfoDouble(InpSymbol, SYMBOL_ASK);
  double minDist = GetStopsLevelPoints() * point + 2.0 * point; // small cushion
  if(dir == POSITION_TYPE_BUY)
  {
    if(proposedSL <= 0.0 || proposedSL >= bid) return 0.0; // invalid side; send without SL
    double maxSL = bid - minDist;
    double sl = MathMin(proposedSL, maxSL);
    if(sl <= 0.0 || sl >= bid) return 0.0;
    return NormalizeDouble(sl, _Digits);
  }
  else
  {
    if(proposedSL <= 0.0 || proposedSL <= ask) return 0.0;
    double minSL = ask + minDist;
    double sl = MathMax(proposedSL, minSL);
    if(sl <= ask) return 0.0;
    return NormalizeDouble(sl, _Digits);
  }
}

double ClampSLForModify(int dir, double desiredSL)
{
  double point = SymbolInfoDouble(InpSymbol, SYMBOL_POINT);
  double bid   = SymbolInfoDouble(InpSymbol, SYMBOL_BID);
  double ask   = SymbolInfoDouble(InpSymbol, SYMBOL_ASK);
  double minDist = GetStopsLevelPoints() * point + 2.0 * point;
  if(dir == POSITION_TYPE_BUY)
  {
    double maxSL = bid - minDist;
    double sl = MathMin(desiredSL, maxSL);
    if(sl <= 0.0 || sl >= bid) return 0.0;
    return NormalizeDouble(sl, _Digits);
  }
  else
  {
    double minSL = ask + minDist;
    double sl = MathMax(desiredSL, minSL);
    if(sl <= ask) return 0.0;
    return NormalizeDouble(sl, _Digits);
  }
}

double AdjustLotsByMargin(double desiredLots, double entryPrice, ENUM_ORDER_TYPE orderType)
{
  double minLot = SymbolInfoDouble(InpSymbol, SYMBOL_VOLUME_MIN);
  double maxLot = SymbolInfoDouble(InpSymbol, SYMBOL_VOLUME_MAX);
  double step   = SymbolInfoDouble(InpSymbol, SYMBOL_VOLUME_STEP);
  if(desiredLots <= 0.0) return 0.0;
  double perLotMargin = 0.0;
  if(!OrderCalcMargin(orderType, InpSymbol, 1.0, entryPrice, perLotMargin))
    return desiredLots; // fallback if broker didn't provide
  double freeMargin = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
  double allowedLots = (perLotMargin > 0.0 ? (freeMargin / (perLotMargin * InpMarginBuffer)) : desiredLots);
  // clamp & step
  allowedLots = MathFloor(allowedLots / step) * step;
  allowedLots = MathMax(0.0, MathMin(maxLot, allowedLots));
  if(allowedLots < minLot) return 0.0; // not enough money for min lot
  // do not increase above desired; we only reduce
  if(allowedLots > desiredLots) allowedLots = desiredLots;
  int stepDigits = (int)MathMax(0, MathRound(-MathLog10(step)));
  return NormalizeDouble(allowedLots, stepDigits);
}

//-------------------- Helpers -------------------
bool IsNewBar()
{
  MqlRates rates[];
  if(CopyRates(InpSymbol, InpTF, 0, 2, rates) != 2) return false;
  if(rates[0].time != lastBarTime)
  {
    lastBarTime = rates[0].time;
    return true;
  }
  return false;
}

bool EnsureHandles()
{
  if(hATR == INVALID_HANDLE)
    hATR = iATR(InpSymbol, InpTF, InpATRPeriod);
  if(hMACD == INVALID_HANDLE)
    hMACD = iMACD(InpSymbol, InpTF, InpMACDFast, InpMACDSlow, InpMACDSignal, PRICE_CLOSE);
  if(hEMAHigh == INVALID_HANDLE)
    hEMAHigh = iMA(InpSymbol, InpTF, InpCloudLength, 0, MODE_EMA, PRICE_HIGH);
  if(hEMALow == INVALID_HANDLE)
    hEMALow = iMA(InpSymbol, InpTF, InpCloudLength, 0, MODE_EMA, PRICE_LOW);
  if(InpUseTrendFilter && hTrendEMA == INVALID_HANDLE)
    hTrendEMA = iMA(InpSymbol, InpTrendTF, InpTrendEMALength, 0, MODE_EMA, PRICE_CLOSE);
  if(InpEntryMode == ENTRY_SWING_PULLBACK)
  {
    for(int i = 0; i < 3; i++)
      if(hBiasEMA[i] == INVALID_HANDLE) hBiasEMA[i] = iMA(InpSymbol, kBiasTFs[i], InpBiasEMALength, 0, MODE_EMA, PRICE_CLOSE);
    if(hSwingATR == INVALID_HANDLE) hSwingATR = iATR(InpSymbol, InpSwingTF, InpATRPeriod);
    if(hBiasEMA[0] == INVALID_HANDLE || hBiasEMA[1] == INVALID_HANDLE || hBiasEMA[2] == INVALID_HANDLE || hSwingATR == INVALID_HANDLE)
      return false;
  }
  return (hATR != INVALID_HANDLE && hMACD != INVALID_HANDLE && hEMAHigh != INVALID_HANDLE && hEMALow != INVALID_HANDLE);
}

bool CopyLatest(double &close0, double &close1, double &hlMid, double &atr0, double &atr1, double &macd0, double &macd1, double &emaHigh0, double &emaLow0)
{
  double closeArr[2], highArr[1], lowArr[1];
  double atrArr[2], macdMain[2], emaH[1], emaL[1];
  if(CopyClose(InpSymbol, InpTF, 0, 2, closeArr) != 2) return false;
  if(CopyHigh(InpSymbol, InpTF, 0, 1, highArr) != 1) return false;
  if(CopyLow(InpSymbol, InpTF, 0, 1, lowArr) != 1) return false;
  if(CopyBuffer(hATR, 0, 0, 2, atrArr) != 2) return false;
  if(CopyBuffer(hMACD, 0, 0, 2, macdMain) != 2) return false;
  if(CopyBuffer(hEMAHigh, 0, 0, 1, emaH) != 1) return false;
  if(CopyBuffer(hEMALow, 0, 0, 1, emaL) != 1) return false;

  close0 = closeArr[0];
  close1 = closeArr[1];
  hlMid  = (highArr[0] + lowArr[0]) * 0.5; // midpoint of current bar
  atr0   = atrArr[0];
  atr1   = atrArr[1];
  macd0  = macdMain[0];
  macd1  = macdMain[1];
  emaHigh0 = emaH[0];
  emaLow0  = emaL[0];
  return true;
}

int CurrentPositionDirection(double &entryPrice, double &slPrice)
{
  int total = PositionsTotal();
  for(int i=0; i<total; ++i)
  {
    ulong ticket = PositionGetTicket(i);
    if(PositionSelectByTicket(ticket))
    {
      if(PositionGetString(POSITION_SYMBOL) == InpSymbol && PositionGetInteger(POSITION_MAGIC) == InpMagic)
      {
        entryPrice = PositionGetDouble(POSITION_PRICE_OPEN);
        slPrice    = PositionGetDouble(POSITION_SL);
        int type   = (int)PositionGetInteger(POSITION_TYPE);
        lastTicket = ticket;
        return (type == POSITION_TYPE_BUY) ? 1 : -1;
      }
    }
  }
  return 0;
}

// 2026-09-15 bugfix: this used to suffix every line's object name with the current bar's
// timestamp (name + "_" + lastBarTime), which meant a "new" object every single bar instead of
// ever matching an existing one to move -- Entry/SL/TP1/TP2/TP3 (and the EMA cloud) accumulated
// one full set of HLINE objects PER BAR the trade stayed open, unbounded, which is what caused
// the wall of stacked green TP lines and the lag the user hit running Tester visual mode over a
// trade that rode a long trend. Fixed: one persistent, fixed-name object per line, moved in place
// every update -- exactly the "if exists, move; else create" behavior this function always
// intended, now that the name is actually stable.
void DrawLine(const string name, double price, color clr)
{
  if(!InpDrawVisuals) return;
  if(ObjectFind(0, name) == -1)
  {
    ObjectCreate(0, name, OBJ_HLINE, 0, 0, price);
    ObjectSetInteger(0, name, OBJPROP_STYLE, STYLE_SOLID);
    ObjectSetInteger(0, name, OBJPROP_WIDTH, 1);
    // Background layer: MT5 draws foreground objects in creation order, and these lines are
    // created after the HUD, so in the foreground they were drawn straight across the panel.
    // In the background they sit behind candles and behind every foreground object (the HUD).
    ObjectSetInteger(0, name, OBJPROP_BACK, (long)true);
    ObjectSetInteger(0, name, OBJPROP_SELECTABLE, (long)false);
    ObjectSetInteger(0, name, OBJPROP_HIDDEN, (long)true);
  }
  else
  {
    ObjectSetDouble(0, name, OBJPROP_PRICE, price);
  }
  ObjectSetInteger(0, name, OBJPROP_COLOR, clr); // cloud color can change bar to bar
}

// Lines are now persistent single objects (see DrawLine above), so there's nothing to sweep by
// bar age any more -- this just clears the trade-specific lines (Entry/SL/TP1-3) once the
// position is flat, so they don't linger on the chart pointing at a closed trade. The EMA cloud
// lines are left alone here since they're a standing indicator, not tied to a position.
void CleanupOldVisuals(int posDir)
{
  if(!InpDrawVisuals) return;
  if(posDir != 0) return;
  string tradeLines[] = {"Entry", "SL", "TP1", "TP2", "TP3"};
  for(int i = 0; i < ArraySize(tradeLines); i++)
    if(ObjectFind(0, tradeLines[i]) != -1) ObjectDelete(0, tradeLines[i]);
}

// MT5 draws its own marker for every deal (buy/sell arrows and the dotted line joining entry to
// exit) as chart objects whose names start with "#". They are created after the HUD, so they were
// drawn on top of it. Moving them to the background layer keeps them on the chart but behind the
// panel. Rescans only when the chart's object count changes, so it is cheap to call every tick.
int g_lastChartObjectCount = -1;

void SendTerminalTradeMarkersBack()
{
  int total = ObjectsTotal(0, -1, -1);
  if(total == g_lastChartObjectCount) return;
  g_lastChartObjectCount = total;
  for(int i = total - 1; i >= 0; --i)
  {
    string obj = ObjectName(0, i, -1, -1);
    if(StringGetCharacter(obj, 0) != '#') continue;
    if(ObjectGetInteger(0, obj, OBJPROP_BACK) != 0) continue;
    ObjectSetInteger(0, obj, OBJPROP_BACK, (long)true);
  }
}

// Builds before v1.13 named these lines "TP1_<bartime>" etc. and never removed them, so a chart
// (or a tester visualization template) can still be carrying hundreds of them. Prefix match
// catches both the old suffixed names and the current fixed ones. Called once from OnInit.
void PurgeTradeLineObjects()
{
  string prefixes[] = {"Entry", "SL", "TP1", "TP2", "TP3", "CloudHigh", "CloudLow"};
  for(int i = ObjectsTotal(0, -1, -1) - 1; i >= 0; --i)
  {
    string obj = ObjectName(0, i, -1, -1);
    for(int p = 0; p < ArraySize(prefixes); p++)
    {
      if(StringFind(obj, prefixes[p]) == 0) { ObjectDelete(0, obj); break; }
    }
  }
}

bool ClosePartial(ulong ticket, double frac)
{
  if(!PositionSelectByTicket(ticket)) return false;
  double vol = PositionGetDouble(POSITION_VOLUME);
  double minLot = SymbolInfoDouble(InpSymbol, SYMBOL_VOLUME_MIN);
  double step = SymbolInfoDouble(InpSymbol, SYMBOL_VOLUME_STEP);
  double volClose = MathFloor((vol * frac) / step) * step;
  if(volClose < step || volClose >= vol) return false;

  Trade.SetAsyncMode(false);
  Trade.SetDeviationInPoints(InpSlippagePoints);
  int type = (int)PositionGetInteger(POSITION_TYPE);
  bool ok = false;
  if(type == POSITION_TYPE_BUY) ok = Trade.PositionClosePartial(ticket, volClose, InpSlippagePoints);
  else                          ok = Trade.PositionClosePartial(ticket, volClose, InpSlippagePoints);
  return ok;
}

double EffectiveCapital()
{
  if(InpDeclaredCapital > 0.0) return InpDeclaredCapital;
  return AccountInfoDouble(ACCOUNT_EQUITY);
}

// running realized profit for this EA (by magic and symbol)
double GetEARealizedProfit()
{
  double total = 0.0;
  datetime to = TimeCurrent();
  datetime from = 0;
  // rolling window takes precedence
  if(InpStatsWindowMinutes > 0)
  {
    from = to - (InpStatsWindowMinutes * 60);
  }
  else if(g_statsStart > 0)
  {
    from = g_statsStart;
  }
  else if(InpStatsTodayOnly)
  {
    MqlDateTime dt; TimeToStruct(to, dt);
    dt.hour = 0; dt.min = 0; dt.sec = 0;
    from = StructToTime(dt);
  }
  if(!HistorySelect(from, to)) return 0.0;
  int deals = HistoryDealsTotal();
  for(int i=0;i<deals;i++)
  {
    ulong dealTicket = HistoryDealGetTicket(i);
    if(dealTicket == 0) continue;
    long entryType = (long)HistoryDealGetInteger(dealTicket, DEAL_ENTRY);
    if(entryType != DEAL_ENTRY_OUT) continue; // realized profit only when a part is closed
    if(!InpStatsAccountWide)
    {
      long magic = (long)HistoryDealGetInteger(dealTicket, DEAL_MAGIC);
      if(magic != InpMagic) continue;
      string sym = HistoryDealGetString(dealTicket, DEAL_SYMBOL);
      if(sym != InpSymbol) continue;
    }
    double profit = HistoryDealGetDouble(dealTicket, DEAL_PROFIT);
    // Use DEAL_PROFIT only; swap/commission already included in this field for the deal
    total += profit;
  }
  return total;
}

double GetEAFloatingProfit()
{
  double total = 0.0;
  int totalPos = PositionsTotal();
  for(int i=0;i<totalPos;i++)
  {
    ulong tk = PositionGetTicket(i);
    if(!PositionSelectByTicket(tk)) continue;
    if(PositionGetString(POSITION_SYMBOL) != InpSymbol) continue;
    if((long)PositionGetInteger(POSITION_MAGIC) != InpMagic) continue;
    total += PositionGetDouble(POSITION_PROFIT) + PositionGetDouble(POSITION_SWAP);
  }
  return total;
}

string FormatWithCommas(double value)
{
  bool isNegative = (value < 0.0);
  string s = DoubleToString(MathAbs(value), 2);
  int dotPos = StringFind(s, ".");
  string intPart = (dotPos >= 0 ? StringSubstr(s, 0, dotPos) : s);
  string fracPart = (dotPos >= 0 ? StringSubstr(s, dotPos) : ".00");

  string out = "";
  int len = StringLen(intPart);
  int count = 0;
  for(int i=len-1; i>=0; --i)
  {
    out = StringSubstr(intPart, i, 1) + out;
    count++;
    if(i>0 && (count % 3) == 0) out = "," + out;
  }
  if(isNegative) out = "-" + out;
  return out + fracPart;
}

color GetProfitColor(double value)
{
  if(value > 0.0) return clrDarkGreen; // dark green for profits on white background - very visible
  if(value < 0.0) return clrDarkRed; // dark red for losses on white background - very visible
  return clrBlack; // black for zero on white background
}

string GetRiskLevel()
{
  double equity = AccountInfoDouble(ACCOUNT_EQUITY);
  double balance = AccountInfoDouble(ACCOUNT_BALANCE);
  if(balance == 0.0) return "NORMAL";
  double riskPct = MathAbs(equity - balance) / balance * 100.0;
  if(riskPct >= 20.0) return "HIGHEST";
  if(riskPct >= 10.0) return "HIGH";
  if(riskPct >= 5.0) return "MEDIUM";
  return "LOW";
}

void GetTradeWinLossStats(int &winCount, int &lossCount, double &winRate, double &lossRate)
{
  winCount = 0;
  lossCount = 0;
  winRate = 0.0;
  lossRate = 0.0;
  
  datetime from = 0; datetime to = TimeCurrent();
  if(!HistorySelect(from, to)) return;
  
  int deals = HistoryDealsTotal();
  for(int i=0; i<deals; i++)
  {
    ulong dealTicket = HistoryDealGetTicket(i);
    if(dealTicket == 0) continue;
    
    // Only count closed deals (entry out) for this EA's symbol and magic
    long entryType = (long)HistoryDealGetInteger(dealTicket, DEAL_ENTRY);
    if(entryType != DEAL_ENTRY_OUT) continue;
    
    // Filter by symbol and magic number
    if(!InpStatsAccountWide)
    {
      long magic = (long)HistoryDealGetInteger(dealTicket, DEAL_MAGIC);
      if(magic != InpMagic) continue;
      string sym = HistoryDealGetString(dealTicket, DEAL_SYMBOL);
      if(sym != InpSymbol) continue;
    }
    
    double profit = HistoryDealGetDouble(dealTicket, DEAL_PROFIT);
    if(profit > 0.0) winCount++;
    else if(profit < 0.0) lossCount++;
  }
  
  int totalTrades = winCount + lossCount;
  if(totalTrades > 0)
  {
    winRate = (double)winCount / totalTrades * 100.0;
    lossRate = (double)lossCount / totalTrades * 100.0;
  }
}

double GetAccountHistoryProfitAll()
{
  double total = 0.0;
  datetime from = 0; datetime to = TimeCurrent();
  if(!HistorySelect(from, to)) return 0.0;
  int deals = HistoryDealsTotal();
  for(int i=0;i<deals;i++)
  {
    ulong dealTicket = HistoryDealGetTicket(i);
    if(dealTicket == 0) continue;
    long entryType = (long)HistoryDealGetInteger(dealTicket, DEAL_ENTRY);
    if(entryType != DEAL_ENTRY_OUT) continue;
    total += HistoryDealGetDouble(dealTicket, DEAL_PROFIT);
  }
  return total;
}

//==================================== Swing-pullback entry mode ====================================
// Most recent confirmed swing highs (highs=true) or lows on tf: a bar whose high is strictly above the
// `strength` bars on each side (low strictly below). Only closed bars count, so shift >= strength + 1.
// Fills out[] most recent first, up to `want` prices, and returns how many were found.
int FindSwings(ENUM_TIMEFRAMES tf, bool highs, int strength, int want, double &out[])
{
  ArrayResize(out, 0);
  double buf[];
  ArraySetAsSeries(buf, true);
  int got = highs ? CopyHigh(InpSymbol, tf, 0, 300, buf) : CopyLow(InpSymbol, tf, 0, 300, buf);
  if(got < strength * 2 + 2) return 0;
  for(int k = strength + 1; k < got - strength && ArraySize(out) < want; k++)
  {
    bool isSwing = true;
    for(int j = 1; j <= strength && isSwing; j++)
    {
      if(highs) isSwing = (buf[k] > buf[k - j] && buf[k] > buf[k + j]);
      else      isSwing = (buf[k] < buf[k - j] && buf[k] < buf[k + j]);
    }
    if(isSwing)
    {
      int n = ArraySize(out);
      ArrayResize(out, n + 1);
      out[n] = buf[k];
    }
  }
  return ArraySize(out);
}

// 1 = bullish (last close above a rising EMA, higher high and higher low), -1 = the bearish mirror, 0 = neither.
int TimeframeBias(int idx)
{
  double ema[], close[], hi[], lo[];
  ArraySetAsSeries(ema, true);
  ArraySetAsSeries(close, true);
  if(CopyBuffer(hBiasEMA[idx], 0, 1, 4, ema) != 4) return 0;
  if(CopyClose(InpSymbol, kBiasTFs[idx], 1, 1, close) != 1) return 0;
  if(FindSwings(kBiasTFs[idx], true, InpSwingStrength, 2, hi) < 2) return 0;
  if(FindSwings(kBiasTFs[idx], false, InpSwingStrength, 2, lo) < 2) return 0;
  if(close[0] > ema[0] && ema[0] > ema[3] && hi[0] > hi[1] && lo[0] > lo[1]) return 1;
  if(close[0] < ema[0] && ema[0] < ema[3] && hi[0] < hi[1] && lo[0] < lo[1]) return -1;
  return 0;
}

int ComputeBias()
{
  int bull = 0, bear = 0;
  for(int i = 0; i < 3; i++)
  {
    g_biasTF[i] = TimeframeBias(i);
    if(g_biasTF[i] > 0) bull++;
    else if(g_biasTF[i] < 0) bear++;
  }
  if(bull >= InpBiasMinAgree && bull > bear) return 1;
  if(bear >= InpBiasMinAgree && bear > bull) return -1;
  return 0;
}

ulong FindPendingOrder()
{
  for(int i = OrdersTotal() - 1; i >= 0; i--)
  {
    ulong t = OrderGetTicket(i);
    if(t == 0) continue;
    if(OrderGetString(ORDER_SYMBOL) != InpSymbol || OrderGetInteger(ORDER_MAGIC) != InpMagic) continue;
    long ot = OrderGetInteger(ORDER_TYPE);
    if(ot == ORDER_TYPE_BUY_LIMIT || ot == ORDER_TYPE_SELL_LIMIT) return t;
  }
  return 0;
}

// Same margin / spread / session gates the breakout entries use.
bool SwingEntryFiltersPass()
{
  if(InpEnableMarginCheck)
  {
    double need = 0.0;
    if(OrderCalcMargin(ORDER_TYPE_BUY, InpSymbol, InpLots, SymbolInfoDouble(InpSymbol, SYMBOL_ASK), need)
       && AccountInfoDouble(ACCOUNT_MARGIN_FREE) < need * InpMarginBuffer)
    {
      Print("Swing: skip, free margin below requirement");
      return false;
    }
  }
  if(InpMaxSpreadPoints > 0 && SymbolInfoInteger(InpSymbol, SYMBOL_SPREAD) > InpMaxSpreadPoints)
  {
    Print("Swing: skip, spread too wide");
    return false;
  }
  if(InpUseSessionFilter)
  {
    MqlDateTime ts;
    TimeToStruct(TimeCurrent(), ts);
    bool inSession = (InpSessionStartHour <= InpSessionEndHour
                      ? (ts.hour >= InpSessionStartHour && ts.hour < InpSessionEndHour)
                      : (ts.hour >= InpSessionStartHour || ts.hour < InpSessionEndHour));
    if(!inSession)
    {
      PrintFormat("Swing: skip, outside session hours [%d,%d)", InpSessionStartHour, InpSessionEndHour);
      return false;
    }
  }
  return true;
}

double SwingLots(double entry, double sl, ENUM_ORDER_TYPE ot)
{
  double lots = InpLots;
  double risk = MathAbs(entry - sl);
  if(InpUseRiskSizing && risk > 0.0)
  {
    double tickValue = SymbolInfoDouble(InpSymbol, SYMBOL_TRADE_TICK_VALUE);
    double tickSize  = SymbolInfoDouble(InpSymbol, SYMBOL_TRADE_TICK_SIZE);
    double lossPerLot = (risk / tickSize) * tickValue;
    if(lossPerLot > 0.0) lots = AccountInfoDouble(ACCOUNT_EQUITY) * InpRiskPercent / 100.0 / lossPerLot;
  }
  double step = SymbolInfoDouble(InpSymbol, SYMBOL_VOLUME_STEP);
  lots = MathFloor(lots / step) * step;
  lots = MathMax(SymbolInfoDouble(InpSymbol, SYMBOL_VOLUME_MIN), MathMin(SymbolInfoDouble(InpSymbol, SYMBOL_VOLUME_MAX), lots));
  return AdjustLotsByMargin(lots, entry, ot);
}

// Called once per new H1 bar while flat: cancel the unfilled order from the last check, then place a
// fresh limit order at the M30 swing in the bias direction.
void PlanSwingEntry(int bias, bool filtersPass)
{
  ulong stale = FindPendingOrder();
  if(stale != 0)
  {
    if(Trade.OrderDelete(stale)) PrintFormat("Swing: cancelled unfilled pending #%I64u at bias re-check", stale);
    else PrintFormat("Swing: could not cancel pending #%I64u rc=%d", stale, (int)Trade.ResultRetcode());
  }
  PrintFormat("Swing bias: M30=%d H1=%d H4=%d -> %d (need %d agreeing)", g_biasTF[0], g_biasTF[1], g_biasTF[2], bias, InpBiasMinAgree);
  if(bias == 0 || !filtersPass) return;

  double ask = SymbolInfoDouble(InpSymbol, SYMBOL_ASK);
  double bid = SymbolInfoDouble(InpSymbol, SYMBOL_BID);
  double minDist = (GetStopsLevelPoints() + 2) * SymbolInfoDouble(InpSymbol, SYMBOL_POINT);
  double atr[1];
  if(hSwingATR == INVALID_HANDLE || CopyBuffer(hSwingATR, 0, 1, 1, atr) != 1 || atr[0] <= 0.0)
  {
    Print("Swing: ATR not ready");
    return;
  }
  double buffer = MathMax(InpSwingSLBufferATR * atr[0], minDist);

  double lows[], highs[];
  int nl = FindSwings(InpSwingTF, false, InpSwingStrength, 10, lows);
  int nh = FindSwings(InpSwingTF, true, InpSwingStrength, 10, highs);
  double entry = 0.0, sl = 0.0, tp1 = 0.0;
  if(bias > 0)
  {
    for(int i = 0; i < nl && entry == 0.0; i++) if(lows[i] < ask - minDist) entry = lows[i];
    if(entry > 0.0)
      for(int i = 0; i < nh && tp1 == 0.0; i++) if(highs[i] > entry + minDist) tp1 = highs[i];
    sl = entry - buffer;
  }
  else
  {
    for(int i = 0; i < nh && entry == 0.0; i++) if(highs[i] > bid + minDist) entry = highs[i];
    if(entry > 0.0)
      for(int i = 0; i < nl && tp1 == 0.0; i++) if(lows[i] < entry - minDist) tp1 = lows[i];
    sl = entry + buffer;
  }
  if(entry <= 0.0 || tp1 <= 0.0)
  {
    PrintFormat("Swing: no usable swing for %s (entry=%.2f tp1=%.2f)", bias > 0 ? "BUY" : "SELL", entry, tp1);
    return;
  }
  double risk = MathAbs(entry - sl), reward = MathAbs(tp1 - entry);
  if(reward < InpSwingMinRR * risk)
  {
    PrintFormat("Swing: skip, reward %.2f < %.2f x risk %.2f", reward, InpSwingMinRR, risk);
    return;
  }
  ENUM_ORDER_TYPE ot = (bias > 0 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL);
  double lots = SwingLots(entry, sl, ot);
  if(lots <= 0.0)
  {
    Print("Swing: skip, not enough margin for the minimum lot");
    return;
  }
  entry = NormalizeDouble(entry, _Digits);
  sl = NormalizeDouble(sl, _Digits);
  Trade.SetAsyncMode(false);
  bool ok = (bias > 0)
            ? Trade.BuyLimit(lots, entry, InpSymbol, sl, 0.0, ORDER_TIME_GTC, 0, "SwingPullbackBuy")
            : Trade.SellLimit(lots, entry, InpSymbol, sl, 0.0, ORDER_TIME_GTC, 0, "SwingPullbackSell");
  if(!ok)
  {
    PrintFormat("Swing: order failed rc=%d %s", (int)Trade.ResultRetcode(), Trade.ResultRetcodeDescription());
    return;
  }
  g_planSL = sl;
  g_planTP1 = tp1;
  tp1Hit = false;
  tp2Hit = false;
  lastTicket = 0;
  PrintFormat("Swing: placed %s LIMIT %.2f lots @ %.2f sl=%.2f tp1=%.2f (risk %.2f, reward %.2f)",
              bias > 0 ? "BUY" : "SELL", lots, entry, sl, tp1, risk, reward);
}

// Swing-mode targets from the stored plan: R = distance from the actual fill to the planned SL, TP1 = the
// planned opposite swing, TP2/TP3 = the R multiples, pushed out so they always stay beyond the previous level.
bool SwingTargets(int dir, double entry, double &tp1, double &tp2, double &tp3)
{
  if(g_planSL <= 0.0) return false;
  double r = MathAbs(entry - g_planSL);
  if(r <= 0.0) return false;
  double d1 = (g_planTP1 > 0.0 ? MathAbs(g_planTP1 - entry) : InpTP1_R_Mult * r);
  double d2 = MathMax(InpTP2_R_Mult * r, d1 + r);
  double d3 = MathMax(InpTP3_R_Mult * r, d2 + r);
  tp1 = entry + dir * d1;
  tp2 = entry + dir * d2;
  tp3 = entry + dir * d3;
  return true;
}

string BiasWord(int b)
{
  return (b > 0 ? "up" : (b < 0 ? "down" : "flat"));
}

void SwingHUDLines(string &l1, color &c1, string &l2, string &l3)
{
  l1 = StringFormat("Bias M30:%s H1:%s H4:%s -> %s", BiasWord(g_biasTF[0]), BiasWord(g_biasTF[1]), BiasWord(g_biasTF[2]),
                    g_bias > 0 ? "BUY" : (g_bias < 0 ? "SELL" : "WAIT"));
  c1 = (g_bias > 0 ? HUD_GREEN : (g_bias < 0 ? HUD_RED : HUD_SUBTEXT));
  l2 = "No pending order";
  l3 = " ";
  ulong t = FindPendingOrder();
  if(t != 0 && OrderSelect(t))
  {
    bool isBuy = (OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_BUY_LIMIT);
    l2 = StringFormat("%s LIMIT @ %s", isBuy ? "BUY" : "SELL", DoubleToString(OrderGetDouble(ORDER_PRICE_OPEN), _Digits));
    l3 = StringFormat("SL %s   TP1 %s", DoubleToString(OrderGetDouble(ORDER_SL), _Digits), DoubleToString(g_planTP1, _Digits));
  }
}

//---------- small object-creation helpers (every HUD object: HUD_Z z-order, foreground, locked) ----------
void HUD_ApplyCommon(string name)
{
  ObjectSetInteger(0, name, OBJPROP_CORNER, (long)CORNER_LEFT_UPPER);
  ObjectSetInteger(0, name, OBJPROP_BACK, (long)false);       // foreground: draws above candles/indicators
  ObjectSetInteger(0, name, OBJPROP_ZORDER, (long)HUD_Z);     // click priority only -- does not change drawing order
  ObjectSetInteger(0, name, OBJPROP_HIDDEN, (long)true);      // keep it out of the Object List, not off-chart
}

void HUD_Rect(string name, int x, int y, int w, int h, color bg, color border)
{
  if(ObjectFind(0, name) == -1) ObjectCreate(0, name, OBJ_RECTANGLE_LABEL, 0, 0, 0);
  HUD_ApplyCommon(name);
  ObjectSetInteger(0, name, OBJPROP_XDISTANCE, (long)x);
  ObjectSetInteger(0, name, OBJPROP_YDISTANCE, (long)y);
  ObjectSetInteger(0, name, OBJPROP_XSIZE, (long)w);
  ObjectSetInteger(0, name, OBJPROP_YSIZE, (long)h);
  // No #ifdef here: OBJPROP_BGCOLOR is an enum value, not a preprocessor macro, so the old
  // "#ifdef OBJPROP_BGCOLOR" guard was always false and silently compiled this line out --
  // leaving every panel on MT5's default light background with light-gray text on top of it.
  ObjectSetInteger(0, name, OBJPROP_BGCOLOR, (long)bg);
  ObjectSetInteger(0, name, OBJPROP_BORDER_TYPE, (long)BORDER_FLAT);
  ObjectSetInteger(0, name, OBJPROP_COLOR, (long)border);
  ObjectSetInteger(0, name, OBJPROP_WIDTH, (long)1);
  ObjectSetInteger(0, name, OBJPROP_SELECTABLE, (long)false);
}

void HUD_Label(string name, int x, int y, string text, color clr, int fontSize, bool bold)
{
  if(ObjectFind(0, name) == -1) ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);
  HUD_ApplyCommon(name);
  ObjectSetInteger(0, name, OBJPROP_XDISTANCE, (long)x);
  ObjectSetInteger(0, name, OBJPROP_YDISTANCE, (long)y);
  ObjectSetInteger(0, name, OBJPROP_SELECTABLE, (long)false);
  ObjectSetInteger(0, name, OBJPROP_FONTSIZE, (long)fontSize);
  // MQL5 has no bold property for labels; weight comes from the font face itself.
  ObjectSetString(0, name, OBJPROP_FONT, bold ? "Segoe UI Semibold" : "Segoe UI");
  ObjectSetInteger(0, name, OBJPROP_COLOR, (long)clr);
  ObjectSetString(0, name, OBJPROP_TEXT, text == "" ? " " : text); // "" would render as "Label"
}

void HUD_Button(string name, int x, int y, int w, int h, string text, color bg, color fg, int fontSize)
{
  if(ObjectFind(0, name) == -1) ObjectCreate(0, name, OBJ_BUTTON, 0, 0, 0);
  HUD_ApplyCommon(name);
  ObjectSetInteger(0, name, OBJPROP_XDISTANCE, (long)x);
  ObjectSetInteger(0, name, OBJPROP_YDISTANCE, (long)y);
  ObjectSetInteger(0, name, OBJPROP_XSIZE, (long)w);
  ObjectSetInteger(0, name, OBJPROP_YSIZE, (long)h);
  ObjectSetInteger(0, name, OBJPROP_SELECTABLE, (long)false);
  ObjectSetInteger(0, name, OBJPROP_BORDER_COLOR, (long)bg);
  ObjectSetInteger(0, name, OBJPROP_BGCOLOR, (long)bg);
  ObjectSetInteger(0, name, OBJPROP_COLOR, (long)fg);
  ObjectSetInteger(0, name, OBJPROP_FONTSIZE, (long)fontSize);
  ObjectSetString(0, name, OBJPROP_FONT, "Segoe UI");
  ObjectSetString(0, name, OBJPROP_TEXT, text);
  ObjectSetInteger(0, name, OBJPROP_STATE, (long)false);
}

// Only sets the *default* text at creation time -- never overwrites it afterward, so a user
// typing into the box doesn't get stomped on the next tick's update.
void HUD_Edit(string name, int x, int y, int w, int h, string defaultText)
{
  bool isNew = (ObjectFind(0, name) == -1);
  if(isNew) ObjectCreate(0, name, OBJ_EDIT, 0, 0, 0);
  HUD_ApplyCommon(name);
  ObjectSetInteger(0, name, OBJPROP_XDISTANCE, (long)x);
  ObjectSetInteger(0, name, OBJPROP_YDISTANCE, (long)y);
  ObjectSetInteger(0, name, OBJPROP_XSIZE, (long)w);
  ObjectSetInteger(0, name, OBJPROP_YSIZE, (long)h);
  ObjectSetInteger(0, name, OBJPROP_SELECTABLE, (long)true); // must be selectable to type into
  ObjectSetInteger(0, name, OBJPROP_ALIGN, (long)ALIGN_CENTER);
  ObjectSetInteger(0, name, OBJPROP_BGCOLOR, (long)HUD_FIELDBG);
  ObjectSetInteger(0, name, OBJPROP_COLOR, (long)HUD_TEXT);
  ObjectSetInteger(0, name, OBJPROP_BORDER_COLOR, (long)HUD_SUBTEXT);
  ObjectSetInteger(0, name, OBJPROP_FONTSIZE, (long)9);
  ObjectSetString(0, name, OBJPROP_FONT, "Segoe UI");
  if(isNew) ObjectSetString(0, name, OBJPROP_TEXT, defaultText);
}

void HUD_SetVisible(string name, bool visible)
{
  ObjectSetInteger(0, name, OBJPROP_TIMEFRAMES, visible ? (long)OBJ_ALL_PERIODS : (long)0);
}

double HUD_GetEditDouble(string name)
{
  return StringToDouble(ObjectGetString(0, name, OBJPROP_TEXT));
}

//---------- stats not already available elsewhere: profit factor, historical max drawdown ----------
void GetProfitFactorStats(double &pf, double &grossWin, double &grossLoss)
{
  pf = 0.0; grossWin = 0.0; grossLoss = 0.0;
  if(!HistorySelect(0, TimeCurrent())) return;
  int deals = HistoryDealsTotal();
  for(int i = 0; i < deals; i++)
  {
    ulong dealTicket = HistoryDealGetTicket(i);
    if(dealTicket == 0) continue;
    if((long)HistoryDealGetInteger(dealTicket, DEAL_ENTRY) != DEAL_ENTRY_OUT) continue;
    if(!InpStatsAccountWide)
    {
      if((long)HistoryDealGetInteger(dealTicket, DEAL_MAGIC) != InpMagic) continue;
      if(HistoryDealGetString(dealTicket, DEAL_SYMBOL) != InpSymbol) continue;
    }
    double p = HistoryDealGetDouble(dealTicket, DEAL_PROFIT);
    if(p > 0.0) grossWin += p; else if(p < 0.0) grossLoss += -p;
  }
  pf = (grossLoss > 0.0 ? grossWin / grossLoss : (grossWin > 0.0 ? -1.0 /*inf*/ : 0.0));
}

// Historical max drawdown across the same deal history GetProfitFactorStats/GetTradeWinLossStats
// use, walked in chronological order from a baseline of (current balance - total realized P/L).
void GetMaxDrawdownStats(double &ddAbs, double &ddPct)
{
  ddAbs = 0.0; ddPct = 0.0;
  double totalPL = GetAccountHistoryProfitAll();
  double running = AccountInfoDouble(ACCOUNT_BALANCE) - totalPL;
  double peak = running;
  if(!HistorySelect(0, TimeCurrent())) return;
  int deals = HistoryDealsTotal();
  for(int i = 0; i < deals; i++)
  {
    ulong dealTicket = HistoryDealGetTicket(i);
    if(dealTicket == 0) continue;
    if((long)HistoryDealGetInteger(dealTicket, DEAL_ENTRY) != DEAL_ENTRY_OUT) continue;
    if(!InpStatsAccountWide)
    {
      if((long)HistoryDealGetInteger(dealTicket, DEAL_MAGIC) != InpMagic) continue;
      if(HistoryDealGetString(dealTicket, DEAL_SYMBOL) != InpSymbol) continue;
    }
    running += HistoryDealGetDouble(dealTicket, DEAL_PROFIT);
    if(running > peak) peak = running;
    double dd = peak - running;
    if(dd > ddAbs) { ddAbs = dd; ddPct = (peak > 0.0 ? dd / peak * 100.0 : 0.0); }
  }
}

double HUD_CalcProfit(bool isBuy, double lots, double openPrice, double closePrice)
{
  double profit = 0.0;
  ENUM_ORDER_TYPE ot = isBuy ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
  if(lots <= 0.0 || openPrice <= 0.0 || closePrice <= 0.0) return 0.0;
  if(!OrderCalcProfit(ot, InpSymbol, lots, openPrice, closePrice, profit)) return 0.0;
  return profit;
}

//========================================= EnsureHUD =========================================
// Builds the static layout once. It used to re-run the whole build on every tick, which reset
// every value label to "" (MT5 renders an empty label as the placeholder "Label") and re-applied
// tab colors/visibility several times a second -- that was the blinking. Now it returns early
// once built, and only rebuilds if the panel has been removed (e.g. objects deleted manually).
void EnsureHUD()
{
  if(g_hudBuilt && ObjectFind(0, HUD_PREFIX + "BG") >= 0) return;

  int x = HUD_PanelX, w = HUD_PanelW;
  int pad = 14;
  int innerX = x + pad;
  int innerW = w - pad * 2;

  HUD_Rect(HUD_PREFIX + "BG", x, HUD_PanelY, w, HUD_PanelH, HUD_BG, HUD_BORDER);

  int y = HUD_PanelY + 12;
  HUD_Label(HUD_PREFIX + "TITLE", innerX, y, "MGNFY GOLD", HUD_HEADER, 15, true); y += 24;
  HUD_Label(HUD_PREFIX + "SUB", innerX, y, "", HUD_SUBTEXT, 9, false); y += 18;
  HUD_Label(HUD_PREFIX + "SESS", innerX, y, "", HUD_TEXT, 10, true); y += 16;
  HUD_Label(HUD_PREFIX + "SESSNEXT", innerX, y, "", HUD_SUBTEXT, 8, false); y += 18;

  // Tab buttons
  int tabW = (innerW - 6) / 2;
  HUD_Button(HUD_PREFIX + "TAB0", innerX, y, tabW, 24, "STATS", HUD_TABBG_ON, HUD_TABFG_ON, 9);
  HUD_Button(HUD_PREFIX + "TAB1", innerX + tabW + 6, y, tabW, 24, "RISK CALC", HUD_TABBG_OFF, HUD_TABFG_OFF, 9);
  y += 24 + 10;

  int contentTop = y; // both tabs' content starts here

  //---------------- STATS TAB ----------------
  y = contentTop;
  HUD_Label(HUD_PREFIX + "S_ACCT_HDR", innerX, y, "ACCOUNT", HUD_HEADER, 9, true); y += 16;
  HUD_Label(HUD_PREFIX + "S_BAL",   innerX, y, "", HUD_TEXT, 10, false); y += 16;
  HUD_Label(HUD_PREFIX + "S_EQ",    innerX, y, "", HUD_TEXT, 10, false); y += 16;
  HUD_Label(HUD_PREFIX + "S_FLOAT", innerX, y, "", HUD_TEXT, 10, false); y += 16;
  HUD_Label(HUD_PREFIX + "S_TODAY", innerX, y, "", HUD_TEXT, 10, false); y += 18;
  HUD_Rect(HUD_PREFIX + "S_DIV1", innerX, y, innerW, 1, HUD_SUBTEXT, HUD_SUBTEXT); y += 10;

  HUD_Label(HUD_PREFIX + "S_PERF_HDR", innerX, y, "PERFORMANCE", HUD_HEADER, 9, true); y += 18;
  HUD_Label(HUD_PREFIX + "S_WINRATE",  innerX, y, "", HUD_TEXT, 13, true); y += 20;
  HUD_Label(HUD_PREFIX + "S_WL",       innerX, y, "", HUD_TEXT, 10, false); y += 16;
  HUD_Label(HUD_PREFIX + "S_PF",       innerX, y, "", HUD_TEXT, 10, false); y += 16;
  HUD_Label(HUD_PREFIX + "S_DD",       innerX, y, "", HUD_TEXT, 10, false); y += 18;
  HUD_Rect(HUD_PREFIX + "S_DIV2", innerX, y, innerW, 1, HUD_SUBTEXT, HUD_SUBTEXT); y += 10;

  HUD_Label(HUD_PREFIX + "S_POS_HDR", innerX, y, "OPEN POSITION", HUD_HEADER, 9, true); y += 16;
  HUD_Label(HUD_PREFIX + "S_POS1", innerX, y, "", HUD_TEXT, 10, false); y += 16;
  HUD_Label(HUD_PREFIX + "S_POS2", innerX, y, "", HUD_TEXT, 10, false); y += 16;
  HUD_Label(HUD_PREFIX + "S_POS3", innerX, y, "", HUD_TEXT, 10, false); y += 18;
  HUD_Rect(HUD_PREFIX + "S_DIV3", innerX, y, innerW, 1, HUD_SUBTEXT, HUD_SUBTEXT); y += 10;

  HUD_Label(HUD_PREFIX + "S_SYS_HDR", innerX, y, "SYSTEM", HUD_HEADER, 9, true); y += 16;
  HUD_Label(HUD_PREFIX + "S_SYS1", innerX, y, "", HUD_SUBTEXT, 9, false); y += 14;
  HUD_Label(HUD_PREFIX + "S_SYS2", innerX, y, "", HUD_SUBTEXT, 9, false); y += 16;

  //---------------- RISK CALCULATOR TAB ----------------
  y = contentTop;
  HUD_Label(HUD_PREFIX + "C_PRICE", innerX, y, "", HUD_SUBTEXT, 9, false); y += 18;

  HUD_Button(HUD_PREFIX + "C_DIRBTN", innerX, y, innerW, 24, "BUY", HUD_GREEN, HUD_TABFG_ON, 10);
  y += 24 + 10;

  int lblW = 78, fldH = 20;
  HUD_Label(HUD_PREFIX + "C_LBL_ENTRY", innerX, y + 4, "Entry price", HUD_SUBTEXT, 9, false);
  HUD_Edit(HUD_PREFIX + "C_ENTRY", innerX + lblW, y, innerW - lblW, fldH, "0.00");
  y += fldH + 6;
  HUD_Label(HUD_PREFIX + "C_LBL_LOT", innerX, y + 4, "Lot size", HUD_SUBTEXT, 9, false);
  HUD_Edit(HUD_PREFIX + "C_LOT", innerX + lblW, y, innerW - lblW, fldH, DoubleToString(InpLots, 2));
  y += fldH + 6;
  HUD_Label(HUD_PREFIX + "C_LBL_TP", innerX, y + 4, "Exit (TP) price", HUD_SUBTEXT, 9, false);
  HUD_Edit(HUD_PREFIX + "C_TP", innerX + lblW, y, innerW - lblW, fldH, "0.00");
  y += fldH + 6;
  HUD_Label(HUD_PREFIX + "C_LBL_SL", innerX, y + 4, "Exit (SL) price", HUD_SUBTEXT, 9, false);
  HUD_Edit(HUD_PREFIX + "C_SL", innerX + lblW, y, innerW - lblW, fldH, "0.00");
  y += fldH + 10;

  HUD_Rect(HUD_PREFIX + "C_DIV1", innerX, y, innerW, 1, HUD_SUBTEXT, HUD_SUBTEXT); y += 10;
  HUD_Label(HUD_PREFIX + "C_RESULT_HDR", innerX, y, "RESULT", HUD_HEADER, 9, true); y += 18;
  HUD_Label(HUD_PREFIX + "C_TPRESULT", innerX, y, "", HUD_TEXT, 11, true); y += 18;
  HUD_Label(HUD_PREFIX + "C_SLRESULT", innerX, y, "", HUD_TEXT, 11, true); y += 18;
  HUD_Label(HUD_PREFIX + "C_RR", innerX, y, "", HUD_SUBTEXT, 9, false); y += 20;
  HUD_Label(HUD_PREFIX + "C_HINT", innerX, y, "Edit a field, press Enter to recalc", HUD_SUBTEXT, 8, false);

  if(!g_hudBuilt)
  {
    g_hudBuilt = true;
    // seed sensible defaults for the calculator the first time it's ever built
    double ask = SymbolInfoDouble(InpSymbol, SYMBOL_ASK);
    double atrGuess = 0.0;
    if(hATR != INVALID_HANDLE)
    {
      double a[1];
      if(CopyBuffer(hATR, 0, 0, 1, a) == 1) atrGuess = a[0];
    }
    if(ask > 0.0)
    {
      ObjectSetString(0, HUD_PREFIX + "C_ENTRY", OBJPROP_TEXT, DoubleToString(ask, _Digits));
      if(atrGuess > 0.0)
      {
        ObjectSetString(0, HUD_PREFIX + "C_TP", OBJPROP_TEXT, DoubleToString(ask + 2.0 * atrGuess, _Digits));
        ObjectSetString(0, HUD_PREFIX + "C_SL", OBJPROP_TEXT, DoubleToString(ask - 1.0 * atrGuess, _Digits));
      }
    }
  }

  ApplyHUDTabVisibility();
}

void ApplyHUDTabVisibility()
{
  string statsObjs[] = {"S_ACCT_HDR","S_BAL","S_EQ","S_FLOAT","S_TODAY","S_DIV1",
                         "S_PERF_HDR","S_WINRATE","S_WL","S_PF","S_DD","S_DIV2",
                         "S_POS_HDR","S_POS1","S_POS2","S_POS3","S_DIV3",
                         "S_SYS_HDR","S_SYS1","S_SYS2"};
  string calcObjs[] = {"C_PRICE","C_DIRBTN","C_LBL_ENTRY","C_ENTRY","C_LBL_LOT","C_LOT",
                        "C_LBL_TP","C_TP","C_LBL_SL","C_SL","C_DIV1",
                        "C_RESULT_HDR","C_TPRESULT","C_SLRESULT","C_RR","C_HINT"};
  bool showStats = (g_hudTab == 0);
  for(int i = 0; i < ArraySize(statsObjs); i++) HUD_SetVisible(HUD_PREFIX + statsObjs[i], showStats);
  for(int i = 0; i < ArraySize(calcObjs); i++)  HUD_SetVisible(HUD_PREFIX + calcObjs[i], !showStats);

  ObjectSetInteger(0, HUD_PREFIX + "TAB0", OBJPROP_BGCOLOR, (long)(showStats ? HUD_TABBG_ON : HUD_TABBG_OFF));
  ObjectSetInteger(0, HUD_PREFIX + "TAB0", OBJPROP_COLOR,   (long)(showStats ? HUD_TABFG_ON : HUD_TABFG_OFF));
  ObjectSetInteger(0, HUD_PREFIX + "TAB1", OBJPROP_BGCOLOR, (long)(showStats ? HUD_TABBG_OFF : HUD_TABBG_ON));
  ObjectSetInteger(0, HUD_PREFIX + "TAB1", OBJPROP_COLOR,   (long)(showStats ? HUD_TABFG_OFF : HUD_TABFG_ON));
}

//---------- market session (Tokyo / London / New York), computed in UTC with UK and US daylight saving ----------
// Live: TimeGMT() comes from the PC clock. Strategy Tester: TimeGMT() equals the simulated server time,
// which is UTC on Exness -- on a broker whose server clock isn't UTC the tester display would be shifted.
datetime HUD_UTC(int y, int m, int d, int h, int mi)
{
  MqlDateTime s;
  ZeroMemory(s);
  s.year = y; s.mon = m; s.day = d; s.hour = h; s.min = mi;
  return StructToTime(s);
}

// Day of month of the nth Sunday (nth >= 1), or of the last Sunday when nth <= 0.
int HUD_SundayOfMonth(int y, int m, int nth)
{
  MqlDateTime s;
  if(nth > 0)
  {
    TimeToStruct(HUD_UTC(y, m, 1, 0, 0), s);
    return 1 + (7 - s.day_of_week) % 7 + 7 * (nth - 1);
  }
  datetime lastDay = HUD_UTC(m == 12 ? y + 1 : y, m == 12 ? 1 : m + 1, 1, 0, 0) - 86400;
  TimeToStruct(lastDay, s);
  return s.day - s.day_of_week;
}

bool HUD_UKSummer(datetime utc)   // last Sunday of March 01:00 UTC -> last Sunday of October 01:00 UTC
{
  MqlDateTime s;
  TimeToStruct(utc, s);
  return utc >= HUD_UTC(s.year, 3, HUD_SundayOfMonth(s.year, 3, 0), 1, 0)
      && utc <  HUD_UTC(s.year, 10, HUD_SundayOfMonth(s.year, 10, 0), 1, 0);
}

bool HUD_USSummer(datetime utc)   // second Sunday of March 02:00 local -> first Sunday of November 02:00 local
{
  MqlDateTime s;
  TimeToStruct(utc, s);
  return utc >= HUD_UTC(s.year, 3, HUD_SundayOfMonth(s.year, 3, 2), 7, 0)
      && utc <  HUD_UTC(s.year, 11, HUD_SundayOfMonth(s.year, 11, 1), 6, 0);
}

void UpdateSessionLabels()
{
  datetime utc = TimeGMT();
  MqlDateTime s;
  TimeToStruct(utc, s);
  int now = s.hour * 60 + s.min;
  int ukShift = HUD_UKSummer(utc) ? 60 : 0;
  int usShift = HUD_USSummer(utc) ? 240 : 300;
  int tkOpen = 0, tkClose = 9 * 60;                                // Tokyo 09:00-18:00 JST, no DST
  int lonOpen = 8 * 60 - ukShift, lonClose = 17 * 60 - ukShift;    // London 08:00-17:00 local
  int nyOpen = 8 * 60 + usShift, nyClose = 17 * 60 + usShift;      // New York 08:00-17:00 local
  int breakEnd = nyClose + 60;                                     // gold pauses NY 17:00-18:00

  bool weekend = (s.day_of_week == 6) || (s.day_of_week == 5 && now >= nyClose) || (s.day_of_week == 0 && now < breakEnd);
  bool london = (now >= lonOpen && now < lonClose);
  bool newyork = (now >= nyOpen && now < nyClose);
  bool tokyo = (now >= tkOpen && now < tkClose);

  string name;
  color clr;
  if(weekend)                                { name = "Market closed (weekend)";   clr = HUD_RED; }
  else if(now >= nyClose && now < breakEnd)  { name = "Daily break";               clr = HUD_SUBTEXT; }
  else if(london && newyork)                 { name = "London + New York overlap"; clr = HUD_HEADER; }
  else if(london)                            { name = tokyo ? "Tokyo + London" : "London"; clr = C'90,160,230'; }
  else if(newyork)                           { name = "New York";                  clr = HUD_GREEN; }
  else if(tokyo)                             { name = "Asia (Tokyo)";              clr = HUD_TEXT; }
  else                                       { name = "Asia (Sydney), quiet";      clr = HUD_SUBTEXT; }
  ObjectSetString(0, HUD_PREFIX + "SESS", OBJPROP_TEXT, "Session: " + name);
  ObjectSetInteger(0, HUD_PREFIX + "SESS", OBJPROP_COLOR, (long)clr);

  string next = " ";
  if(!weekend)
  {
    int    times[] = {tkClose, lonOpen, lonClose, nyOpen, nyClose, breakEnd, 1440};
    string names[] = {"Tokyo closes", "London opens", "London closes", "New York opens",
                      "New York closes", "Daily break ends", "Tokyo opens"};
    int best = -1;
    for(int i = 0; i < ArraySize(times); i++)
      if(times[i] > now && (best < 0 || times[i] < times[best])) best = i;
    if(best >= 0)
    {
      int mins = times[best] - now;
      next = StringFormat("%s in %dh %02dm", names[best], mins / 60, mins % 60);
    }
  }
  ObjectSetString(0, HUD_PREFIX + "SESSNEXT", OBJPROP_TEXT, next);
}

//========================================= UpdateHUD =========================================
// Called every OnTick(); only touches dynamic TEXT/color (never edit-box text, so typing in the
// risk calculator is never stomped) -- cheap enough to run unconditionally.
void UpdateHUD()
{
  EnsureHUD();

  string sub = StringFormat("%s  |  %s", InpSymbol, EnumToString((ENUM_TIMEFRAMES)Period()));
  ObjectSetString(0, HUD_PREFIX + "SUB", OBJPROP_TEXT, sub);
  UpdateSessionLabels();

  if(g_hudTab == 0) UpdateStatsTab();
  else              UpdateCalcTab();
}

void UpdateStatsTab()
{
  double realized = GetEARealizedProfit();
  double floating = GetEAFloatingProfit();
  double balance  = AccountInfoDouble(ACCOUNT_BALANCE);
  double equity   = AccountInfoDouble(ACCOUNT_EQUITY);

  ObjectSetString(0, HUD_PREFIX + "S_BAL", OBJPROP_TEXT, StringFormat("Balance:      $%s", FormatWithCommas(balance)));
  ObjectSetString(0, HUD_PREFIX + "S_EQ",  OBJPROP_TEXT, StringFormat("Equity:       $%s", FormatWithCommas(equity)));
  string floatTxt = StringFormat("Floating P/L: $%s", FormatWithCommas(floating));
  ObjectSetString(0, HUD_PREFIX + "S_FLOAT", OBJPROP_TEXT, floatTxt);
  ObjectSetInteger(0, HUD_PREFIX + "S_FLOAT", OBJPROP_COLOR, (long)(floating > 0 ? HUD_GREEN : (floating < 0 ? HUD_RED : HUD_TEXT)));
  string todayTxt = StringFormat("Realized P/L: $%s", FormatWithCommas(realized));
  ObjectSetString(0, HUD_PREFIX + "S_TODAY", OBJPROP_TEXT, todayTxt);
  ObjectSetInteger(0, HUD_PREFIX + "S_TODAY", OBJPROP_COLOR, (long)(realized > 0 ? HUD_GREEN : (realized < 0 ? HUD_RED : HUD_TEXT)));

  int winCount = 0, lossCount = 0;
  double winRate = 0.0, lossRate = 0.0;
  GetTradeWinLossStats(winCount, lossCount, winRate, lossRate);
  int totalTrades = winCount + lossCount;
  ObjectSetString(0, HUD_PREFIX + "S_WINRATE", OBJPROP_TEXT, StringFormat("Win rate: %.1f%%  (%d trades)", winRate, totalTrades));
  ObjectSetInteger(0, HUD_PREFIX + "S_WINRATE", OBJPROP_COLOR, (long)(winRate >= 50.0 ? HUD_GREEN : (totalTrades == 0 ? HUD_TEXT : HUD_RED)));
  ObjectSetString(0, HUD_PREFIX + "S_WL", OBJPROP_TEXT, StringFormat("Wins: %d     Losses: %d", winCount, lossCount));

  double pf = 0.0, grossWin = 0.0, grossLoss = 0.0;
  GetProfitFactorStats(pf, grossWin, grossLoss);
  string pfTxt = (pf < 0.0 ? "Profit factor: inf" : StringFormat("Profit factor: %.2f", pf));
  ObjectSetString(0, HUD_PREFIX + "S_PF", OBJPROP_TEXT, pfTxt);
  ObjectSetInteger(0, HUD_PREFIX + "S_PF", OBJPROP_COLOR, (long)(pf >= 1.0 || pf < 0.0 ? HUD_GREEN : HUD_RED));

  double ddAbs = 0.0, ddPct = 0.0;
  GetMaxDrawdownStats(ddAbs, ddPct);
  ObjectSetString(0, HUD_PREFIX + "S_DD", OBJPROP_TEXT, StringFormat("Max drawdown: $%s (%.1f%%)", FormatWithCommas(ddAbs), ddPct));

  double posEntry = 0.0, posSL = 0.0;
  int posDir = CurrentPositionDirection(posEntry, posSL);
  if(posDir != 0)
  {
    ObjectSetString(0, HUD_PREFIX + "S_POS1", OBJPROP_TEXT,
      StringFormat("%s @ %s", (posDir == 1 ? "BUY" : "SELL"), DoubleToString(posEntry, _Digits)));
    ObjectSetInteger(0, HUD_PREFIX + "S_POS1", OBJPROP_COLOR, (long)(posDir == 1 ? HUD_GREEN : HUD_RED));
    ObjectSetString(0, HUD_PREFIX + "S_POS2", OBJPROP_TEXT,
      StringFormat("P/L: $%s   SL: %s", FormatWithCommas(floating), DoubleToString(posSL, _Digits)));
    ObjectSetString(0, HUD_PREFIX + "S_POS3", OBJPROP_TEXT,
      StringFormat("TP1: %s   TP2: %s", (tp1Hit ? "hit" : "pending"), (tp2Hit ? "hit" : "pending")));
  }
  else if(InpEntryMode == ENTRY_SWING_PULLBACK)
  {
    string l1, l2, l3;
    color c1;
    SwingHUDLines(l1, c1, l2, l3);
    ObjectSetString(0, HUD_PREFIX + "S_POS1", OBJPROP_TEXT, l1);
    ObjectSetInteger(0, HUD_PREFIX + "S_POS1", OBJPROP_COLOR, (long)c1);
    ObjectSetString(0, HUD_PREFIX + "S_POS2", OBJPROP_TEXT, l2);
    ObjectSetString(0, HUD_PREFIX + "S_POS3", OBJPROP_TEXT, l3);
  }
  else
  {
    ObjectSetString(0, HUD_PREFIX + "S_POS1", OBJPROP_TEXT, "No open position");
    ObjectSetInteger(0, HUD_PREFIX + "S_POS1", OBJPROP_COLOR, (long)HUD_SUBTEXT);
    ObjectSetString(0, HUD_PREFIX + "S_POS2", OBJPROP_TEXT, " ");
    ObjectSetString(0, HUD_PREFIX + "S_POS3", OBJPROP_TEXT, " ");
  }

  int spread = (int)SymbolInfoInteger(InpSymbol, SYMBOL_SPREAD);
  long leverage = AccountInfoInteger(ACCOUNT_LEVERAGE);
  ObjectSetString(0, HUD_PREFIX + "S_SYS1", OBJPROP_TEXT, StringFormat("Spread: %d pts   Lot: %.2f", spread, InpLots));
  ObjectSetString(0, HUD_PREFIX + "S_SYS2", OBJPROP_TEXT, StringFormat("Leverage: 1:%d   Risk: %s", (int)leverage, GetRiskLevel()));
}

void UpdateCalcTab()
{
  double bid = SymbolInfoDouble(InpSymbol, SYMBOL_BID);
  double ask = SymbolInfoDouble(InpSymbol, SYMBOL_ASK);
  ObjectSetString(0, HUD_PREFIX + "C_PRICE", OBJPROP_TEXT,
    StringFormat("Bid %s   Ask %s", DoubleToString(bid, _Digits), DoubleToString(ask, _Digits)));

  ObjectSetString(0, HUD_PREFIX + "C_DIRBTN", OBJPROP_TEXT, g_calcIsBuy ? "BUY" : "SELL");
  ObjectSetInteger(0, HUD_PREFIX + "C_DIRBTN", OBJPROP_BGCOLOR, (long)(g_calcIsBuy ? HUD_GREEN : HUD_RED));

  double entry = HUD_GetEditDouble(HUD_PREFIX + "C_ENTRY");
  double lots  = HUD_GetEditDouble(HUD_PREFIX + "C_LOT");
  double tp    = HUD_GetEditDouble(HUD_PREFIX + "C_TP");
  double sl    = HUD_GetEditDouble(HUD_PREFIX + "C_SL");

  double tpProfit = HUD_CalcProfit(g_calcIsBuy, lots, entry, tp);
  double slProfit = HUD_CalcProfit(g_calcIsBuy, lots, entry, sl);

  double point = SymbolInfoDouble(InpSymbol, SYMBOL_POINT);
  double tpPts = (point > 0.0 && entry > 0.0 && tp > 0.0) ? MathAbs(tp - entry) / point : 0.0;
  double slPts = (point > 0.0 && entry > 0.0 && sl > 0.0) ? MathAbs(entry - sl) / point : 0.0;

  ObjectSetString(0, HUD_PREFIX + "C_TPRESULT", OBJPROP_TEXT,
    StringFormat("If TP hit:  %s$%s  (%.0f pts)", (tpProfit >= 0 ? "+" : "-"), FormatWithCommas(MathAbs(tpProfit)), tpPts));
  ObjectSetInteger(0, HUD_PREFIX + "C_TPRESULT", OBJPROP_COLOR, (long)(tpProfit >= 0 ? HUD_GREEN : HUD_RED));

  ObjectSetString(0, HUD_PREFIX + "C_SLRESULT", OBJPROP_TEXT,
    StringFormat("If SL hit:  %s$%s  (%.0f pts)", (slProfit >= 0 ? "+" : "-"), FormatWithCommas(MathAbs(slProfit)), slPts));
  ObjectSetInteger(0, HUD_PREFIX + "C_SLRESULT", OBJPROP_COLOR, (long)(slProfit >= 0 ? HUD_GREEN : HUD_RED));

  if(tpPts > 0.0 && slPts > 0.0)
    ObjectSetString(0, HUD_PREFIX + "C_RR", OBJPROP_TEXT, StringFormat("Risk:Reward = 1 : %.2f", tpPts / slPts));
  else
    ObjectSetString(0, HUD_PREFIX + "C_RR", OBJPROP_TEXT, "Risk:Reward = --");
}

//========================================= OnChartEvent =========================================
void OnChartEvent(const int id, const long &lparam, const double &dparam, const string &sparam)
{
  if(id == CHARTEVENT_OBJECT_CLICK)
  {
    if(sparam == HUD_PREFIX + "TAB0" && g_hudTab != 0) { g_hudTab = 0; ApplyHUDTabVisibility(); UpdateHUD(); }
    else if(sparam == HUD_PREFIX + "TAB1" && g_hudTab != 1) { g_hudTab = 1; ApplyHUDTabVisibility(); UpdateHUD(); }
    else if(sparam == HUD_PREFIX + "C_DIRBTN") { g_calcIsBuy = !g_calcIsBuy; UpdateCalcTab(); }
    ObjectSetInteger(0, sparam, OBJPROP_STATE, (long)false); // never leave it looking "stuck pressed"
    ChartRedraw(0);
  }
  else if(id == CHARTEVENT_OBJECT_ENDEDIT)
  {
    if(sparam == HUD_PREFIX + "C_ENTRY" || sparam == HUD_PREFIX + "C_LOT" ||
       sparam == HUD_PREFIX + "C_TP"    || sparam == HUD_PREFIX + "C_SL")
    {
      UpdateCalcTab();
      ChartRedraw(0);
    }
  }
}

// Minimum SL change worth sending to the broker (500 points = 0.50 on XAUUSDm). The ATR trail
// used to fire a modify request on nearly every tick for sub-cent moves -- visible in tester
// logs as dozens of "modify position" lines per minute -- which lags visual mode and is the kind
// of request volume a live broker can throttle. Stairstep/BE moves are far larger than this.
#define TRAIL_MIN_STEP_POINTS 500

void MoveSLto(double slNew)
{
  if(!PositionSelect(InpSymbol)) return;
  Trade.SetAsyncMode(false);
  int type = (int)PositionGetInteger(POSITION_TYPE);
  double currentSL = PositionGetDouble(POSITION_SL);
  double currentTP = PositionGetDouble(POSITION_TP);
  double clamped = ClampSLForModify(type, slNew);
  if(clamped <= 0.0) return; // broker would reject
  if(currentSL > 0.0 && MathAbs(clamped - currentSL) < TRAIL_MIN_STEP_POINTS * SymbolInfoDouble(InpSymbol, SYMBOL_POINT))
    return;
  double pt = SymbolInfoDouble(InpSymbol, SYMBOL_POINT);
  if(currentSL > 0.0 && MathAbs(clamped - currentSL) <= 0.5*pt) return; // no effective change
  Trade.PositionModify(InpSymbol, clamped, currentTP);
}

double NormalizeLotsToSymbol(double desiredLots)
{
  double minLot = SymbolInfoDouble(InpSymbol, SYMBOL_VOLUME_MIN);
  double maxLot = SymbolInfoDouble(InpSymbol, SYMBOL_VOLUME_MAX);
  double step   = SymbolInfoDouble(InpSymbol, SYMBOL_VOLUME_STEP);
  if(step <= 0.0) return desiredLots; // fallback
  double lots = MathFloor(desiredLots / step + 1e-8) * step;
  if(lots < minLot) lots = minLot;
  if(lots > maxLot) lots = maxLot;
  int stepDigits = (int)MathMax(0, MathRound(-MathLog10(step)));
  return NormalizeDouble(lots, stepDigits);
}

//-------------------- Lifecycle -----------------
int OnInit()
{
  Trade.SetExpertMagicNumber(InpMagic);
  // Strategy Tester only: don't auto-add the EA's ATR/MACD/EMA indicators to the visual chart.
  // Their sub-windows shrank the main chart and cut the HUD off. Must run before handles exist.
  TesterHideIndicators(true);
  PurgeTradeLineObjects();
  if(!EnsureHandles()) return(INIT_FAILED);
  // initialize stats baseline
  string gname = StatsGlobalName();
  if(InpResetHUD)
  {
    g_statsStart = TimeCurrent();
    GlobalVariableSet(gname, (double)g_statsStart);
  }
  else if(InpStatsFromAttach)
  {
    g_statsStart = TimeCurrent();
    GlobalVariableSet(gname, (double)g_statsStart);
  }
  else if(GlobalVariableCheck(gname))
  {
    g_statsStart = (datetime)GlobalVariableGet(gname);
  }
  else
  {
    g_statsStart = 0; // default; use Today or full history depending on other inputs
  }
  lastBarTime = 0;
  prevTrend = 0;
  prevUp1 = 0.0;
  prevDn1 = 0.0;
  tp1Hit = false;
  tp2Hit = false;
  lastTicket = 0;
  
  // Initialize HUD immediately so it's visible from start (including backtests)
  EnsureHUD();
  UpdateHUD();
  PrintFormat("Init: RequireFlip=%d MidlineBreak=%d ConfirmBars=%d ATRmult=%.2f ATRSL=%.2f RiskSizing=%d Risk%%=%.2f MarginCheck=%d SpreadMax=%d",
              (int)InpRequireTrendFlip, (int)InpUseMidlineBreakout, InpBreakoutConfirmBars,
              InpATRMultiplier, InpSL_ATR_Mult, (int)InpUseRiskSizing, InpRiskPercent,
              (int)InpEnableMarginCheck, InpMaxSpreadPoints);
  return(INIT_SUCCEEDED);
}



void OnTick()
{
  if(Symbol() != InpSymbol) return;
  if(!EnsureHandles()) return;
  UpdateHUD();
  SendTerminalTradeMarkersBack();

  // gate logic to new bar for signal generation
  bool newBar = IsNewBar();
  double close0, close1, hlMid, atr0, atr1, macd0, macd1, emaH0, emaL0;
  if(!CopyLatest(close0, close1, hlMid, atr0, atr1, macd0, macd1, emaH0, emaL0)) return;

  // optional cloud visuals
  if(InpDrawVisuals)
  {
    if(InpShowCloud)
    {
      color cloud = clrNONE;
      if(macd0 > 0 && macd0 > macd1) cloud = clrAqua;
      if(macd0 < 0 && macd0 < macd1) cloud = clrRed;
      DrawLine("CloudHigh", emaH0, cloud);
      DrawLine("CloudLow",  emaL0, cloud);
    }
  }

  // compute bands (lowerBand/upperBand). Naming explicit: lowerBand < upperBand
  double lowerBand = hlMid - InpATRMultiplier * atr0;
  double upperBand = hlMid + InpATRMultiplier * atr0;

  double up1 = (prevUp1 == 0.0 ? lowerBand : (close1 > prevUp1 ? MathMax(lowerBand, prevUp1) : lowerBand));
  double dn1 = (prevDn1 == 0.0 ? upperBand : (close1 < prevDn1 ? MathMin(upperBand, prevDn1) : upperBand));

  int trend = (prevTrend == 0 ? 1 : prevTrend);
  if(close0 > dn1) trend = 1; else if(close0 < up1) trend = -1;

  // Breakout confirmation (default 1 bar)
  bool buyBreak, sellBreak;
  if(InpUseMidlineBreakout)
  {
    // Use hlMid to produce more frequent signals
    buyBreak = (close1 <= hlMid && close0 > hlMid);
    sellBreak = (close1 >= hlMid && close0 < hlMid);
  }
  else
  {
    // Use ATR bands
    buyBreak = (close1 <= dn1 && close0 > dn1);
    sellBreak = (close1 >= up1 && close0 < up1);
  }
  // For N>1, require last N-1 bars inside and current outside (simple check)
  if(InpBreakoutConfirmBars > 1)
  {
    // We only implement N=2 efficiently without extra buffers for performance; higher N falls back to 2
    double c2[1];
    if(CopyClose(InpSymbol, InpTF, 2, 1, c2) == 1)
    {
      if(InpUseMidlineBreakout)
      {
        buyBreak = (c2[0] <= hlMid && close1 <= hlMid && close0 > hlMid);
        sellBreak = (c2[0] >= hlMid && close1 >= hlMid && close0 < hlMid);
      }
      else
      {
        buyBreak = (c2[0] <= dn1 && close1 <= dn1 && close0 > dn1);
        sellBreak = (c2[0] >= up1 && close1 >= up1 && close0 < up1);
      }
    }
  }

  bool buySignal, sellSignal;
  if(InpRequireTrendFlip)
  {
    buySignal = ((trend == 1 && prevTrend == -1) && buyBreak);
    sellSignal = ((trend == -1 && prevTrend == 1) && sellBreak);
  }
  else
  {
    buySignal = buyBreak;
    sellSignal = sellBreak;
  }

  // optional MACD filter
  if(InpUseMACDFilter)
  {
    if(buySignal && macd0 <= 0) buySignal = false;
    if(sellSignal && macd0 >= 0) sellSignal = false;
  }

  // log per new bar the regime state and raw signals
  if(newBar)
    PrintFormat("NB state: close1=%.2f close0=%.2f up1=%.2f dn1=%.2f mid=%.2f prevTrend=%d -> trend=%d breakBuy=%d breakSell=%d buySig=%d sellSig=%d (midBreak=%d)",
                close1, close0, up1, dn1, hlMid, prevTrend, trend, (int)buyBreak, (int)sellBreak, (int)buySignal, (int)sellSignal, (int)InpUseMidlineBreakout);

  // margin check (optional)
  double priceAsk = SymbolInfoDouble(InpSymbol, SYMBOL_ASK);
  double priceBid = SymbolInfoDouble(InpSymbol, SYMBOL_BID);
  if(InpEnableMarginCheck)
  {
    double freeMarginCheck = 0.0;
    if(!OrderCalcMargin(ORDER_TYPE_BUY, InpSymbol, InpLots, priceAsk, freeMarginCheck)) freeMarginCheck = 0.0;
    double freeMargin = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
    if(freeMargin < freeMarginCheck * InpMarginBuffer)
    {
      // insufficient margin; skip entries
      if(newBar)
        PrintFormat("Skip entries: FreeMargin=%.2f < Required=%.2f (buffer x%.2f) for lots %.2f", freeMargin, freeMarginCheck*InpMarginBuffer, InpMarginBuffer, InpLots);
      buySignal = false;
      sellSignal = false;
    }
  }

  // spread filter
  if(InpMaxSpreadPoints > 0)
  {
    int spreadPts = (int)SymbolInfoInteger(InpSymbol, SYMBOL_SPREAD);
    if(spreadPts > InpMaxSpreadPoints)
    {
      if(newBar)
        PrintFormat("Skip entries: spread %d > max %d points", spreadPts, InpMaxSpreadPoints);
      buySignal = false; sellSignal = false;
    }
  }

  // session filter (server time hours)
  if(InpUseSessionFilter)
  {
    datetime nowTime = TimeCurrent();
    MqlDateTime ts; TimeToStruct(nowTime, ts);
    int hour = (int)ts.hour;
    bool inSession = (InpSessionStartHour <= InpSessionEndHour
                      ? (hour >= InpSessionStartHour && hour < InpSessionEndHour)
                      : (hour >= InpSessionStartHour || hour < InpSessionEndHour));
    if(!inSession)
    {
      if(newBar) PrintFormat("Skip entries: out of session hour=%d [%d,%d)", hour, InpSessionStartHour, InpSessionEndHour);
      buySignal = false; sellSignal = false;
    }
  }

  // One position at a time if configured
  double curEntry=0.0, curSL=0.0;
  int posDir = CurrentPositionDirection(curEntry, curSL);
  if(newBar && posDir != 0 && (buySignal || sellSignal))
    PrintFormat("Skip entries: existing position dir=%d (only-one=%d)", posDir, (int)InpOnlyOnePosition);

  // Trend filter (higher timeframe EMA + slope)
  if(InpUseTrendFilter)
  {
    double emaT[2];
    if(hTrendEMA != INVALID_HANDLE && CopyBuffer(hTrendEMA, 0, 0, 2, emaT) == 2)
    {
      double emaNow = emaT[0], emaPrev = emaT[1];
      bool upSlope = (emaNow >= emaPrev);
      bool dnSlope = (emaNow <= emaPrev);
      bool upTrend = (priceAsk > emaNow) && (!InpTrendRequireSlope || upSlope);
      bool dnTrend = (priceBid < emaNow) && (!InpTrendRequireSlope || dnSlope);
      if(!upTrend) buySignal = false;
      if(!dnTrend) sellSignal = false;
      if(newBar) PrintFormat("TrendFilter emaNow=%.2f emaPrev=%.2f up=%d dn=%d slopeReq=%d", emaNow, emaPrev, (int)upTrend, (int)dnTrend, (int)InpTrendRequireSlope);
    }
  }

  // Swing-pullback mode: the breakout market entries above are switched off. At each new H1 bar the
  // M30/H1/H4 bias is re-checked and, while flat, the pending order is re-planned.
  if(InpEntryMode == ENTRY_SWING_PULLBACK)
  {
    buySignal = false;
    sellSignal = false;
    datetime h1Bar = iTime(InpSymbol, PERIOD_H1, 0);
    if(h1Bar != 0 && h1Bar != g_lastBiasBar)
    {
      g_lastBiasBar = h1Bar;
      g_bias = ComputeBias();
      if(posDir == 0) PlanSwingEntry(g_bias, SwingEntryFiltersPass());
    }
  }

  // entries only on new bar to avoid whipsaw
  if(newBar && InpOnlyOnePosition && posDir == 0)
  {
    if(buySignal)
    {
      // compute SL and TPs using ATR or percent of entry price
      double entry = priceAsk;
      double slPct = (InpStopLossPercent > 0.0 ? InpStopLossPercent / 100.0 : 0.0);
      double slPrice = (slPct > 0.0 ? entry * (1.0 - slPct) : 0.0);
      if(InpUseATRStops)
      {
        slPrice = entry - InpSL_ATR_Mult * atr0;
      }
      // clamp to broker stop level; can return 0 which means send without SL
      slPrice = ClampSLForOrder(POSITION_TYPE_BUY, slPrice);
      double riskR = 0.0; if(slPrice > 0.0) riskR = MathMax(0.0, entry - slPrice);

      // risk-based sizing if enabled
      double lots = InpLots;
      if(InpUseRiskSizing && slPrice > 0.0)
      {
        double equity = AccountInfoDouble(ACCOUNT_EQUITY);
        double riskAmt = equity * InpRiskPercent / 100.0;
        double tickValue = SymbolInfoDouble(InpSymbol, SYMBOL_TRADE_TICK_VALUE);
        double tickSize  = SymbolInfoDouble(InpSymbol, SYMBOL_TRADE_TICK_SIZE);
        double lossPerLot = (riskR / tickSize) * tickValue;
        if(lossPerLot > 0.0)
        {
          lots = riskAmt / lossPerLot;
          double step = SymbolInfoDouble(InpSymbol, SYMBOL_VOLUME_STEP);
          double minLot = SymbolInfoDouble(InpSymbol, SYMBOL_VOLUME_MIN);
          double maxLot = SymbolInfoDouble(InpSymbol, SYMBOL_VOLUME_MAX);
          lots = MathFloor(lots / step) * step;
          lots = MathMax(minLot, MathMin(maxLot, lots));
        }
      }
      else
      {
        lots = NormalizeLotsToSymbol(InpLots);
      }

      // finalize lots by margin allowance
      lots = AdjustLotsByMargin(lots, entry, ORDER_TYPE_BUY);
      if(lots <= 0.0)
      {
        Print("Skip BUY: not enough margin for min lot after adjustment.");
      }
      else
      {
        Trade.SetDeviationInPoints(InpSlippagePoints);
        Trade.SetAsyncMode(false);
        PrintFormat("Enter BUY lots=%.2f sl=%.2f spread=%d", lots, slPrice, (int)SymbolInfoInteger(InpSymbol, SYMBOL_SPREAD));
        bool ok = Trade.Buy(lots, InpSymbol, 0.0, slPrice, 0.0, "ATRRegimeBuy");
        if(!ok)
        {
          PrintFormat("Buy failed: rc=%d desc=%s", (int)Trade.ResultRetcode(), Trade.ResultRetcodeDescription());
        }
        else
        {
          PrintFormat("Buy placed. retcode=%d deal=%I64u order=%I64u", (int)Trade.ResultRetcode(), (ulong)Trade.ResultDeal(), (ulong)Trade.ResultOrder());
        }
        // record/reset state
        tp1Hit = false; tp2Hit = false;
        lastTicket = 0;
      }
    }
    else if(sellSignal)
    {
      double entry = priceBid;
      double slPct = (InpStopLossPercent > 0.0 ? InpStopLossPercent / 100.0 : 0.0);
      double slPrice = (slPct > 0.0 ? entry * (1.0 + slPct) : 0.0);
      if(InpUseATRStops)
      {
        slPrice = entry + InpSL_ATR_Mult * atr0;
      }
      slPrice = ClampSLForOrder(POSITION_TYPE_SELL, slPrice);
      double riskR = 0.0; if(slPrice > 0.0) riskR = MathMax(0.0, slPrice - entry);

      double lots = InpLots;
      if(InpUseRiskSizing && slPrice > 0.0)
      {
        double equity = AccountInfoDouble(ACCOUNT_EQUITY);
        double riskAmt = equity * InpRiskPercent / 100.0;
        double tickValue = SymbolInfoDouble(InpSymbol, SYMBOL_TRADE_TICK_VALUE);
        double tickSize  = SymbolInfoDouble(InpSymbol, SYMBOL_TRADE_TICK_SIZE);
        double lossPerLot = (riskR / tickSize) * tickValue;
        if(lossPerLot > 0.0)
        {
          lots = riskAmt / lossPerLot;
          double step = SymbolInfoDouble(InpSymbol, SYMBOL_VOLUME_STEP);
          double minLot = SymbolInfoDouble(InpSymbol, SYMBOL_VOLUME_MIN);
          double maxLot = SymbolInfoDouble(InpSymbol, SYMBOL_VOLUME_MAX);
          lots = MathFloor(lots / step) * step;
          lots = MathMax(minLot, MathMin(maxLot, lots));
        }
      }
      else
      {
        lots = NormalizeLotsToSymbol(InpLots);
      }

      // finalize lots by margin allowance
      lots = AdjustLotsByMargin(lots, entry, ORDER_TYPE_SELL);
      if(lots <= 0.0)
      {
        Print("Skip SELL: not enough margin for min lot after adjustment.");
      }
      else
      {
        Trade.SetDeviationInPoints(InpSlippagePoints);
        Trade.SetAsyncMode(false);
        PrintFormat("Enter SELL lots=%.2f sl=%.2f spread=%d", lots, slPrice, (int)SymbolInfoInteger(InpSymbol, SYMBOL_SPREAD));
        bool ok = Trade.Sell(lots, InpSymbol, 0.0, slPrice, 0.0, "ATRRegimeSell");
        if(!ok)
        {
          PrintFormat("Sell failed: rc=%d desc=%s", (int)Trade.ResultRetcode(), Trade.ResultRetcodeDescription());
        }
        else
        {
          PrintFormat("Sell placed. retcode=%d deal=%I64u order=%I64u", (int)Trade.ResultRetcode(), (ulong)Trade.ResultDeal(), (ulong)Trade.ResultOrder());
        }
        tp1Hit = false; tp2Hit = false;
        lastTicket = 0;
      }
    }
  }

  // refresh position info
  posDir = CurrentPositionDirection(curEntry, curSL);

  // --- Small-account partial-capture logic
  {
    double effCap = EffectiveCapital();
    bool smallAccountActive = (effCap > 0.0 && effCap <= InpSmallCapThreshold);
    double eaFloating = GetEAFloatingProfit();
    static double lastEntryPriceForSmall = 0.0;
    if(lastEntryPriceForSmall != curEntry) { smallProfitTaken = false; lastEntryPriceForSmall = curEntry; }
    if(smallAccountActive && !smallProfitTaken)
    {
      double thresholdUsd = MathMax(InpSmallProfitAbs, effCap * (InpSmallProfitPct/100.0));
      if(eaFloating >= thresholdUsd)
      {
        if(lastTicket != 0 && InpSmallPartialFrac > 0.0)
        {
          bool closed = ClosePartial(lastTicket, InpSmallPartialFrac);
          if(closed)
          {
            smallProfitTaken = true;
            PrintFormat("Small-account: closed %.2f%% at floating=%.2f (threshold=%.2f)", InpSmallPartialFrac*100.0, eaFloating, thresholdUsd);
            if(InpSmallMoveToBE)
            {
              double pt = SymbolInfoDouble(InpSymbol, SYMBOL_POINT);
              double newSL = curEntry;
              if(posDir == 1) newSL = curEntry + InpSmallBEBufferPts * pt; else newSL = curEntry - InpSmallBEBufferPts * pt;
              MoveSLto(newSL);
              PrintFormat("Small-account: moved SL to BE+buffer %.5f", newSL);
            }
          }
        }
      }
    }
  }

  // manage TPs and visuals for open trade
  if(posDir != 0)
  {
    // if we just opened, draw visuals
    if(InpDrawVisuals && newBar)
    {
      // Visual targets based on chosen model
      double tp1, tp2, tp3;
      if(InpUseATRStops)
      {
        double r = InpSL_ATR_Mult * atr0;
        if(posDir == 1) { tp1 = curEntry + InpTP1_R_Mult * r; tp2 = curEntry + InpTP2_R_Mult * r; tp3 = curEntry + InpTP3_R_Mult * r; }
        else            { tp1 = curEntry - InpTP1_R_Mult * r; tp2 = curEntry - InpTP2_R_Mult * r; tp3 = curEntry - InpTP3_R_Mult * r; }
      }
      else
      {
        double slPct = (InpStopLossPercent > 0.0 ? InpStopLossPercent / 100.0 : 0.0);
        tp1 = (posDir == 1 ? curEntry * (1.0 + slPct) : curEntry * (1.0 - slPct));
        tp2 = (posDir == 1 ? curEntry * (1.0 + 2.0 * slPct) : curEntry * (1.0 - 2.0 * slPct));
        tp3 = (posDir == 1 ? curEntry * (1.0 + 3.0 * slPct) : curEntry * (1.0 - 3.0 * slPct));
      }
      DrawLine("Entry", curEntry, clrBlue);
      if(InpUseATRStops)
      {
        double slv = (posDir == 1 ? curEntry - InpSL_ATR_Mult * atr0 : curEntry + InpSL_ATR_Mult * atr0);
        DrawLine("SL", slv, clrRed);
      }
      else
      {
        double slPct = (InpStopLossPercent > 0.0 ? InpStopLossPercent / 100.0 : 0.0);
        if(slPct > 0.0) DrawLine("SL", (posDir == 1 ? curEntry * (1.0 - slPct) : curEntry * (1.0 + slPct)), clrRed);
      }
      if(InpEntryMode == ENTRY_SWING_PULLBACK && SwingTargets(posDir, curEntry, tp1, tp2, tp3))
        DrawLine("SL", g_planSL, clrRed);
      DrawLine("TP1", tp1, clrGreen);
      DrawLine("TP2", tp2, clrGreen);
      DrawLine("TP3", tp3, clrGreen);
    }

    // manage partial TPs in realtime (tick-based)
    if((InpUseATRStops && InpSL_ATR_Mult > 0.0) || (!InpUseATRStops && InpStopLossPercent > 0.0))
    {
      double tp1, tp2, tp3;
      if(InpUseATRStops)
      {
        double r = InpSL_ATR_Mult * atr0;
        if(posDir == 1) { tp1 = curEntry + InpTP1_R_Mult * r; tp2 = curEntry + InpTP2_R_Mult * r; tp3 = curEntry + InpTP3_R_Mult * r; }
        else            { tp1 = curEntry - InpTP1_R_Mult * r; tp2 = curEntry - InpTP2_R_Mult * r; tp3 = curEntry - InpTP3_R_Mult * r; }
      }
      else
      {
        double slPct = InpStopLossPercent / 100.0;
        tp1 = (posDir == 1 ? curEntry * (1.0 + slPct) : curEntry * (1.0 - slPct));
        tp2 = (posDir == 1 ? curEntry * (1.0 + 2.0 * slPct) : curEntry * (1.0 - 2.0 * slPct));
        tp3 = (posDir == 1 ? curEntry * (1.0 + 3.0 * slPct) : curEntry * (1.0 - 3.0 * slPct));
      }

      if(InpEntryMode == ENTRY_SWING_PULLBACK) SwingTargets(posDir, curEntry, tp1, tp2, tp3);

      // capture the ticket if not set
      if(lastTicket == 0)
      {
        int total = PositionsTotal();
        for(int i=0;i<total;++i)
        {
          ulong tk = PositionGetTicket(i);
          if(PositionSelectByTicket(tk) && PositionGetString(POSITION_SYMBOL)==InpSymbol && PositionGetInteger(POSITION_MAGIC)==InpMagic)
          { lastTicket = tk; break; }
        }
      }

      // Check hits
      if(posDir == 1) // buy
      {
        // TP1
        if(!tp1Hit && SymbolInfoDouble(InpSymbol, SYMBOL_BID) >= tp1)
        {
          // 2026-09-15 fix: at min lot size (0.01), a 33% partial close rounds to 0.00 and
          // ClosePartial() silently fails — tp1Hit must still count as reached, or the whole
          // breakeven/TP2/TP3 chain never fires. See JOURNAL.md in MGNFY_GOLD_LIVE for the trace.
          ClosePartial(lastTicket, InpTP1CloseFrac);
          tp1Hit = true;
          // 2026-09-15: stairstep lock — SL moves to TP1's price, not flat entry. Tested against
          // 2 years of real XAUUSDm data: lifts profit factor 0.70 -> 0.87 vs the old flat-BE
          // behavior, because a pullback after TP1 now exits with real profit, not breakeven.
          if(InpMoveToBEafterTP1) MoveSLto(tp1);
        }
        // TP2
        if(tp1Hit && !tp2Hit && SymbolInfoDouble(InpSymbol, SYMBOL_BID) >= tp2)
        {
          ClosePartial(lastTicket, InpTP2CloseFrac);
          tp2Hit = true;
          if(InpMoveToBEafterTP1) MoveSLto(tp2); // stairstep: lock at TP2's price too
        }
        // ATR trailing stop (long)
        if(InpUseATRTrailing && lastTicket != 0)
        {
          double trail = InpTrail_ATR_Mult * atr0;
          double curBid = SymbolInfoDouble(InpSymbol, SYMBOL_BID);
          double newSL = curBid - trail;
          if(newSL > curSL) MoveSLto(newSL);
        }
        // TP3 -> close remainder
        if(tp2Hit && SymbolInfoDouble(InpSymbol, SYMBOL_BID) >= tp3)
        {
          Trade.PositionClose(InpSymbol);
          tp1Hit = tp2Hit = false;
          lastTicket = 0;
        }
      }
      else // sell
      {
        if(!tp1Hit && SymbolInfoDouble(InpSymbol, SYMBOL_ASK) <= tp1)
        {
          ClosePartial(lastTicket, InpTP1CloseFrac);
          tp1Hit = true;
          if(InpMoveToBEafterTP1) MoveSLto(tp1);
        }
        if(tp1Hit && !tp2Hit && SymbolInfoDouble(InpSymbol, SYMBOL_ASK) <= tp2)
        {
          ClosePartial(lastTicket, InpTP2CloseFrac);
          tp2Hit = true;
          if(InpMoveToBEafterTP1) MoveSLto(tp2);
        }
        // ATR trailing stop (short)
        if(InpUseATRTrailing && lastTicket != 0)
        {
          double trail = InpTrail_ATR_Mult * atr0;
          double curAsk = SymbolInfoDouble(InpSymbol, SYMBOL_ASK);
          double newSL = curAsk + trail;
          if(newSL < curSL || curSL == 0.0) MoveSLto(newSL);
        }
        if(tp2Hit && SymbolInfoDouble(InpSymbol, SYMBOL_ASK) <= tp3)
        {
          Trade.PositionClose(InpSymbol);
          tp1Hit = tp2Hit = false;
          lastTicket = 0;
        }
      }
    }
  }

  // update state for next bar
  if(newBar)
  {
    CleanupOldVisuals(posDir);
    prevUp1 = up1;
    prevDn1 = dn1;
    prevTrend = trend;
  }
}

// Cleanup resources
void OnDeinit(const int reason)
{
  if(hATR != INVALID_HANDLE)      { IndicatorRelease(hATR);    hATR = INVALID_HANDLE; }
  if(hMACD != INVALID_HANDLE)     { IndicatorRelease(hMACD);   hMACD = INVALID_HANDLE; }
  if(hEMAHigh != INVALID_HANDLE)  { IndicatorRelease(hEMAHigh);hEMAHigh = INVALID_HANDLE; }
  if(hEMALow != INVALID_HANDLE)   { IndicatorRelease(hEMALow); hEMALow = INVALID_HANDLE; }
  if(hTrendEMA != INVALID_HANDLE) { IndicatorRelease(hTrendEMA); hTrendEMA = INVALID_HANDLE; }
  for(int i = 0; i < 3; i++)
    if(hBiasEMA[i] != INVALID_HANDLE) { IndicatorRelease(hBiasEMA[i]); hBiasEMA[i] = INVALID_HANDLE; }
  if(hSwingATR != INVALID_HANDLE) { IndicatorRelease(hSwingATR); hSwingATR = INVALID_HANDLE; }
  
  int markers = 0, markersFront = 0;
  for(int i = ObjectsTotal(0, -1, -1) - 1; i >= 0; --i)
  {
    string obj = ObjectName(0, i, -1, -1);
    if(StringGetCharacter(obj, 0) != '#') continue;
    markers++;
    if(ObjectGetInteger(0, obj, OBJPROP_BACK) == 0) markersFront++;
  }
  PrintFormat("Deinit: %d horizontal-line objects on chart (expected at most 5: Entry/SL/TP1-3); %d terminal trade markers, %d still in foreground",
              ObjectsTotal(0, -1, OBJ_HLINE), markers, markersFront);

  // Cleanup HUD objects -- every HUD object uses this prefix, so one call catches all of them
  // (including anything a future edit adds, without needing to keep this list in sync by hand).
  ObjectsDeleteAll(0, HUD_PREFIX);
}