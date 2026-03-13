import { api } from "@/api/client";
import type { PaperTrade, PortfolioPerformancePoint } from "@/types";

export const getPaperTrades = () => api.get<PaperTrade[]>("/trades");

export const getPortfolioPerformance = () => api.get<PortfolioPerformancePoint[]>("/trades/performance");
