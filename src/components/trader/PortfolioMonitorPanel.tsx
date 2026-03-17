import { useQuery } from "@tanstack/react-query";
import { Activity, BarChart3, ShieldAlert, TrendingUp } from "lucide-react";
import { getPortfolioMetrics } from "@/services/traderGatewayService";
import { ListSkeleton } from "@/components/LoadingSkeletons";

function sparklinePath(values: number[]) {
  if (values.length === 0) return "";
  const width = 240;
  const height = 56;
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

export function PortfolioMonitorPanel() {
  const metricsQuery = useQuery({
    queryKey: ["gateway", "portfolio-metrics"],
    queryFn: getPortfolioMetrics,
    refetchInterval: 15000,
  });

  const metrics = metricsQuery.data;
  const curve = metrics?.equityCurve ?? [];
  const path = sparklinePath(curve.map((point) => point.cumulativePnl));

  return (
    <div className="terminal-card p-4">
      <div className="mb-4 flex items-center gap-2">
        <Activity className="h-4 w-4 text-primary" />
        <div>
          <h3 className="text-sm font-semibold text-foreground">Portfolio Monitor</h3>
          <p className="text-xs text-muted-foreground">Live paper-trade health from the local gateway.</p>
        </div>
      </div>

      {metricsQuery.isLoading ? (
        <ListSkeleton count={2} />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
            <div className="rounded-lg bg-muted/30 p-3">
              <div className="mb-1 flex items-center gap-1 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
                <TrendingUp className="h-3 w-3" />
                Sharpe
              </div>
              <div className="font-mono text-lg font-semibold text-foreground">{(metrics?.sharpeRatio ?? 0).toFixed(2)}</div>
            </div>
            <div className="rounded-lg bg-muted/30 p-3">
              <div className="mb-1 flex items-center gap-1 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
                <BarChart3 className="h-3 w-3" />
                Sortino
              </div>
              <div className="font-mono text-lg font-semibold text-foreground">{(metrics?.sortinoRatio ?? 0).toFixed(2)}</div>
            </div>
            <div className="rounded-lg bg-muted/30 p-3">
              <div className="mb-1 flex items-center gap-1 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
                <ShieldAlert className="h-3 w-3" />
                Max DD
              </div>
              <div className="font-mono text-lg font-semibold text-danger">{((metrics?.maxDrawdown ?? 0) * 100).toFixed(2)}%</div>
            </div>
            <div className="rounded-lg bg-muted/30 p-3">
              <div className="mb-1 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Turnover</div>
              <div className="font-mono text-lg font-semibold text-foreground">{(metrics?.turnover ?? 0).toFixed(2)}x</div>
            </div>
          </div>

          <div className="mt-4 rounded-lg border border-border bg-background/50 p-3">
            <div className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Equity Curve</div>
            {curve.length === 0 ? (
              <p className="text-xs text-muted-foreground">No simulated or paper trades are available yet.</p>
            ) : (
              <svg viewBox="0 0 240 56" className="h-16 w-full">
                <path d={path} fill="none" stroke="hsl(var(--primary))" strokeWidth="2" />
              </svg>
            )}
          </div>
        </>
      )}
    </div>
  );
}
