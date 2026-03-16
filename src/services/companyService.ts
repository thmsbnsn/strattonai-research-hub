import { supabase } from "@/integrations/supabase/client";
import { mergeCompanyRelationships } from "@/engine/companyRelationshipEngine";
import type { CompanyProfile, CompanyRelationship, EventMarker, PricePoint } from "@/types";
import {
  fetchSupabaseWithFallback,
  getMockFallback,
  isMissingTableError,
} from "./supabaseService";
import { getRelationshipMappings } from "./settingsService";

type CompanyProfileRow = {
  ticker?: string | null;
  name?: string | null;
  sector?: string | null;
  industry?: string | null;
  market_cap?: string | null;
  marketCap?: string | null;
  pe?: number | null;
  revenue?: string | null;
  employees?: string | null;
};

type RelatedCompanyRow = {
  event_id?: string | number | null;
  eventId?: string | number | null;
  source?: string | null;
  source_ticker?: string | null;
  primary_ticker?: string | null;
  company?: string | null;
  target?: string | null;
  target_ticker?: string | null;
  related_ticker?: string | null;
  related?: string | null;
  source_name?: string | null;
  target_name?: string | null;
  relationship?: string | null;
  relationship_type?: string | null;
  relation_type?: string | null;
  strength?: number | null;
};

type DailyPriceRow = {
  date?: string | null;
  trade_date?: string | null;
  close?: number | null;
  price?: number | null;
  volume?: number | null;
};

type EventMarkerRow = {
  ticker?: string | null;
  primary_ticker?: string | null;
  category?: string | null;
  event_type?: string | null;
  sentiment?: string | null;
  timestamp?: string | null;
  occurred_at?: string | null;
  created_at?: string | null;
};

type CompanySearchRow = {
  ticker?: string | null;
  name?: string | null;
};

export type CompanySearchResult = {
  ticker: string;
  name: string;
};

function toCompanyProfile(row: CompanyProfileRow, requestedTicker?: string): CompanyProfile {
  return {
    ticker: row.ticker || requestedTicker || "N/A",
    name: row.name || `${row.ticker || requestedTicker || "Unknown"} profile`,
    sector: row.sector || "Unknown sector",
    industry: row.industry || "Unknown industry",
    marketCap: row.market_cap || row.marketCap || "N/A",
    pe: row.pe ?? 0,
    revenue: row.revenue || "N/A",
    employees: row.employees || "N/A",
  };
}

function toCompanyRelationship(row: RelatedCompanyRow): CompanyRelationship {
  return {
    source: row.source || row.source_ticker || row.primary_ticker || row.company || "N/A",
    target: row.target || row.target_ticker || row.related_ticker || row.related || "N/A",
    relationship: row.relationship || row.relationship_type || row.relation_type || "Related",
    strength: row.strength ?? 0.5,
  };
}

function toPricePoint(row: DailyPriceRow): PricePoint {
  return {
    date: row.date || row.trade_date || new Date().toISOString().split("T")[0],
    price: row.close ?? row.price ?? 0,
    volume: row.volume ?? 0,
  };
}

function toEventMarker(row: EventMarkerRow): EventMarker {
  const markerDate = row.timestamp || row.occurred_at || row.created_at || new Date().toISOString();

  return {
    date: markerDate.split("T")[0],
    label: row.category || row.event_type || "Event",
    type: row.sentiment || "neutral",
  };
}

function toCompanySearchResult(row: CompanySearchRow): CompanySearchResult {
  return {
    ticker: (row.ticker || "").trim().toUpperCase(),
    name: row.name?.trim() || (row.ticker || "").trim().toUpperCase(),
  };
}

function rankCompanySearchResults(rows: CompanySearchResult[], query: string) {
  const normalizedQuery = query.trim().toUpperCase();
  const uniqueRows = Array.from(
    new Map(rows.filter((row) => row.ticker).map((row) => [row.ticker, row])).values()
  );

  return uniqueRows.sort((left, right) => {
    const leftTicker = left.ticker.toUpperCase();
    const rightTicker = right.ticker.toUpperCase();
    const leftName = left.name.toUpperCase();
    const rightName = right.name.toUpperCase();

    const leftScore =
      (leftTicker === normalizedQuery ? 100 : 0) +
      (leftName === normalizedQuery ? 90 : 0) +
      (leftTicker.startsWith(normalizedQuery) ? 50 : 0) +
      (leftName.startsWith(normalizedQuery) ? 40 : 0) +
      (leftName.includes(normalizedQuery) ? 20 : 0);
    const rightScore =
      (rightTicker === normalizedQuery ? 100 : 0) +
      (rightName === normalizedQuery ? 90 : 0) +
      (rightTicker.startsWith(normalizedQuery) ? 50 : 0) +
      (rightName.startsWith(normalizedQuery) ? 40 : 0) +
      (rightName.includes(normalizedQuery) ? 20 : 0);

    if (rightScore !== leftScore) {
      return rightScore - leftScore;
    }

    return leftTicker.localeCompare(rightTicker);
  });
}

