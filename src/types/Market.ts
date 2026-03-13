export interface MarketIndex {
  ticker: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
}

export interface SectorPerformance {
  name: string;
  change: number;
  value: number;
}

export interface VolatilityData {
  vix: number;
  change: number;
  trend: "declining" | "rising" | "stable";
}

export interface PricePoint {
  date: string;
  price: number;
  volume: number;
}

export interface EventMarker {
  date: string;
  label: string;
  type: string;
}
