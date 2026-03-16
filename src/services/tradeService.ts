import { supabase } from "@/integrations/supabase/client";
import type { PaperTrade, PortfolioPerformancePoint } from "@/types";
import { fetchSupabaseWithFallback, getMockFallback } from "./supabaseService";

type PaperTradeRow = {
  id?: string | number | null;
  ticker?: string | null;
  direction?: string | null;
  signal?: string | null;
  entry_price?: number | null;
  current_price?: number | null;
  entry_date?: string | null;
  quantity?: number | null;
  status?: string | null;
};

function normalizeDirection(value: string | null | undefined): PaperTrade["direction"] {
  return value === "Short" ? "Short" : "Long";
}

function normalizeStatus(value: string | null | undefined): PaperTrade["status"] {
  return value === "Closed" ? "Closed" : "Open";
}

function toPaperTrade(row: PaperTradeRow): PaperTrade {
  return {
    id: String(row.id ?? row.ticker ?? crypto.randomUUID()),
    ticker: row.ticker || "N/A",
    direction: normalizeDirection(row.direction),
    signal: row.signal || "No signal recorded.",
    entryPrice: row.entry_price ?? 0,
    currentPrice: row.current_price ?? row.entry_price ?? 0,
    entryDate: row.entry_date || new Date().toISOString().slice(0, 10),
    quantity: row.quantity ?? 0,
    status: normalizeStatus(row.status),
  };
}

export async function getPaperTrades() {
  return fetchSupabaseWithFallback<PaperTradeRow, PaperTrade[]>({
    resource: "tradeService.getPaperTrades",
    table: "paper_trades",
    mockEndpoint: "/trades",
    execute: async () => {
      if (!supabase) {
        return { data: null, error: null };
      }

      return await supabase.from("paper_trades").select("*");
    },
    transform: (rows) => rows.map(toPaperTrade),
  });
}

export async function getPortfolioPerformance() {
  return getMockFallback<PortfolioPerformancePoint[]>("/trades/performance");
}
