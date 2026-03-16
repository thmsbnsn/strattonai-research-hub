import { useState } from "react";
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

export default function AITraderDashboard() {
  const { tradingMode, setTradingMode } = useTradingMode();
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);

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
            <CompanyBriefing ticker={selectedTicker} />
          ) : (
            <CompanyBriefingEmpty />
          )}

          {/* Supporting cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <TradeThesisCard ticker={selectedTicker} />
            <EvidenceSummaryCard ticker={selectedTicker} />
            <PaperTradeIdeaCard ticker={selectedTicker} />
            <LiveReadinessChecklist ticker={selectedTicker} />
          </div>
        </div>

        {/* Right: chat + signals + events */}
        <div className="lg:col-span-4 space-y-4">
          <AIChatPanel ticker={selectedTicker} tradingMode={tradingMode} />
          <TopRankedSignals ticker={selectedTicker} />
          <RecentRelatedEvents ticker={selectedTicker} />
        </div>
      </div>
    </div>
  );
}