export async function getCompanyProfile(ticker = "NVDA") {
  const normalizedTicker = ticker.trim().toUpperCase() || "NVDA";

  return fetchSupabaseWithFallback<CompanyProfileRow, CompanyProfile>({
    resource: "companyService.getCompanyProfile",
    table: "company_profiles",
    mockEndpoint: `/companies/profile?ticker=${normalizedTicker}`,
    execute: async () => {
      if (!supabase) {
        return { data: null, error: null };
      }

      return await supabase
        .from("company_profiles")
        .select("*")
        .eq("ticker", normalizedTicker);
    },
    transform: (rows) => toCompanyProfile(rows[0], normalizedTicker),
  });
}

export async function getCompanyRelationships() {
  const relationshipMappings = getRelationshipMappings();

  if (!supabase) {
    const mockRelationships = await getMockFallback<CompanyRelationship[]>("/companies/relationships");
    return mergeCompanyRelationships(mockRelationships, relationshipMappings);
  }

  try {
    const graphResponse = await supabase.from("company_relationship_graph").select("*");

    if (!graphResponse.error && graphResponse.data && graphResponse.data.length > 0) {
      return mergeCompanyRelationships(
        graphResponse.data
        .map(toCompanyRelationship)
        .filter((relationship) => relationship.source !== "N/A" && relationship.target !== "N/A"),
        relationshipMappings
      );
    }

    if (graphResponse.error && !isMissingTableError(graphResponse.error)) {
      console.error("[companyService.getCompanyRelationships] Canonical graph query failed.", graphResponse.error);
    }

    const fallbackRelationships = await fetchSupabaseWithFallback<RelatedCompanyRow, CompanyRelationship[]>({
      resource: "companyService.getCompanyRelationships",
      table: "related_companies",
      mockEndpoint: "/companies/relationships",
      execute: async () => await supabase.from("related_companies").select("*"),
      transform: (rows) =>
        rows
          .filter((row) => !row.event_id && !row.eventId)
          .map(toCompanyRelationship)
          .filter((relationship) => relationship.source !== "N/A" && relationship.target !== "N/A"),
    });
    return mergeCompanyRelationships(fallbackRelationships, relationshipMappings);
  } catch (error) {
    console.error("[companyService.getCompanyRelationships] Graph lookup crashed; using mock fallback.", error);
    const mockRelationships = await getMockFallback<CompanyRelationship[]>("/companies/relationships");
    return mergeCompanyRelationships(mockRelationships, relationshipMappings);
  }
}

export async function searchCompanies(query: string) {
  const normalizedQuery = query.trim();
  if (!normalizedQuery) {
    return [] as CompanySearchResult[];
  }

  const sanitizedQuery = normalizedQuery.replace(/[,]/g, " ").trim();

  return fetchSupabaseWithFallback<CompanySearchRow, CompanySearchResult[]>({
    resource: "companyService.searchCompanies",
    table: "company_profiles",
    mockEndpoint: `/companies/search?query=${encodeURIComponent(sanitizedQuery)}`,
    execute: async () => {
      if (!supabase) {
        return { data: null, error: null };
      }

      return await supabase
        .from("company_profiles")
        .select("ticker,name")
        .or(`ticker.ilike.%${sanitizedQuery}%,name.ilike.%${sanitizedQuery}%`)
        .limit(8);
    },
    transform: (rows) => rankCompanySearchResults(rows.map(toCompanySearchResult), sanitizedQuery).slice(0, 8),
  });
}

export async function getPriceHistory(ticker = "NVDA") {
  const normalizedTicker = ticker.trim().toUpperCase() || "NVDA";

  return fetchSupabaseWithFallback<DailyPriceRow, PricePoint[]>({
    resource: "companyService.getPriceHistory",
    table: "daily_prices",
    mockEndpoint: `/companies/price-history?ticker=${normalizedTicker}`,
    execute: async () => {
      if (!supabase) {
        return { data: null, error: null };
      }

      return await supabase
        .from("daily_prices")
        .select("date,trade_date,close,price,volume")
        .eq("ticker", normalizedTicker)
        .order("date", { ascending: true })
        .limit(90);
    },
    transform: (rows) => rows.map(toPricePoint),
  });
}

export async function getEventMarkers(ticker = "NVDA") {
  const normalizedTicker = ticker.trim().toUpperCase() || "NVDA";

  return fetchSupabaseWithFallback<EventMarkerRow, EventMarker[]>({
    resource: "companyService.getEventMarkers",
    table: "events",
    mockEndpoint: `/companies/event-markers?ticker=${normalizedTicker}`,
    execute: async () => {
      if (!supabase) {
        return { data: null, error: null };
      }

      return await supabase
        .from("events")
        .select("ticker,primary_ticker,category,event_type,sentiment,timestamp,occurred_at,created_at")
        .or(`ticker.eq.${normalizedTicker},primary_ticker.eq.${normalizedTicker}`)
        .order("timestamp", { ascending: true })
        .limit(12);
    },
    transform: (rows) => rows.map(toEventMarker),
  });
}
