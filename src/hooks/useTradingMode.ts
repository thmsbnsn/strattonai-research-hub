import { useState, useCallback } from "react";

export type TradingMode = "paper" | "live";

function getStoredTradingMode(): TradingMode {
  try {
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
    } catch {}
  }, []);

  return { tradingMode, setTradingMode } as const;
}
