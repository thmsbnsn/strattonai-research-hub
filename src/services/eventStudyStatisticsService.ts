import { supabase } from "@/integrations/supabase/client";
import { fetchOptionalSupabaseRows } from "./supabaseService";

export type EventStudySlice = {
  studyKey: string;
  studyTargetType: "category_summary" | "primary" | "relationship" | "related";
  eventCategory: string;
  primaryTicker?: string;
  relatedTicker?: string;
  relationshipType?: string;
  horizon: string;
  avgReturn: number;
  medianReturn: number;
  winRate: number;
  sampleSize: number;
  notes?: string;
  metadata: Record<string, unknown>;
};

type EventStudySliceRow = {
  study_key?: string | null;
  study_target_type?: "category_summary" | "primary" | "relationship" | "related" | null;
  event_category?: string | null;
  primary_ticker?: string | null;
  related_ticker?: string | null;
  relationship_type?: string | null;
  horizon?: string | null;
  avg_return?: number | null;
  median_return?: number | null;
  win_rate?: number | null;
  sample_size?: number | null;
  notes?: string | null;
  metadata?: Record<string, unknown> | null;
};

function toSlice(row: EventStudySliceRow): EventStudySlice {
  return {
    studyKey: row.study_key || crypto.randomUUID(),
    studyTargetType: row.study_target_type || "category_summary",
    eventCategory: row.event_category || "Unknown",
    primaryTicker: row.primary_ticker || undefined,
    relatedTicker: row.related_ticker || undefined,
    relationshipType: row.relationship_type || undefined,
    horizon: row.horizon || "Unknown",
    avgReturn: row.avg_return ?? 0,
    medianReturn: row.median_return ?? 0,
    winRate: row.win_rate ?? 0,
    sampleSize: row.sample_size ?? 0,
    notes: row.notes || undefined,
    metadata: row.metadata || {},
  };
}

function sortByHorizonAndReturn(rows: EventStudySlice[]) {
  const order = ["1D", "3D", "5D", "10D", "20D"];
  return rows.slice().sort((left, right) => {
    const leftIndex = order.indexOf(left.horizon);
    const rightIndex = order.indexOf(right.horizon);
    const horizonDelta = (leftIndex === -1 ? order.length : leftIndex) - (rightIndex === -1 ? order.length : rightIndex);
    if (horizonDelta !== 0) return horizonDelta;
    return right.avgReturn - left.avgReturn;
  });
}

export async function getCategorySummaryStudies(category: string) {
  const rows = await fetchOptionalSupabaseRows<EventStudySliceRow>({
    resource: "eventStudyStatisticsService.getCategorySummaryStudies",
    table: "event_study_statistics",
    execute: async () => {
      if (!supabase) return { data: null, error: null };
      return await supabase
        .from("event_study_statistics")
        .select("*")
        .eq("study_target_type", "category_summary")
        .eq("event_category", category);
    },
  });
  return sortByHorizonAndReturn(rows.map(toSlice));
}

export async function getPrimaryStudies(ticker: string, category?: string) {
  const normalizedTicker = ticker.trim().toUpperCase();
  const rows = await fetchOptionalSupabaseRows<EventStudySliceRow>({
    resource: "eventStudyStatisticsService.getPrimaryStudies",
    table: "event_study_statistics",
    execute: async () => {
      if (!supabase) return { data: null, error: null };
      let query = supabase
        .from("event_study_statistics")
        .select("*")
        .eq("study_target_type", "primary")
        .eq("primary_ticker", normalizedTicker);
      if (category) query = query.eq("event_category", category);
      return await query;
    },
  });
  return sortByHorizonAndReturn(rows.map(toSlice));
}

export async function getRelatedTickerStudies(relatedTicker: string, category?: string) {
  const normalizedTicker = relatedTicker.trim().toUpperCase();
  const rows = await fetchOptionalSupabaseRows<EventStudySliceRow>({
    resource: "eventStudyStatisticsService.getRelatedTickerStudies",
    table: "event_study_statistics",
    execute: async () => {
      if (!supabase) return { data: null, error: null };
      let query = supabase
        .from("event_study_statistics")
        .select("*")
        .eq("study_target_type", "related")
        .eq("related_ticker", normalizedTicker);
      if (category) query = query.eq("event_category", category);
      return await query;
    },
  });
  return sortByHorizonAndReturn(rows.map(toSlice));
}

export async function getRelationshipStudies(relationshipType: string, category?: string) {
  const rows = await fetchOptionalSupabaseRows<EventStudySliceRow>({
    resource: "eventStudyStatisticsService.getRelationshipStudies",
    table: "event_study_statistics",
    execute: async () => {
      if (!supabase) return { data: null, error: null };
      let query = supabase
        .from("event_study_statistics")
        .select("*")
        .eq("study_target_type", "relationship")
        .eq("relationship_type", relationshipType);
      if (category) query = query.eq("event_category", category);
      return await query;
    },
  });
  return sortByHorizonAndReturn(rows.map(toSlice));
}

export async function getEvidenceSlices(ticker: string) {
  const normalizedTicker = ticker.trim().toUpperCase();
  const rows = await fetchOptionalSupabaseRows<EventStudySliceRow>({
    resource: "eventStudyStatisticsService.getEvidenceSlices",
    table: "event_study_statistics",
    execute: async () => {
      if (!supabase) return { data: null, error: null };
      return await supabase
        .from("event_study_statistics")
        .select("*")
        .or(`primary_ticker.eq.${normalizedTicker},related_ticker.eq.${normalizedTicker}`);
    },
  });
  return sortByHorizonAndReturn(rows.map(toSlice));
}
