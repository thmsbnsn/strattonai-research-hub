import { useQuery } from "@tanstack/react-query";
import { Database, TriangleAlert, Wifi } from "lucide-react";
import { getDashboardDataSourceStatus } from "@/services/dashboardService";

const statusStyles = {
  connected: {
    badge: "border-success/30 bg-success/10 text-success",
    icon: Wifi,
  },
  fallback: {
    badge: "border-warning/30 bg-warning/10 text-warning",
    icon: Database,
  },
  partial: {
    badge: "border-primary/30 bg-primary/10 text-primary",
    icon: Database,
  },
  error: {
    badge: "border-danger/30 bg-danger/10 text-danger",
    icon: TriangleAlert,
  },
} as const;

export function DataSourceStatusBadge() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard", "data-source-status"],
    queryFn: getDashboardDataSourceStatus,
    staleTime: 30_000,
    refetchInterval: 60_000,
  });

  if (isLoading) {
    return (
      <div className="inline-flex items-center gap-2 rounded-full border border-border bg-muted/40 px-3 py-1 text-xs text-muted-foreground">
        <Database className="h-3.5 w-3.5" />
        <span>Checking Supabase…</span>
      </div>
    );
  }

  const currentStatus = data?.status ?? "fallback";
  const Icon = statusStyles[currentStatus].icon;

  return (
    <div className="flex flex-wrap items-center gap-2">
      <div
        className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium ${statusStyles[currentStatus].badge}`}
        title={data?.probes.map((probe) => `${probe.table}: ${probe.detail}`).join("\n")}
      >
        <Icon className="h-3.5 w-3.5" />
        <span>{data?.label ?? "Fallback to mock data"}</span>
      </div>
      {data?.detail ? <p className="text-xs text-muted-foreground">{data.detail}</p> : null}
    </div>
  );
}
