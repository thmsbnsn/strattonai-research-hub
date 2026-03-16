import { AlertTriangle } from "lucide-react";
import type { TradingMode } from "@/hooks/useTradingMode";

interface TradingModeSelectorProps {
  tradingMode: TradingMode;
  onModeChange: (mode: TradingMode) => void;
}

export function TradingModeSelector({ tradingMode, onModeChange }: TradingModeSelectorProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1 p-1 rounded-lg bg-muted/50 border border-border w-fit">
        <button
          onClick={() => onModeChange("paper")}
          className={`px-4 py-1.5 rounded-md text-xs font-medium transition-all ${
            tradingMode === "paper"
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Paper Trading
        </button>
        <button
          onClick={() => onModeChange("live")}
          className={`px-4 py-1.5 rounded-md text-xs font-medium transition-all ${
            tradingMode === "live"
              ? "bg-danger/90 text-foreground"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Live Trading
        </button>
      </div>
      {tradingMode === "live" && (
        <div className="flex items-start gap-2 p-2.5 rounded-lg bg-danger/10 border border-danger/20 max-w-md">
          <AlertTriangle className="h-3.5 w-3.5 text-danger shrink-0 mt-0.5" />
          <p className="text-xs text-danger/90 leading-relaxed">
            Live mode uses Alpaca-backed configuration. Orders placed in this mode may execute against real markets. Proceed with caution.
          </p>
        </div>
      )}
    </div>
  );
}
