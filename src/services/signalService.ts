import { supabase } from "@/integrations/supabase/client";
import type { SignalScore } from "@/models";
import { fetchSupabaseWithFallback } from "./supabaseService";

type SignalRow = {
  id?: string | null;
  event_id?: string | null;
  event_category?: string | null;
  primary_ticker?: string | null;
  related_ticker?: string | null;
  target_ticker?: string | null;
  target_type?: string | null;
  relationship_type?: string | null;
  horizon?: string | null;
  score?: number | null;
  confidence_band?: string | null;
  evidence_summary?: string | null;
  sample_size?: number | null;
  avg_return?: number | null;
  median_return?: number | null;
  win_rate?: number | null;
  origin_type?: string | null;
};

function normalizeConfidenceBand(value: string | null | undefined): SignalScore["confidenceBand"] {
  if (value === "High" || value === "Moderate" || value === "Low") {
    return value;
  }

  return "Low";
}

function normalizeTargetType(value: string | null | undefined): SignalScore["targetType"] {
  return value === "related" ? "related" : "primary";
}

function normalizeOriginType(value: string | null | undefined): SignalScore["originType"] {
  if (value === "explicit" || value === "inferred" || value === "primary") {
    return value;
  }

  return "primary";
}

function toSignalScore(row: SignalRow): SignalScore {
  const targetTicker = row.target_ticker || row.primary_ticker || "N/A";
  const relatedTicker =
    row.related_ticker || (normalizeTargetType(row.target_type) === "related" ? targetTicker : undefined);

  return {
    id: row.id || `${targetTicker}-${row.horizon || "unknown"}`,
    eventId: row.event_id || "",
    eventCategory: row.event_category || "Unknown",
    primaryTicker: row.primary_ticker || "N/A",
    relatedTicker,
    targetTicker,
    targetType: normalizeTargetType(row.target_type),
    relationshipType: row.relationship_type || undefined,
    horizon: row.horizon || "Unknown",
    score: row.score ?? 0,
    confidenceBand: normalizeConfidenceBand(row.confidence_band),
    evidenceSummary: row.evidence_summary || "No evidence summary available.",
    sampleSize: row.sample_size ?? 0,
    avgReturn: row.avg_return ?? 0,
    medianReturn: row.median_return ?? 0,
    winRate: row.win_rate ?? 0,
    originType: normalizeOriginType(row.origin_type),
  };
}

export async function getSignalScores(ticker?: string) {
  const normalizedTicker = ticker?.trim().toUpperCase();
  const mockLimit = normalizedTicker ? 50 : 25;

  const scores = await fetchSupabaseWithFallback<SignalRow, SignalScore[]>({
    resource: "signalService.getSignalScores",
    table: "signal_scores",
    mockEndpoint: `/signals/top?limit=${mockLimit}`,
    execute: async () => {
      if (!supabase) {
        return { data: null, error: null };
      }

      let query = supabase
        .from("signal_scores")
        .select("*")
        .order("score", { ascending: false });

      if (normalizedTicker) {
        query = query.eq("primary_ticker", normalizedTicker);
      }

      return await query;
    },
    transform: (rows) => rows.map(toSignalScore).sort((left, right) => right.score - left.score),
  });

  const filteredScores = normalizedTicker
    ? scores.filter((score) => score.primaryTicker === normalizedTicker)
    : scores;

  return filteredScores.sort((left, right) => right.score - left.score);
}

export async function getSignalsForTicker(ticker: string) {
  const normalizedTicker = ticker.trim().toUpperCase();
  if (!normalizedTicker) {
    return [] as SignalScore[];
  }

  const scores = await fetchSupabaseWithFallback<SignalRow, SignalScore[]>({
    resource: "signalService.getSignalsForTicker",
    table: "signal_scores",
    mockEndpoint: "/signals/top?limit=50",
    execute: async () => {
      if (!supabase) {
        return { data: null, error: null };
      }

      return await supabase
        .from("signal_scores")
        .select("*")
        .or(`primary_ticker.eq.${normalizedTicker},target_ticker.eq.${normalizedTicker}`)
        .order("score", { ascending: false });
    },
    transform: (rows) => rows.map(toSignalScore).sort((left, right) => right.score - left.score),
  });

  return scores
    .filter((score) =>
      [score.primaryTicker, score.targetTicker, score.relatedTicker]
        .filter(Boolean)
        .map((value) => value!.toUpperCase())
        .includes(normalizedTicker)
    )
    .sort((left, right) => right.score - left.score);
}

export async function getTopSignals(limit = 5, ticker?: string) {
  const scores = await getSignalScores(ticker);
  return scores.slice(0, limit);
}
