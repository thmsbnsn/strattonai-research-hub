export type TradeDirection = "Long" | "Short";
export type TradeStatus = "Open" | "Closed" | "Simulated" | "Risk-Blocked";

export interface PaperTrade {
  id: string;
  ticker: string;
  direction: TradeDirection;
  signal: string;
  entryPrice: number;
  currentPrice: number;
  entryDate: string;
  quantity: number;
  status: TradeStatus;
  mode?: "simulated" | "paper" | "live";
  realizedPnl?: number;
  universe?: "main" | "penny";
  metadata?: Record<string, unknown>;
  alpacaOrderId?: string;
}
