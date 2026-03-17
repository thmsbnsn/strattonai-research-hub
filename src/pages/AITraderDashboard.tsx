import { useMemo, useState } from "react";
import { useTradingMode } from "@/hooks/useTradingMode";
import { TradingModeSelector } from "@/components/trader/TradingModeSelector";
import { CompanySearch } from "@/components/trader/CompanySearch";
import { CompanyBriefing, CompanyBriefingEmpty } from "@/components/trader/CompanyBriefing";
import { AIChatPanel } from "@/components/trader/AIChatPanel";
import {
  TopRankedSignals,
  TradeThesisCard,
  EvidenceSummaryCard,
  PaperTradeIdeaCard,
  LiveReadinessChecklist,
  RecentRelatedEvents,
} from "@/components/trader/TraderCards";
import { SignalReviewPanel } from "@/components/trader/SignalReviewPanel";
import { PortfolioMonitorPanel } from "@/components/trader/PortfolioMonitorPanel";
import { PortfolioConstructorPanel } from "@/components/trader/PortfolioConstructorPanel";
import { RiskEnginePanel } from "@/components/trader/RiskEnginePanel";
import { PennyStockPanel } from "@/components/trader/PennyStockPanel";
import type { PortfolioAllocation } from "@/models";
import { readTradingSettingsSnapshot } from "@/services/settingsService";

export default function AITraderDashboard() {
  const { tradingMode, setTradingMode } = useTradingMode();
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [allocations, setAllocations] = useState<PortfolioAllocation[]>([]);
  const tradingSettings = useMemo(() => readTradingSettingsSnapshot(), []);

  return (
    <div className="space-y-5">
      {/* Top bar: title + mode selector */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-bold text-foreground">AI Trader Dashboard</h1>
            <span
              className={`text-[10px] px-2.5 py-0.5 rounded-full font-medium uppercase tracking-wider ${
                tradingMode === "paper"
                  ? "bg-primary/10 text-primary"
                  : "bg-danger/10 text-danger"
              }`}
            >
              {tradingMode === "paper" ? "Paper Trading" : "Live Trading"}
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-1 max-w-lg">
            Research-grounded trading workspace powered by StrattonAI signals, event studies, and historical analogs.
          </p>
        </div>
        <TradingModeSelector tradingMode={tradingMode} onModeChange={setTradingMode} />
      </div>

      {/* Search */}
      <CompanySearch onSearch={setSelectedTicker} />

      {/* Main content: 8/4 split */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left: company briefing (dominant) */}
        <div className="lg:col-span-8 space-y-4">
          {selectedTicker ? (
            <CompanyBriefing ticker={selectedTicker} tradingMode={tradingMode} />
          ) : (
            <CompanyBriefingEmpty />
          )}

          {/* Supporting cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <TradeThesisCard ticker={selectedTicker} tradingMode={tradingMode} />
            <EvidenceSummaryCard ticker={selectedTicker} tradingMode={tradingMode} />
            <PaperTradeIdeaCard ticker={selectedTicker} tradingMode={tradingMode} />
            <LiveReadinessChecklist ticker={selectedTicker} tradingMode={tradingMode} />
          </div>
        </div>

        {/* Right: chat + signals + events */}
        <div className="lg:col-span-4 space-y-4">
          <AIChatPanel ticker={selectedTicker} tradingMode={tradingMode} />
          <TopRankedSignals ticker={selectedTicker} />
          <RecentRelatedEvents ticker={selectedTicker} />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.35fr_0.9fr]">
        <SignalReviewPanel ticker={selectedTicker} />
        <PortfolioMonitorPanel />
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.2fr_1fr]">
        <PortfolioConstructorPanel ticker={selectedTicker} onAllocationsChange={setAllocations} />
        <RiskEnginePanel allocations={allocations} />
      </div>

      <PennyStockPanel tradingSettings={tradingSettings} />
    </div>
  );
}
