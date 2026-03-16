export type TradeDirection = "Long" | "Short";
export type TradeStatus = "Open" | "Closed";

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
}
