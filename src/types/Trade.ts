export interface PaperTrade {
  id: string;
  ticker: string;
  direction: "Long" | "Short";
  signal: string;
  entryPrice: number;
  currentPrice: number;
  entryDate: string;
  quantity: number;
  status: "Open" | "Closed";
}

export interface PortfolioPerformancePoint {
  day: number;
  pnl: number;
}
