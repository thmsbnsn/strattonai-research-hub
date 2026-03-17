export type SignalTargetType = "primary" | "related";
export type SignalOriginType = "primary" | "explicit" | "inferred";
export type SignalConfidenceBand = "Low" | "Moderate" | "High";

export interface SignalScore {
  id: string;
  signalKey?: string;
  eventId: string;
  eventCategory: string;
  primaryTicker: string;
  relatedTicker?: string;
  targetTicker: string;
  targetType: SignalTargetType;
  relationshipType?: string;
  horizon: string;
  score: number;
  confidenceBand: SignalConfidenceBand;
  evidenceSummary: string;
  sampleSize: number;
  avgReturn: number;
  medianReturn: number;
  winRate: number;
  originType: SignalOriginType;
  rationale?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}
