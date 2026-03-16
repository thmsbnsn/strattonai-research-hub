import type { Event, EventStudyResult } from "@/models";

export type MarketEvent = Event;
export type { EventStudyResult };

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
