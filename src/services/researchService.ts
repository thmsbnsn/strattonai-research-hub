import { supabase } from "@/integrations/supabase/client";
import { generateJournalEntriesFromSignals } from "@/engine/researchJournalEngine";
import type { JournalEntry, ResearchInsight } from "@/types";
import { getEvents } from "./eventService";
import { getTopSignals } from "./signalService";
import { fetchOptionalSupabaseRows, fetchSupabaseWithFallback, getMockFallback } from "./supabaseService";

type ResearchInsightRow = {
  id?: string | number | null;
  title?: string | null;
  summary?: string | null;
  confidence?: string | null;
  event_count?: number | null;
};

type JournalEntryRow = {
  id?: string | number | null;
  date?: string | null;
  title?: string | null;
  events?: string[] | string | null;
  patterns?: string | null;
  hypothesis?: string | null;
  confidence?: string | null;
};

function normalizeConfidence(value: string | null | undefined): "High" | "Moderate" | "Low" {
  if (value === "High" || value === "Moderate" || value === "Low") {
    return value;
  }

  return "Moderate";
}

function normalizeEventList(value: JournalEntryRow["events"]) {
  if (Array.isArray(value)) {
    return value;
  }

  if (typeof value === "string") {
    try {
      const parsed = JSON.parse(value);
      if (Array.isArray(parsed)) {
        return parsed.filter((item): item is string => typeof item === "string");
      }
    } catch {
      return value
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);
    }
  }

  return [];
}

function toResearchInsight(row: ResearchInsightRow): ResearchInsight {
  return {
    id: String(row.id ?? row.title ?? crypto.randomUUID()),
    title: row.title || "Untitled insight",
    summary: row.summary || "No summary available yet.",
    confidence: normalizeConfidence(row.confidence),
    eventCount: row.event_count ?? 0,
  };
}

function toJournalEntry(row: JournalEntryRow): JournalEntry {
  return {
    id: String(row.id ?? row.title ?? crypto.randomUUID()),
    date: row.date || new Date().toISOString().slice(0, 10),
    title: row.title || "Untitled journal entry",
    events: normalizeEventList(row.events),
    patterns: row.patterns || "No pattern analysis available yet.",
    hypothesis: row.hypothesis || "No hypothesis recorded yet.",
    confidence: normalizeConfidence(row.confidence),
  };
}

export async function getResearchInsights() {
  return fetchSupabaseWithFallback<ResearchInsightRow, ResearchInsight[]>({
    resource: "researchService.getResearchInsights",
    table: "research_insights",
    mockEndpoint: "/research/insights",
    execute: async () => {
      if (!supabase) {
        return { data: null, error: null };
      }

      return await supabase.from("research_insights").select("*");
    },
    transform: (rows) => rows.map(toResearchInsight),
  });
}

export async function getJournalEntries() {
  const liveRows = await fetchOptionalSupabaseRows<JournalEntryRow>({
    resource: "researchService.getJournalEntries.live",
    table: "journal_entries",
    execute: async () => {
      if (!supabase) {
        return { data: null, error: null };
      }

      return await supabase.from("journal_entries").select("*");
    },
  });

  if (liveRows.length > 0) {
    return liveRows.map(toJournalEntry);
  }

  const [events, signals] = await Promise.all([getEvents(), getTopSignals(12)]);
  const generatedEntries = generateJournalEntriesFromSignals(events, signals);

  if (generatedEntries.length > 0) {
    return generatedEntries;
  }

  return getMockFallback<JournalEntry[]>("/research/journal");
}
