import { supabase } from "@/integrations/supabase/client";
import {
  CANONICAL_EVENT_CATEGORIES,
  filterEventsByEnabledCategories,
  sortEventCategories,
} from "@/engine/eventClassifier";
import type {
  EventStudyResult,
  ForwardCurvePoint,
  MarketEvent,
  ReturnDistributionPoint,
} from "@/types";
import {
  fetchOptionalSupabaseRows,
  fetchSupabaseWithFallback,
  getMockFallback,
} from "./supabaseService";
import { getEnabledClassificationCategories, readSettingsSnapshot } from "./settingsService";

type EventRow = {
  id?: string | number | null;
  headline?: string | null;
  title?: string | null;
  ticker?: string | null;
  primary_ticker?: string | null;
  category?: string | null;
  event_type?: string | null;
  sentiment?: string | null;
  timestamp?: string | null;
  occurred_at?: string | null;
  created_at?: string | null;
  related_companies?: unknown;
  historical_analog?: string | null;
  sample_size?: number | null;
  avg_return?: number | null;
  details?: string | null;
  description?: string | null;
};

type RelatedCompanyRow = {
  event_id?: string | number | null;
  eventId?: string | number | null;
  ticker?: string | null;
  related_ticker?: string | null;
  target_ticker?: string | null;
  name?: string | null;
  company_name?: string | null;
  relationship?: string | null;
  relationship_type?: string | null;
  relation_type?: string | null;
};

type EventStudyResultRow = {
  event_type?: string | null;
  event_category?: string | null;
  study_target_type?: string | null;
  primary_ticker?: string | null;
  related_ticker?: string | null;
  relationship_type?: string | null;
  horizon?: string | null;
  avg_return?: number | null;
  median_return?: number | null;
  win_rate?: number | null;
  sample_size?: number | null;
};

const defaultEventCategories = [...CANONICAL_EVENT_CATEGORIES];

function normalizeEventSentiment(sentiment: string | null | undefined): MarketEvent["sentiment"] {
  if (sentiment === "positive" || sentiment === "negative" || sentiment === "neutral") {
    return sentiment;
  }

  return "neutral";
}

function toEventRelationship(row: RelatedCompanyRow) {
  const ticker = row.ticker || row.related_ticker || row.target_ticker || "N/A";

  return {
    ticker,
    name: row.name || row.company_name || ticker,
    relationship: row.relationship || row.relationship_type || row.relation_type || "Related",
  };
}

function toEmbeddedRelationships(value: unknown) {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item) => {
      if (!item || typeof item !== "object") {
        return null;
      }

      const row = item as RelatedCompanyRow;
      return toEventRelationship(row);
    })
    .filter((item): item is NonNullable<typeof item> => Boolean(item));
}

function sortEventsByTimestamp(events: MarketEvent[]) {
  return events.sort((left, right) => {
    const leftTime = new Date(left.timestamp).getTime();
    const rightTime = new Date(right.timestamp).getTime();
    return rightTime - leftTime;
  });
}

function toMarketEvent(row: EventRow, relatedCompanies: MarketEvent["relatedCompanies"]): MarketEvent {
  return {
    id: String(row.id ?? row.ticker ?? row.headline ?? crypto.randomUUID()),
    headline: row.headline || row.title || "Untitled event",
    ticker: row.ticker || row.primary_ticker || "N/A",
    category: row.category || row.event_type || "Unclassified",
    sentiment: normalizeEventSentiment(row.sentiment),
    timestamp: row.timestamp || row.occurred_at || row.created_at || new Date().toISOString(),
    relatedCompanies,
    historicalAnalog: row.historical_analog || "Historical analog data is not available yet.",
    sampleSize: row.sample_size ?? 0,
    avgReturn: row.avg_return ?? 0,
    details: row.details || row.description || undefined,
  };
}

function toEventStudyResult(row: EventStudyResultRow): EventStudyResult {
  return {
    eventCategory: row.event_category || row.event_type || undefined,
    horizon: row.horizon || "Unknown",
    avgReturn: row.avg_return ?? 0,
    medianReturn: row.median_return ?? undefined,
    winRate: row.win_rate ?? 0,
    sampleSize: row.sample_size ?? 0,
  };
}

