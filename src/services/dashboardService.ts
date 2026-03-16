import type { DataSourceProbe, DataSourceStatus } from "./supabaseService";
import { probeSupabaseTable } from "./supabaseService";

const dashboardProbeTables = [
  "events",
  "related_companies",
  "company_relationship_graph",
  "research_insights",
  "journal_entries",
  "paper_trades",
  "company_profiles",
  "event_study_results",
  "event_study_statistics",
  "signal_scores",
] as const;

export interface DashboardDataSourceStatus {
  status: DataSourceStatus;
  label: string;
  detail: string;
  probes: DataSourceProbe[];
}

export async function getDashboardDataSourceStatus(): Promise<DashboardDataSourceStatus> {
  const probes = await Promise.all(dashboardProbeTables.map((table) => probeSupabaseTable(table)));
  const connectedCount = probes.filter((probe) => probe.status === "connected").length;
  const fallbackCount = probes.filter((probe) => probe.status === "fallback").length;

  if (probes.some((probe) => probe.status === "error")) {
    const firstError = probes.find((probe) => probe.status === "error");

    return {
      status: "error",
      label: "Fetch error",
      detail: firstError?.detail ?? "Supabase queries are failing.",
      probes,
    };
  }

  if (connectedCount > 0 && fallbackCount > 0) {
    const fallbackTables = probes
      .filter((probe) => probe.status === "fallback")
      .map((probe) => probe.table)
      .join(", ");

    return {
      status: "partial",
      label: "Partial live / partial fallback",
      detail: fallbackTables
        ? `Live tables: ${connectedCount}. Mock fallback still active for: ${fallbackTables}.`
        : `Live tables: ${connectedCount}.`,
      probes,
    };
  }

  if (fallbackCount > 0) {
    const fallbackTables = probes
      .filter((probe) => probe.status === "fallback")
      .map((probe) => probe.table)
      .join(", ");

    return {
      status: "fallback",
      label: "Mock fallback",
      detail: fallbackTables
        ? `No seeded live data yet for: ${fallbackTables}.`
        : "The UI is using mock fallbacks.",
      probes,
    };
  }

  return {
    status: "connected",
    label: "Supabase connected",
    detail: "All first-pass tables responded with data.",
    probes,
  };
}
