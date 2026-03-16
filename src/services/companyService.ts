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

export async function getPriceHistory() {
  return getMockFallback<PricePoint[]>("/companies/price-history");
}

export async function getEventMarkers() {
  return getMockFallback<EventMarker[]>("/companies/event-markers");
}
