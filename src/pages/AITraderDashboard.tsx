import { useState } from "react";
import { Bot } from "lucide-react";
import { useTradingMode } from "@/hooks/useTradingMode";
import { TradingModeSelector } from "@/components/trader/TradingModeSelector";
import { CompanySearch } from "@/components/trader/CompanySearch";
import { CompanyBriefing } from "@/components/trader/CompanyBriefing";
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
    <div className="space-y-6">
      {/* Top section */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold text-foreground">AI Trader Dashboard</h1>
            <span
              className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                tradingMode === "paper"
                  ? "bg-primary/10 text-primary"
                  : "bg-danger/10 text-danger"
              }`}
            >
              {tradingMode === "paper" ? "Paper Trading" : "Live Trading"}
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-1 max-w-xl">
            AI-assisted trading workspace grounded in StrattonAI research signals, event studies, and historical analogs.
          </p>
        </div>
        <TradingModeSelector tradingMode={tradingMode} onModeChange={setTradingMode} />
      </div>

      {/* Company search */}
      <CompanySearch onSearch={setSelectedTicker} />

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left: briefing + cards */}
        <div className="lg:col-span-2 space-y-4">
          {selectedTicker ? (
            <CompanyBriefing ticker={selectedTicker} />
          ) : (
            <div className="terminal-card p-8 flex flex-col items-center justify-center text-center">
              <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center mb-3">
                <Bot className="h-5 w-5 text-muted-foreground" />
              </div>
              <p className="text-sm font-medium text-foreground">No company selected</p>
              <p className="text-xs text-muted-foreground mt-1">
                Search for a company ticker above to load a detailed intelligence briefing.
              </p>
            </div>
          )}

          {/* Supporting cards grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <TradeThesisCard />
            <EvidenceSummaryCard />
            <PaperTradeIdeaCard />
            <LiveReadinessChecklist />
          </div>
        </div>

        {/* Right: chat + signals + events */}
        <div className="space-y-4">
          <AIChatPanel />
          <TopRankedSignals />
          <RecentRelatedEvents />
        </div>
      </div>
    </div>
  );
}
