import { isSupabaseConfigured, supabase } from "@/integrations/supabase/client";
import { mergeCompanyRelationships } from "@/engine/companyRelationshipEngine";
import type { CompanyProfile, CompanyRelationship, EventMarker, PricePoint } from "@/types";
import {
  fetchOptionalSupabaseRows,
  fetchSupabaseWithFallback,
  getMockFallback,
  isMissingTableError,
} from "./supabaseService";
import { getRelationshipMappings, shouldUseSupabaseLiveData } from "./settingsService";

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

type CompanyGraphRow = {
  source_ticker?: string | null;
  source_name?: string | null;
  target_ticker?: string | null;
  target_name?: string | null;
};

type EventCompanyRow = {
  ticker?: string | null;
  headline?: string | null;
  metadata?: Record<string, unknown> | null;
};

type SignalSearchRow = {
  primary_ticker?: string | null;
  target_ticker?: string | null;
};

export type CompanySearchResult = {
  ticker: string;
  name: string;
};

function canUseLiveSupabase() {
  return shouldUseSupabaseLiveData() && isSupabaseConfigured && Boolean(supabase);
}

function inferCompanyName(row: EventCompanyRow) {
  const metadata = row.metadata;
  if (!metadata || typeof metadata !== "object") {
    return null;
  }

  const canonicalEntityName = metadata["canonical_entity_name"];
  if (typeof canonicalEntityName === "string" && canonicalEntityName.trim()) {
    return canonicalEntityName.trim();
  }

  const companyName = metadata["company_name"];
  if (typeof companyName === "string" && companyName.trim()) {
    return companyName.trim();
  }

  return null;
}

function inferCompanySector(row: EventCompanyRow) {
  const metadata = row.metadata;
  if (!metadata || typeof metadata !== "object") {
    return null;
  }

  const sector = metadata["sector"];
  return typeof sector === "string" && sector.trim() ? sector.trim() : null;
}

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

