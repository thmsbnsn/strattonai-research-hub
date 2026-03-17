import { useMemo, useState } from "react";
import { useQueries, useQuery } from "@tanstack/react-query";
import { ArrowDown, ArrowUp, GitBranch } from "lucide-react";
import { getCompanyRelationships } from "@/services/companyService";
import {
  getEvidenceSlices,
  getRelatedTickerStudies,
  getRelationshipStudies,
  type EventStudySlice,
} from "@/services/eventStudyStatisticsService";
import { ListSkeleton } from "@/components/LoadingSkeletons";
import { EvidenceSliceDrawer } from "./EvidenceSliceDrawer";

type SortKey = "eventCategory" | "relatedTicker" | "relationshipType" | "horizon" | "avgReturn" | "medianReturn" | "winRate" | "sampleSize";

function sortRows(rows: EventStudySlice[], sortKey: SortKey, descending: boolean) {
  return rows.slice().sort((left, right) => {
    const leftValue =
      sortKey === "eventCategory"
        ? left.eventCategory
        : sortKey === "relatedTicker"
        ? left.relatedTicker || ""
        : sortKey === "relationshipType"
        ? left.relationshipType || ""
        : sortKey === "horizon"
        ? left.horizon
        : left[sortKey];
    const rightValue =
      sortKey === "eventCategory"
        ? right.eventCategory
        : sortKey === "relatedTicker"
        ? right.relatedTicker || ""
        : sortKey === "relationshipType"
        ? right.relationshipType || ""
        : sortKey === "horizon"
        ? right.horizon
        : right[sortKey];

    if (typeof leftValue === "number" && typeof rightValue === "number") {
      return descending ? rightValue - leftValue : leftValue - rightValue;
    }

    const comparison = String(leftValue).localeCompare(String(rightValue));
    return descending ? -comparison : comparison;
  });
}

function SortLabel({
  active,
  descending,
  children,
}: {
  active: boolean;
  descending: boolean;
  children: string;
}) {
  return (
    <span className="inline-flex items-center gap-1">
      {children}
      {active ? (descending ? <ArrowDown className="h-3 w-3" /> : <ArrowUp className="h-3 w-3" />) : null}
    </span>
  );
}

