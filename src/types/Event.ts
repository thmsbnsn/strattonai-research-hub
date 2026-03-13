export interface MarketEvent {
  id: string;
  headline: string;
  ticker: string;
  category: string;
  sentiment: "positive" | "negative" | "neutral";
  timestamp: string;
  relatedCompanies: { ticker: string; name: string; relationship: string }[];
  historicalAnalog: string;
  sampleSize: number;
  avgReturn: number;
  details?: string;
}

export interface EventStudyResult {
  horizon: string;
  avgReturn: number;
  winRate: number;
  sampleSize: number;
}

export interface ReturnDistributionPoint {
  id: number;
  return: number;
}

export interface ForwardCurvePoint {
  day: number;
  avgReturn: number;
  upperBound: number;
  lowerBound: number;
}

export interface EventStudyFilters {
  eventType?: string;
  primaryCompany?: string;
  relatedCompany?: string;
  horizon?: string;
}
