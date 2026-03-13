import { api } from "@/api/client";
import type { MarketEvent, EventStudyResult, ReturnDistributionPoint, ForwardCurvePoint } from "@/types";

export const getEvents = () => api.get<MarketEvent[]>("/events");

export const getEventCategories = () => api.get<string[]>("/events/categories");

export const getEventStudies = () => api.get<EventStudyResult[]>("/events/studies");

export const getReturnDistribution = () => api.get<ReturnDistributionPoint[]>("/events/distribution");

export const getForwardCurve = () => api.get<ForwardCurvePoint[]>("/events/forward-curve");

export const getTimeHorizons = () => api.get<string[]>("/events/time-horizons");