export function RelationshipStudyTable({
  ticker,
  category,
  limit,
  maxRows,
  compact = false,
}: {
  ticker: string;
  category?: string;
  limit?: number;
  maxRows?: number;
  compact?: boolean;
}) {
  const [sortKey, setSortKey] = useState<SortKey>("avgReturn");
  const [descending, setDescending] = useState(true);
  const [drawerTicker, setDrawerTicker] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const relationshipsQuery = useQuery({
    queryKey: ["company", "relationships"],
    queryFn: getCompanyRelationships,
  });

  const relationshipTypes = useMemo(
    () =>
      Array.from(
        new Set(
          (relationshipsQuery.data ?? [])
            .filter((relationship) => relationship.source === ticker || relationship.target === ticker)
            .map((relationship) => relationship.relationship)
        )
      ),
    [relationshipsQuery.data, ticker]
  );

  const relatedStudiesQuery = useQuery({
    queryKey: ["studies", "related", ticker, category ?? "all"],
    queryFn: () => getRelatedTickerStudies(ticker, category),
  });

  const relationshipQueries = useQueries({
    queries: relationshipTypes.map((relationshipType) => ({
      queryKey: ["studies", "relationship", relationshipType, category ?? "all"],
      queryFn: () => getRelationshipStudies(relationshipType, category),
    })),
  });

  const evidenceQuery = useQuery({
    queryKey: ["studies", "evidence-slices", ticker],
    queryFn: () => getEvidenceSlices(ticker),
  });

  const rows = useMemo(() => {
    const related = relatedStudiesQuery.data ?? [];
    const relationship = relationshipQueries.flatMap((query) => query.data ?? []);
    const direct = (evidenceQuery.data ?? []).filter(
      (row) => row.relationshipType && row.studyTargetType !== "category_summary"
    );
    const merged = [...related, ...relationship, ...direct];
    const unique = Array.from(
      new Map(
        merged.map((row) => [
          `${row.studyTargetType}:${row.eventCategory}:${row.relatedTicker || ""}:${row.relationshipType || ""}:${row.horizon}`,
          row,
        ])
      ).values()
    );
    const sorted = sortRows(unique, sortKey, descending);
    const rowLimit = typeof maxRows === "number" ? maxRows : limit;
    return typeof rowLimit === "number" ? sorted.slice(0, rowLimit) : sorted;
  }, [category, descending, evidenceQuery.data, limit, maxRows, relatedStudiesQuery.data, relationshipQueries, sortKey]);

  const isLoading =
    relationshipsQuery.isLoading ||
    relatedStudiesQuery.isLoading ||
    evidenceQuery.isLoading ||
    relationshipQueries.some((query) => query.isLoading);

  const toggleSort = (nextKey: SortKey) => {
    if (sortKey === nextKey) {
      setDescending((current) => !current);
      return;
    }
    setSortKey(nextKey);
    setDescending(nextKey !== "eventCategory" && nextKey !== "relatedTicker" && nextKey !== "relationshipType" && nextKey !== "horizon");
  };

  return (
    <div className="terminal-card p-4">
      <div className="mb-3 flex items-center gap-2">
        <GitBranch className="h-4 w-4 text-primary" />
        <h4 className="text-sm font-semibold text-foreground">
          {compact ? `${ticker} Related Studies` : "Relationship Study Slices"}
        </h4>
      </div>

      {isLoading ? (
        <ListSkeleton count={3} />
      ) : rows.length === 0 ? (
        <p className="text-xs text-muted-foreground">No study data yet for this ticker.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full data-grid text-xs">
            <thead>
              <tr className="border-b border-border">
                <th className="px-3 py-2 text-left">
                  <button onClick={() => toggleSort("eventCategory")} className="text-muted-foreground hover:text-foreground">
                    <SortLabel active={sortKey === "eventCategory"} descending={descending}>Event Category</SortLabel>
                  </button>
                </th>
                <th className="px-3 py-2 text-left">
                  <button onClick={() => toggleSort("relatedTicker")} className="text-muted-foreground hover:text-foreground">
                    <SortLabel active={sortKey === "relatedTicker"} descending={descending}>Related Ticker</SortLabel>
                  </button>
                </th>
                <th className="px-3 py-2 text-left">
                  <button onClick={() => toggleSort("relationshipType")} className="text-muted-foreground hover:text-foreground">
                    <SortLabel active={sortKey === "relationshipType"} descending={descending}>Relationship</SortLabel>
                  </button>
                </th>
                <th className="px-3 py-2 text-right">Horizon</th>
                <th className="px-3 py-2 text-right">Avg Return</th>
                <th className="px-3 py-2 text-right">Median</th>
                <th className="px-3 py-2 text-right">Win Rate</th>
                <th className="px-3 py-2 text-right">Sample</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr
                  key={`${row.studyKey}-${row.horizon}`}
                  className="cursor-pointer border-b border-border/50 hover:bg-muted/20"
                  onClick={() => {
                    setDrawerTicker(row.relatedTicker || row.primaryTicker || ticker);
                    setDrawerOpen(true);
                  }}
                >
                  <td className="px-3 py-2 text-foreground">{row.eventCategory}</td>
                  <td className="px-3 py-2 font-mono text-primary">{row.relatedTicker || row.primaryTicker || "—"}</td>
                  <td className="px-3 py-2 text-muted-foreground">{row.relationshipType || "—"}</td>
                  <td className="px-3 py-2 text-right font-mono text-foreground">{row.horizon}</td>
                  <td className={`px-3 py-2 text-right font-mono ${row.avgReturn >= 0 ? "text-success" : "text-danger"}`}>
                    <div className="flex items-center justify-end gap-2">
                      <span className="inline-block h-1.5 rounded-full bg-muted" style={{ width: "48px" }}>
                        <span
                          className={`block h-1.5 rounded-full ${row.avgReturn >= 0 ? "bg-success" : "bg-danger"}`}
                          style={{ width: `${Math.min(Math.abs(row.avgReturn) * 8, 48)}px` }}
                        />
                      </span>
                      <span>{row.avgReturn >= 0 ? "+" : ""}{row.avgReturn.toFixed(2)}%</span>
                    </div>
                  </td>
                  <td className={`px-3 py-2 text-right font-mono ${row.medianReturn >= 0 ? "text-success" : "text-danger"}`}>
                    {row.medianReturn >= 0 ? "+" : ""}{row.medianReturn.toFixed(2)}%
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-foreground">{row.winRate.toFixed(1)}%</td>
                  <td className="px-3 py-2 text-right font-mono text-muted-foreground">{row.sampleSize}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <EvidenceSliceDrawer ticker={drawerTicker} category={category} open={drawerOpen} onOpenChange={setDrawerOpen} />
    </div>
  );
}
