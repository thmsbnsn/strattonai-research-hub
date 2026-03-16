export type EventSentiment = "positive" | "negative" | "neutral";

export interface EventRelationship {
  ticker: string;
  name: string;
  relationship: string;
}

export interface Event {
  id: string;
  headline: string;
  ticker: string;
  category: string;
  sentiment: EventSentiment;
  timestamp: string;
  relatedCompanies: EventRelationship[];
  historicalAnalog: string;
  sampleSize: number;
  avgReturn: number;
  details?: string;
}
