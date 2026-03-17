import { useState, useCallback } from "react";
import { readTradingSettingsSnapshot, saveTradingSettings } from "@/services/settingsService";

export type TradingMode = "paper" | "live";

function getStoredTradingMode(): TradingMode {
  try {
    const tradingSettings = readTradingSettingsSnapshot();
    if (tradingSettings.alpacaMode === "live") {
      return "live";
    }
    const stored = localStorage.getItem("strattonai-trading-mode");
    if (stored === "live") return "live";
  } catch {}
  return "paper";
}

export function useTradingMode() {
  const [tradingMode, setModeState] = useState<TradingMode>(getStoredTradingMode);

  const setTradingMode = useCallback((next: TradingMode) => {
    setModeState(next);
    try {
      localStorage.setItem("strattonai-trading-mode", next);
      const current = readTradingSettingsSnapshot();
      saveTradingSettings({
        ...current,
        alpacaMode: next,
      });
    } catch {}
  }, []);

  return { tradingMode, setTradingMode } as const;
}
