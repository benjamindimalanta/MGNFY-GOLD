//+------------------------------------------------------------------+
//| ExportBars_MGNFY.mq5                                             |
//| One-shot exporter: dumps M15 bars (MGNFY GOLD's native timeframe) |
//| for the last 5 years to CSV, for offline Python backtesting.      |
//| Same pattern as the project's ExportBars.mq5, just M15 + 5y range |
//| and a note on how far back your broker's history actually goes.   |
//+------------------------------------------------------------------+
#property copyright "MGNFY GOLD"
#property version   "1.00"
#property strict

input datetime         ExportFrom = D'2021.09.01 00:00';
input datetime         ExportTo   = D'2026.09.01 00:00';
input ENUM_TIMEFRAMES  ExportTF   = PERIOD_M15;   // MGNFY GOLD's recommended timeframe
input string            OutFile   = "bars_m15_5y.csv";

bool   exported = false;
int    lastCount = -1;
int    stableChecks = 0;
int    totalChecks = 0;

int OnInit()
  {
   Print("ExportBars_MGNFY: ready. 5 years of M15 history may not be cached locally yet — ",
         "this will poll every 3s, letting MT5 download from the broker in the background, ",
         "and export once the bar count stops growing (or after ~5 minutes).");
   EventSetTimer(3);
   return(INIT_SUCCEEDED);
  }

void DoExport()
  {
   MqlRates r[];
   ArraySetAsSeries(r, false);

   int got = CopyRates(_Symbol, ExportTF, ExportFrom, ExportTo, r);
   if(got <= 0)
     {
      Print("ExportBars_MGNFY: CopyRates failed, err=", GetLastError(),
            " (requested ", TimeToString(ExportFrom), " .. ", TimeToString(ExportTo), ")");
      Print("ExportBars_MGNFY: try Tools > History Center in MT5, select ", _Symbol,
            ", right-click the timeframe and 'Download' to force the broker to backfill history first.");
      return;
     }

   int fh = FileOpen(OutFile, FILE_WRITE | FILE_ANSI | FILE_TXT);
   if(fh == INVALID_HANDLE)
     {
      Print("ExportBars_MGNFY: FileOpen failed, err=", GetLastError());
      return;
     }

   FileWriteString(fh, "time,open,high,low,close,tickvol,spread\n");

   for(int i = 0; i < got; i++)
     {
      string line = StringFormat("%s,%.3f,%.3f,%.3f,%.3f,%d,%d\n",
                                 TimeToString(r[i].time, TIME_DATE | TIME_SECONDS),
                                 r[i].open, r[i].high, r[i].low, r[i].close,
                                 (int)r[i].tick_volume, (int)r[i].spread);
      FileWriteString(fh, line);
     }

   FileClose(fh);
   Print("ExportBars_MGNFY: wrote ", got, " ", EnumToString(ExportTF), " bars to ", OutFile);
   Print("ExportBars_MGNFY: actual range covered: ", TimeToString(r[0].time), " .. ", TimeToString(r[got-1].time));
   Print("ExportBars_MGNFY: requested range was: ", TimeToString(ExportFrom), " .. ", TimeToString(ExportTo));

   int mh = FileOpen("symbol_meta.csv", FILE_WRITE | FILE_ANSI | FILE_TXT);
   if(mh != INVALID_HANDLE)
     {
      FileWriteString(mh, "field,value\n");
      FileWriteString(mh, StringFormat("symbol,%s\n", _Symbol));
      FileWriteString(mh, StringFormat("digits,%d\n", (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS)));
      FileWriteString(mh, StringFormat("point,%.6f\n", SymbolInfoDouble(_Symbol, SYMBOL_POINT)));
      FileWriteString(mh, StringFormat("tick_value,%.6f\n", SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE)));
      FileWriteString(mh, StringFormat("tick_size,%.6f\n", SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE)));
      FileWriteString(mh, StringFormat("volume_min,%.4f\n", SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN)));
      FileWriteString(mh, StringFormat("volume_step,%.4f\n", SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP)));
      FileWriteString(mh, StringFormat("volume_max,%.4f\n", SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX)));
      FileClose(mh);
      Print("ExportBars_MGNFY: wrote symbol_meta.csv");
     }
  }

void OnTimer()
  {
   if(exported) return;
   totalChecks++;

   MqlRates probe[];
   ArraySetAsSeries(probe, false);
   int got = CopyRates(_Symbol, ExportTF, ExportFrom, ExportTo, probe);

   Print("ExportBars_MGNFY: poll ", totalChecks, " — have ", got, " bars cached so far...");

   if(got == lastCount)
      stableChecks++;
   else
      stableChecks = 0;
   lastCount = got;

   // export once the count has stopped growing for 3 checks (~9s), or after ~5 min regardless
   if(stableChecks >= 3 || totalChecks >= 100)
     {
      exported = true;
      EventKillTimer();
      DoExport();
      ExpertRemove();
     }
  }

void OnTick()
  {
   // present so MT5 treats this as a normal EA; all real work happens on the timer
  }

void OnDeinit(const int reason)
  {
   EventKillTimer();
  }
