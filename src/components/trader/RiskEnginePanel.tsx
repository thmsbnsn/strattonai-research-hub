import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ShieldAlert, X } from "lucide-react";
import { assessRisk, getRiskGateLog } from "@/services/traderGatewayService";
import type { PortfolioAllocation } from "@/models";

export function RiskEnginePanel({ allocations }: { allocations: PortfolioAllocation[] }) {
  const [dismissedWarnings, setDismissedWarnings] = useState<string[]>([]);
  const allocationMap = useMemo(
    () =>
      allocations.reduce<Record<string, number>>((accumulator, allocation) => {
        accumulator[allocation.ticker] = allocation.allocationDollars;
        return accumulator;
      }, {}),
    [allocations]
  );

  const riskQuery = useQuery({
    queryKey: ["gateway", "risk", JSON.stringify(allocationMap)],
    queryFn: () => assessRisk(allocationMap),
    enabled: allocations.length > 0,
  });
  const riskGateLogQuery = useQuery({
    queryKey: ["gateway", "risk-gate-log"],
    queryFn: getRiskGateLog,
  });

  const warnings = [
    ...(riskQuery.data?.sectorBreachWarnings ?? []),
    ...(riskQuery.data?.clusterWarnings ?? []),
  ].filter((warning) => !dismissedWarnings.includes(warning));

  return (
    <div className="terminal-card p-4">
      <div className="mb-4 flex items-center gap-2">
        <ShieldAlert className="h-4 w-4 text-primary" />
        <div>
          <h3 className="text-sm font-semibold text-foreground">Risk Engine</h3>
          <p className="text-xs text-muted-foreground">Volatility, sector, cluster, and factor diagnostics for the current allocation map.</p>
        </div>
      </div>

      {allocations.length === 0 ? (
        <p className="text-xs text-muted-foreground">Construct a portfolio first to generate a risk report.</p>
      ) : (
        <div className="space-y-4">
          {riskQuery.isError ? (
            <div className="rounded-md border border-warning/20 bg-warning/10 px-3 py-2 text-xs text-warning">
              Gateway offline — showing cached data where possible.
            </div>
          ) : null}
          <div className="flex justify-end">
            <button onClick={() => riskQuery.refetch()} className="rounded-md border border-border bg-muted/30 px-3 py-2 text-xs text-foreground hover:bg-muted/50">
              Re-assess
            </button>
          </div>
          {warnings.map((warning) => (
            <div key={warning} className="flex items-start justify-between gap-3 rounded-md border border-warning/20 bg-warning/10 px-3 py-2 text-xs text-warning">
              <span>{warning}</span>
              <button onClick={() => setDismissedWarnings((current) => [...current, warning])}>
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}

          <div className="overflow-x-auto">
            <table className="w-full data-grid text-xs">
              <thead>
                <tr className="border-b border-border">
                  <th className="px-3 py-2 text-left text-muted-foreground">Ticker</th>
                  <th className="px-3 py-2 text-right text-muted-foreground">Vol</th>
                  <th className="px-3 py-2 text-right text-muted-foreground">Beta</th>
                  <th className="px-3 py-2 text-right text-muted-foreground">VaR</th>
                  <th className="px-3 py-2 text-right text-muted-foreground">Max DD</th>
                </tr>
              </thead>
              <tbody>
                {(riskQuery.data?.metrics ?? []).map((metric) => (
                  <tr key={metric.ticker} className="border-b border-border/50 hover:bg-muted/20">
                    <td className="px-3 py-2 font-mono text-primary">{metric.ticker}</td>
                    <td className={`px-3 py-2 text-right font-mono ${metric.blockedHighVol ? "text-danger" : "text-foreground"}`}>
                      {metric.annualizedVol !== null ? `${(metric.annualizedVol * 100).toFixed(1)}%` : "—"}
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-foreground">{metric.beta !== null ? metric.beta.toFixed(2) : "—"}</td>
                    <td className="px-3 py-2 text-right font-mono text-foreground">{metric.valueAtRisk95 !== null ? `${(metric.valueAtRisk95 * 100).toFixed(2)}%` : "—"}</td>
                    <td className="px-3 py-2 text-right font-mono text-danger">{metric.maxDrawdown !== null ? `${(metric.maxDrawdown * 100).toFixed(2)}%` : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <div className="rounded-lg border border-border bg-background/50 p-3">
              <div className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Sector Exposure</div>
              <div className="space-y-2">
                {Object.entries(riskQuery.data?.sectorExposure ?? {}).map(([sector, weight]) => (
                  <div key={sector}>
                    <div className="mb-1 flex items-center justify-between text-xs text-muted-foreground">
                      <span>{sector}</span>
                      <span className="font-mono text-foreground">{(weight * 100).toFixed(1)}%</span>
                    </div>
                    <div className="h-2 rounded-full bg-muted">
                      <div className={`h-2 rounded-full ${weight > 0.35 ? "bg-danger" : "bg-primary"}`} style={{ width: `${Math.min(weight * 100, 100)}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-lg border border-border bg-background/50 p-3">
              <div className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Correlation Heatmap</div>
              <div className="grid gap-1" style={{ gridTemplateColumns: `repeat(${Math.max((riskQuery.data?.metrics ?? []).length, 1)}, minmax(0, 1fr))` }}>
                {(riskQuery.data?.metrics ?? []).flatMap((rowMetric) =>
                  (riskQuery.data?.metrics ?? []).map((columnMetric) => {
                    const value = riskQuery.data?.correlationMatrix?.[rowMetric.ticker]?.[columnMetric.ticker] ?? 0;
                    const background =
                      value > 0.75 ? "bg-danger/50" : value > 0.5 ? "bg-warning/40" : value > 0.25 ? "bg-primary/20" : "bg-success/20";
                    return (
                      <div
                        key={`${rowMetric.ticker}-${columnMetric.ticker}`}
                        className={`flex h-8 items-center justify-center rounded text-[10px] font-mono text-foreground ${background}`}
                        title={`${rowMetric.ticker} vs ${columnMetric.ticker}: ${value.toFixed(2)}`}
                      >
                        {value.toFixed(2)}
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-background/50 p-3">
            <div className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Risk Gate Log</div>
            <div className="space-y-2">
              {(riskGateLogQuery.data ?? []).slice(0, 20).map((row) => (
                <div key={row.id} className="rounded-md bg-danger/10 px-3 py-2 text-xs text-danger">
                  <span className="font-mono">{row.ticker}</span> · {(row.hardBlocks ?? []).join(", ") || "No hard blocks recorded"}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