function addSearchCandidate(target: Map<string, CompanySearchResult>, ticker: string | null | undefined, name?: string | null) {
  const normalizedTicker = (ticker || "").trim().toUpperCase();
  if (!normalizedTicker) {
    return;
  }

  const normalizedName = name?.trim();
  const existing = target.get(normalizedTicker);
  if (!existing) {
    target.set(normalizedTicker, {
      ticker: normalizedTicker,
      name: normalizedName || normalizedTicker,
    });
    return;
  }

  const currentLooksSynthetic = existing.name.toUpperCase() === normalizedTicker;
  if (normalizedName && currentLooksSynthetic) {
    target.set(normalizedTicker, { ticker: normalizedTicker, name: normalizedName });
  }
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
  if (!canUseLiveSupabase()) {
    return getMockFallback<CompanyProfile>(`/companies/profile?ticker=${normalizedTicker}`);
  }

  const [profileRows, graphRows, eventRows] = await Promise.all([
    fetchOptionalSupabaseRows<CompanyProfileRow>({
      resource: "companyService.getCompanyProfile.profile",
      table: "company_profiles",
      execute: async () =>
        await supabase!
          .from("company_profiles")
          .select("*")
          .eq("ticker", normalizedTicker)
          .limit(1),
    }),
    fetchOptionalSupabaseRows<CompanyGraphRow>({
      resource: "companyService.getCompanyProfile.graph",
      table: "company_relationship_graph",
      execute: async () =>
        await supabase!
          .from("company_relationship_graph")
          .select("source_ticker,source_name,target_ticker,target_name")
          .or(`source_ticker.eq.${normalizedTicker},target_ticker.eq.${normalizedTicker}`)
          .limit(20),
    }),
    fetchOptionalSupabaseRows<EventCompanyRow>({
      resource: "companyService.getCompanyProfile.events",
      table: "events",
      execute: async () =>
        await supabase!
          .from("events")
          .select("ticker,headline,metadata")
          .eq("ticker", normalizedTicker)
          .order("timestamp", { ascending: false })
          .limit(20),
    }),
  ]);

  if (profileRows[0]) {
    return toCompanyProfile(profileRows[0], normalizedTicker);
  }

  const graphMatch = graphRows.find(
    (row) =>
      row.source_ticker?.toUpperCase() === normalizedTicker || row.target_ticker?.toUpperCase() === normalizedTicker
  );
  const graphName =
    graphMatch?.source_ticker?.toUpperCase() === normalizedTicker
      ? graphMatch?.source_name
      : graphMatch?.target_name;
  const eventMatch = eventRows.find((row) => row.ticker?.toUpperCase() === normalizedTicker);

  return {
    ticker: normalizedTicker,
    name: graphName?.trim() || inferCompanyName(eventMatch ?? {}) || normalizedTicker,
    sector: inferCompanySector(eventMatch ?? {}) || "Unknown sector",
    industry: "Research coverage in progress",
    marketCap: "N/A",
    pe: 0,
    revenue: "N/A",
    employees: "N/A",
  };
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
  if (!canUseLiveSupabase()) {
    return getMockFallback<CompanySearchResult[]>(`/companies/search?query=${encodeURIComponent(sanitizedQuery)}`);
  }

  const [profileRows, graphRows, relatedRows, signalRows, eventRows] = await Promise.all([
    fetchOptionalSupabaseRows<CompanySearchRow>({
      resource: "companyService.searchCompanies.profiles",
      table: "company_profiles",
      execute: async () =>
        await supabase!
          .from("company_profiles")
          .select("ticker,name")
          .or(`ticker.ilike.%${sanitizedQuery}%,name.ilike.%${sanitizedQuery}%`)
          .limit(12),
    }),
    fetchOptionalSupabaseRows<CompanyGraphRow>({
      resource: "companyService.searchCompanies.graph",
      table: "company_relationship_graph",
      execute: async () =>
        await supabase!
          .from("company_relationship_graph")
          .select("source_ticker,source_name,target_ticker,target_name")
          .or(
            `source_ticker.ilike.%${sanitizedQuery}%,source_name.ilike.%${sanitizedQuery}%,target_ticker.ilike.%${sanitizedQuery}%,target_name.ilike.%${sanitizedQuery}%`
          )
          .limit(24),
    }),
    fetchOptionalSupabaseRows<RelatedCompanyRow>({
      resource: "companyService.searchCompanies.related",
      table: "related_companies",
      execute: async () =>
        await supabase!
          .from("related_companies")
          .select("source_ticker,target_ticker,name")
          .or(`source_ticker.ilike.%${sanitizedQuery}%,target_ticker.ilike.%${sanitizedQuery}%,name.ilike.%${sanitizedQuery}%`)
          .limit(24),
    }),
    fetchOptionalSupabaseRows<SignalSearchRow>({
      resource: "companyService.searchCompanies.signals",
      table: "signal_scores",
      execute: async () =>
        await supabase!
          .from("signal_scores")
          .select("primary_ticker,target_ticker")
          .or(`primary_ticker.ilike.%${sanitizedQuery}%,target_ticker.ilike.%${sanitizedQuery}%`)
          .limit(24),
    }),
    fetchOptionalSupabaseRows<EventCompanyRow>({
      resource: "companyService.searchCompanies.events",
      table: "events",
      execute: async () =>
        await supabase!
          .from("events")
          .select("ticker,headline,metadata")
          .limit(3000),
    }),
  ]);

  const candidates = new Map<string, CompanySearchResult>();
  profileRows.forEach((row) => addSearchCandidate(candidates, row.ticker, row.name));
  graphRows.forEach((row) => {
    addSearchCandidate(candidates, row.source_ticker, row.source_name);
    addSearchCandidate(candidates, row.target_ticker, row.target_name);
  });
  relatedRows.forEach((row) => {
    addSearchCandidate(candidates, row.source_ticker, null);
    addSearchCandidate(candidates, row.target_ticker, row.name || null);
  });
  signalRows.forEach((row) => {
    addSearchCandidate(candidates, row.primary_ticker, null);
    addSearchCandidate(candidates, row.target_ticker, null);
  });

  const uppercaseQuery = sanitizedQuery.toUpperCase();
  eventRows
    .filter((row) => {
      const tickerValue = row.ticker?.toUpperCase() ?? "";
      const headlineValue = row.headline?.toUpperCase() ?? "";
      const inferredName = inferCompanyName(row)?.toUpperCase() ?? "";
      return (
        tickerValue.includes(uppercaseQuery) ||
        headlineValue.includes(uppercaseQuery) ||
        inferredName.includes(uppercaseQuery)
      );
    })
    .forEach((row) => addSearchCandidate(candidates, row.ticker, inferCompanyName(row)));

  const ranked = rankCompanySearchResults(Array.from(candidates.values()), sanitizedQuery).slice(0, 12);
  if (ranked.length > 0) {
    return ranked;
  }

  return getMockFallback<CompanySearchResult[]>(`/companies/search?query=${encodeURIComponent(sanitizedQuery)}`);
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
        .select("trade_date,close,volume")
        .eq("ticker", normalizedTicker)
        .order("trade_date", { ascending: true })
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
