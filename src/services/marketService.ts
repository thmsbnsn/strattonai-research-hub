import { api } from "@/api/client";
import type { MarketIndex, SectorPerformance, VolatilityData } from "@/types";

export const getMarketIndexes = () => api.get<MarketIndex[]>("/market/indexes");

export const getSectorPerformance = () => api.get<SectorPerformance[]>("/market/sectors");

export const getVolatilityData = () => api.get<VolatilityData>("/market/volatility");
