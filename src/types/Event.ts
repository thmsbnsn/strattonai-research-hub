import type { Event, EventStudyResult } from "@/models";

export type MarketEvent = Event;
export type { Event, EventStudyResult };

export interface ReturnDistributionPoint {
  id: number;
  return: number;
  count: number;
}

export interface ForwardCurvePoint {
  day: number;
  horizon: string;
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