function sortStudiesByHorizon(studies: EventStudyResult[]) {
  const order = ["1D", "3D", "5D", "10D", "20D"];
  return studies.sort((left, right) => order.indexOf(left.horizon) - order.indexOf(right.horizon));
}

export async function getEvents() {
  const events = await fetchSupabaseWithFallback<EventRow, MarketEvent[]>({
    resource: "eventService.getEvents",
    table: "events",
    mockEndpoint: "/events",
    execute: async () => {
      if (!supabase) {
        return { data: null, error: null };
      }

      return await supabase.from("events").select("*");
    },
    transform: async (rows) => {
      const relatedRows = await fetchOptionalSupabaseRows<RelatedCompanyRow>({
        resource: "eventService.getEvents.relatedCompanies",
        table: "related_companies",
        execute: async () => {
          if (!supabase) {
            return { data: null, error: null };
          }

          return await supabase.from("related_companies").select("*");
        },
      });

      const relatedByEventId = relatedRows.reduce<Record<string, MarketEvent["relatedCompanies"]>>((accumulator, row) => {
        const eventId = row.event_id ?? row.eventId;

        if (!eventId) {
          return accumulator;
        }

        const key = String(eventId);
        accumulator[key] = [...(accumulator[key] ?? []), toEventRelationship(row)];
        return accumulator;
      }, {});

      return sortEventsByTimestamp(
        rows.map((row) => {
          const embeddedRelationships = toEmbeddedRelationships(row.related_companies);
          const relatedCompanies = [
            ...embeddedRelationships,
            ...(relatedByEventId[String(row.id ?? "")] ?? []),
          ];

          return toMarketEvent(row, relatedCompanies);
        })
      );
    },
  });

  return filterEventsByEnabledCategories(events, readSettingsSnapshot().classification);
}

export async function getEventCategories() {
  const events = await getEvents();
  const enabledCategories = getEnabledClassificationCategories();
  const categories = sortEventCategories([...new Set(events.map((event) => event.category))]);

  if (categories.length > 0) {
    return categories;
  }

  const enabledDefaults = defaultEventCategories.filter((category) => enabledCategories.includes(category));
  return enabledDefaults.length > 0 ? enabledDefaults : defaultEventCategories;
}

export async function getEventStudies(eventType = "Product Launch") {
  const normalizedEventType = eventType.trim() || "Product Launch";

  const detailedRows = await fetchOptionalSupabaseRows<EventStudyResultRow>({
    resource: "eventService.getEventStudies.detailed",
    table: "event_study_statistics",
    execute: async () => {
      if (!supabase) {
        return { data: null, error: null };
      }

      return await supabase
        .from("event_study_statistics")
        .select("*")
        .eq("study_target_type", "category_summary")
        .eq("event_category", normalizedEventType);
    },
  });

  if (detailedRows.length > 0) {
    return sortStudiesByHorizon(detailedRows.map(toEventStudyResult));
  }

  return fetchSupabaseWithFallback<EventStudyResultRow, EventStudyResult[]>({
    resource: "eventService.getEventStudies",
    table: "event_study_results",
    mockEndpoint: "/events/studies",
    execute: async () => {
      if (!supabase) {
        return { data: null, error: null };
      }

      return await supabase.from("event_study_results").select("*").eq("event_type", normalizedEventType);
    },
    transform: (rows) => sortStudiesByHorizon(rows.map(toEventStudyResult)),
  });
}

export async function getReturnDistribution() {
  return getMockFallback<ReturnDistributionPoint[]>("/events/distribution");
}

export async function getForwardCurve() {
  return getMockFallback<ForwardCurvePoint[]>("/events/forward-curve");
}

export async function getTimeHorizons(eventType = "Product Launch") {
  const studies = await getEventStudies(eventType);
  const horizons = [...new Set(studies.map((study) => study.horizon))];
  return horizons.length > 0 ? horizons : ["1D", "3D", "5D", "10D", "20D"];
}
