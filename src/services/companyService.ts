import { api } from "@/api/client";
import type { CompanyProfile, CompanyRelationship, PricePoint, EventMarker } from "@/types";

export const getCompanyProfile = (ticker?: string) =>
  api.get<CompanyProfile>("/companies/profile", ticker ? { ticker } : undefined);

export const getCompanyRelationships = () => api.get<CompanyRelationship[]>("/companies/relationships");

export const getPriceHistory = () => api.get<PricePoint[]>("/companies/price-history");

export const getEventMarkers = () => api.get<EventMarker[]>("/companies/event-markers");
