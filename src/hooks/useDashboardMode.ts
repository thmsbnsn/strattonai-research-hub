import { useState, useCallback } from "react";

export type DashboardMode = "research" | "trader";

function getStoredMode(): DashboardMode {
  try {
    const stored = localStorage.getItem("strattonai-dashboard-mode");
    if (stored === "trader") return "trader";
  } catch {}
  return "research";
}

export function useDashboardMode() {
  const [mode, setModeState] = useState<DashboardMode>(getStoredMode);

  const setMode = useCallback((next: DashboardMode) => {
    setModeState(next);
    try {
      localStorage.setItem("strattonai-dashboard-mode", next);
    } catch {}
  }, []);

  const toggle = useCallback(() => {
    setModeState((current) => {
      const next = current === "research" ? "trader" : "research";

      try {
        localStorage.setItem("strattonai-dashboard-mode", next);
      } catch {}

      return next;
    });
  }, []);

  return { mode, setMode, toggle } as const;
}
