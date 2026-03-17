import { useEffect, useMemo } from "react";
import { useQueries, useQuery } from "@tanstack/react-query";
import { BarChart3, X } from "lucide-react";
import {
  getEvidenceSlices,
  getCategorySummaryStudies,
  getPrimaryStudies,
  getRelatedTickerStudies,
  getRelationshipStudies,
  type EventStudySlice,
} from "@/services/eventStudyStatisticsService";
import { ListSkeleton } from "@/components/LoadingSkeletons";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

function seriesKey(row: EventStudySlice) {
  return `${row.studyTargetType}:${row.eventCategory}:${row.primaryTicker || ""}:${row.relatedTicker || ""}:${row.relationshipType || ""}`;
}

const HORIZON_ORDER = ["1D", "3D", "5D", "10D", "20D"];

function sparklinePath(values: number[]) {
  if (values.length === 0) return "";
  const width = 120;
  const height = 40;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  return values
    .map((value, index) => {
      const x = (index / Math.max(values.length - 1, 1)) * width;
      const y = height - ((value - min) / range) * height;
      return `${index === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}

function StudyRows({ rows }: { rows: EventStudySlice[] }) {
  const grouped = useMemo(() => {
    const map = new Map<string, EventStudySlice[]>();
    rows.forEach((row) => {
      const key = seriesKey(row);
      map.set(key, [...(map.get(key) ?? []), row]);
    });
    return map;
  }, [rows]);

  if (rows.length === 0) {
    return <p className="text-xs text-muted-foreground">No slices available.</p>;
  }

  return (
    <div className="space-y-3">
      {rows.map((row) => {
        const series = (grouped.get(seriesKey(row)) ?? []).sort(
          (left, right) => HORIZON_ORDER.indexOf(left.horizon) - HORIZON_ORDER.indexOf(right.horizon)
        );
        const path = sparklinePath(series.map((point) => point.avgReturn));
        const finalPoint = series[series.length - 1];
        return (
          <div key={`${row.studyKey}-${row.horizon}`} className="rounded-lg border border-border bg-muted/30 p-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-sm font-medium text-foreground">{row.eventCategory}</div>
                <div className="text-xs text-muted-foreground">
                  {row.primaryTicker || "—"} {row.relatedTicker ? `-> ${row.relatedTicker}` : ""} {row.relationshipType ? `· ${row.relationshipType}` : ""}
                </div>
              </div>
              <div className={`font-mono text-sm ${row.avgReturn >= 0 ? "text-success" : "text-danger"}`}>
                {row.avgReturn >= 0 ? "+" : ""}{row.avgReturn.toFixed(2)}%
              </div>
            </div>
            <div className="mt-2 flex items-center justify-between gap-3">
              <div className="text-[11px] text-muted-foreground">
                <div>
                  {row.horizon} · median {row.medianReturn.toFixed(2)}% · win {row.winRate.toFixed(1)}%
                </div>
                {row.notes ? <div className="italic text-muted-foreground/80">{row.notes}</div> : null}
              </div>
              <div className="flex items-center gap-2">
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                    row.sampleSize >= 20 ? "bg-success/10 text-success" : row.sampleSize >= 10 ? "bg-warning/10 text-warning" : "bg-danger/10 text-danger"
                  }`}
                >
                  n={row.sampleSize}
                </span>
                <svg width="120" height="40" className="shrink-0 overflow-visible">
                  <path
                    d={path}
                    fill="none"
                    stroke="currentColor"
                    className={(finalPoint?.avgReturn ?? row.avgReturn) >= 0 ? "text-emerald-400" : "text-red-400"}
                    strokeWidth="1.75"
                  />
                </svg>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function EvidenceSliceDrawer({
  ticker,
  category,
  open,
  onOpenChange,
}: {
  ticker: string | null;
  category?: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const primaryQuery = useQuery({
    queryKey: ["studies", "primary", ticker ?? "none", category ?? "all"],
    queryFn: () => getPrimaryStudies(ticker || "", category ?? undefined),
    enabled: Boolean(ticker && open),
  });
  const relatedQuery = useQuery({
    queryKey: ["studies", "related", ticker ?? "none", category ?? "all"],
    queryFn: () => getRelatedTickerStudies(ticker || "", category ?? undefined),
    enabled: Boolean(ticker && open),
  });
  const categoryQuery = useQuery({
    queryKey: ["studies", "category-summary", category ?? "none"],
    queryFn: () => getCategorySummaryStudies(category || ""),
    enabled: Boolean(category && open),
  });
  const allSlicesQuery = useQuery({
    queryKey: ["studies", "evidence", ticker ?? "none"],
    queryFn: () => getEvidenceSlices(ticker || ""),
    enabled: Boolean(ticker && open),
  });

  const relationshipTypes = useMemo(
    () => Array.from(new Set((allSlicesQuery.data ?? []).map((row) => row.relationshipType).filter(Boolean))) as string[],
    [allSlicesQuery.data]
  );
  const relationshipQueries = useQueries({
    queries: relationshipTypes.map((relationshipType) => ({
      queryKey: ["studies", "relationship", relationshipType, category ?? "all"],
      queryFn: () => getRelationshipStudies(relationshipType, category ?? undefined),
      enabled: Boolean(open),
    })),
  });
  const relationshipRows = relationshipQueries.flatMap((query) => query.data ?? []);
  const isLoading = primaryQuery.isLoading || relatedQuery.isLoading || allSlicesQuery.isLoading || categoryQuery.isLoading || relationshipQueries.some((query) => query.isLoading);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onOpenChange(false);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onOpenChange, open]);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full border-border bg-background transition-transform duration-200 sm:max-w-2xl">
        <SheetHeader>
          <div className="flex items-center justify-between gap-3">
            <SheetTitle className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-primary" />
              Evidence Slices
            </SheetTitle>
            <button onClick={() => onOpenChange(false)} className="rounded-md p-1 text-muted-foreground hover:bg-muted/40 hover:text-foreground">
              <X className="h-4 w-4" />
            </button>
          </div>
          <SheetDescription>
            {ticker ? `Historical study depth touching ${ticker}` : "Select a ticker to inspect evidence slices."}
          </SheetDescription>
        </SheetHeader>
        <div className="mt-6">
          {!ticker ? (
            <p className="text-sm text-muted-foreground">No ticker selected.</p>
          ) : isLoading ? (
            <ListSkeleton count={3} />
          ) : (
            <Tabs defaultValue="primary" className="space-y-4">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="primary">Primary Studies</TabsTrigger>
                <TabsTrigger value="related">Related Studies</TabsTrigger>
                <TabsTrigger value="relationship">Relationship Studies</TabsTrigger>
              </TabsList>
              <TabsContent value="primary">
                <StudyRows rows={[...(primaryQuery.data ?? []), ...(categoryQuery.data ?? [])]} />
              </TabsContent>
              <TabsContent value="related">
                <StudyRows rows={relatedQuery.data ?? []} />
              </TabsContent>
              <TabsContent value="relationship">
                <StudyRows rows={relationshipRows} />
              </TabsContent>
            </Tabs>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
