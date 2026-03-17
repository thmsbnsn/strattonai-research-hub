import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AppLayout } from "@/components/AppLayout";
import { StatCard } from "@/components/StatCard";
import { ChartCard } from "@/components/ChartCard";
import { CardSkeleton, ChartSkeleton, TableSkeleton } from "@/components/LoadingSkeletons";
import { ErrorState } from "@/components/StateDisplays";
import { getPaperTrades, getPortfolioPerformance } from "@/services/tradeService";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";

export default function PaperTrades() {
  const [groupByRun, setGroupByRun] = useState(false);
  const trades = useQuery({ queryKey: ["trades"], queryFn: getPaperTrades });
  const performance = useQuery({ queryKey: ["trades", "performance"], queryFn: getPortfolioPerformance });

  const openTrades = trades.data?.filter((t) => t.status === "Open" || t.status === "Simulated") ?? [];
  const closedTrades = trades.data?.filter((t) => t.status === "Closed") ?? [];
  const blockedTrades = trades.data?.filter((t) => t.status === "Risk-Blocked") ?? [];
  const totalPnl = openTrades.reduce((sum, t) => {
    if (typeof t.realizedPnl === "number") {
      return sum + t.realizedPnl;
    }
    const pnl = t.direction === "Long"
      ? (t.currentPrice - t.entryPrice) * t.quantity
      : (t.entryPrice - t.currentPrice) * t.quantity;
    return sum + pnl;
  }, 0);
  const winRate = closedTrades.length
    ? (closedTrades.filter((trade) => (trade.realizedPnl ?? 0) > 0).length / closedTrades.length) * 100
    : 0;
  const selectedRun = new URLSearchParams(window.location.search).get("run");
  const filteredTrades = useMemo(
    () =>
      (trades.data ?? []).filter((trade) =>
        selectedRun ? String((trade.metadata as Record<string, unknown> | undefined)?.run_id ?? (trade.metadata as Record<string, unknown> | undefined)?.runId ?? "") === selectedRun : true
      ),
    [selectedRun, trades.data]
  );
  const groupedRuns = useMemo(() => {
    const groups = new Map<string, typeof filteredTrades>();
    filteredTrades.forEach((trade) => {
      const runId = String((trade.metadata as Record<string, unknown> | undefined)?.run_id ?? (trade.metadata as Record<string, unknown> | undefined)?.runId ?? "");
      if (!runId) return;
      groups.set(runId, [...(groups.get(runId) ?? []), trade]);
    });
    return Array.from(groups.entries());
  }, [filteredTrades]);

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Paper Trade Tracker</h1>
          <p className="text-sm text-muted-foreground mt-1">Simulated trades from research signals — no real execution</p>
        </div>

        {/* Summary */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {trades.isLoading ? (
            <><CardSkeleton /><CardSkeleton /><CardSkeleton /><CardSkeleton /></>
          ) : trades.isError ? (
            <div className="col-span-4"><ErrorState onRetry={() => trades.refetch()} /></div>
          ) : (
            <>
              <StatCard label="Open Trades" value={String(openTrades.length)} />
              <StatCard label="Total P&L" value={`${totalPnl >= 0 ? "+" : ""}$${totalPnl.toFixed(0)}`} color={totalPnl >= 0 ? "text-success" : "text-danger"} />
              <StatCard label="Win Rate" value={`${winRate.toFixed(0)}%`} />
              <StatCard label="Closed Trades" value={String(closedTrades.length)} />
            </>
          )}
        </div>

        {blockedTrades.length > 0 ? (
          <div className="rounded-lg border border-warning/20 bg-warning/10 px-4 py-3 text-xs text-warning">
            {blockedTrades.length} trade{blockedTrades.length === 1 ? "" : "s"} were blocked by the deterministic risk engine and remain in the log for auditability.
          </div>
        ) : null}

        <div className="flex items-center justify-between gap-3 rounded-lg border border-border bg-muted/20 px-4 py-3 text-xs text-muted-foreground">
          <span>{selectedRun ? `Filtered to run ${selectedRun}` : "Toggle grouped view to inspect portfolio-construction runs."}</span>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={groupByRun} onChange={(event) => setGroupByRun(event.target.checked)} />
            Group by Run
          </label>
        </div>

        {/* Performance Chart */}
        {performance.isLoading ? (
          <ChartSkeleton />
        ) : (
          <ChartCard title="Portfolio Performance (30 Days)" height="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={performance.data}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(222 30% 16%)" />
                <XAxis dataKey="day" tick={{ fill: "hsl(215 20% 55%)", fontSize: 10 }} axisLine={{ stroke: "hsl(222 30% 16%)" }} />
                <YAxis tick={{ fill: "hsl(215 20% 55%)", fontSize: 10 }} axisLine={{ stroke: "hsl(222 30% 16%)" }} tickFormatter={(v) => `$${v}`} />
                <Tooltip contentStyle={{ backgroundColor: "hsl(222 44% 8%)", border: "1px solid hsl(222 30% 16%)", borderRadius: "8px", fontSize: "12px", color: "hsl(210 40% 92%)" }} formatter={(v: number) => [`$${v.toFixed(0)}`, "P&L"]} />
                <Line type="monotone" dataKey="pnl" stroke="hsl(210 100% 56%)" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>
        )}

        {/* Trades Table */}
        {trades.isLoading ? (
          <TableSkeleton rows={4} cols={7} />
        ) : (
          <div className="terminal-card p-5">
            <h3 className="text-sm font-semibold text-foreground mb-4">Trade Log</h3>
            <div className="overflow-x-auto">
              <table className="w-full data-grid">
                <thead>
                  <tr className="border-b border-border">
                    {["Ticker", "Direction", "Signal", "Entry", "Current", "P&L", "Status", "Mode"].map((h) => (
                      <th key={h} className="text-left py-2 px-3 text-xs text-muted-foreground font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(groupByRun ? [] : filteredTrades).map((t) => {
                    const pnl = typeof t.realizedPnl === "number"
                      ? t.realizedPnl
                      : t.direction === "Long"
                        ? (t.currentPrice - t.entryPrice) * t.quantity
                        : (t.entryPrice - t.currentPrice) * t.quantity;
                    const pnlPercent = t.direction === "Long"
                      ? ((t.currentPrice - t.entryPrice) / t.entryPrice) * 100
                      : ((t.entryPrice - t.currentPrice) / t.entryPrice) * 100;
                    return (
                      <tr key={t.id} className="border-b border-border/50 hover:bg-muted/20">
                        <td className="py-2.5 px-3 font-semibold text-primary">{t.ticker}</td>
                        <td className="py-2.5 px-3">
                          <span className={`text-xs px-2 py-0.5 rounded-full ${t.direction === "Long" ? "bg-success/10 text-success" : "bg-danger/10 text-danger"}`}>
                            {t.direction}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-muted-foreground text-xs max-w-[200px] truncate">{t.signal}</td>
                        <td className="py-2.5 px-3 text-foreground">${t.entryPrice.toFixed(2)}</td>
                        <td className="py-2.5 px-3 text-foreground">${t.currentPrice.toFixed(2)}</td>
                        <td className={`py-2.5 px-3 ${pnl >= 0 ? "text-success" : "text-danger"}`}>
                          <div className="flex items-center gap-1">
                            {pnl >= 0 ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                            ${Math.abs(pnl).toFixed(0)} ({pnlPercent >= 0 ? "+" : ""}{pnlPercent.toFixed(1)}%)
                          </div>
                        </td>
                        <td className="py-2.5 px-3">
                          <span className={`text-xs px-2 py-0.5 rounded-full ${
                            t.status === "Open" || t.status === "Simulated"
                              ? "bg-primary/10 text-primary"
                              : t.status === "Risk-Blocked"
                                ? "bg-warning/10 text-warning"
                                : "bg-muted text-muted-foreground"
                          }`}>
                            {t.status}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-xs text-muted-foreground uppercase">{t.mode || "simulated"}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {groupByRun ? (
              <div className="mt-4 space-y-3">
                {groupedRuns.length === 0 ? (
                  <p className="text-xs text-muted-foreground">No run metadata found for the current trade set.</p>
                ) : (
                  groupedRuns.map(([runId, runTrades]) => {
                    const totalCost = runTrades.reduce((sum, trade) => sum + trade.entryPrice * trade.quantity, 0);
                    const totalUnrealized = runTrades.reduce((sum, trade) => sum + (trade.realizedPnl ?? 0), 0);
                    const first = runTrades[0];
                    const metadata = (first.metadata as Record<string, unknown> | undefined) ?? {};
                    return (
                      <div key={runId} className="rounded-lg border border-border bg-muted/20 p-4">
                        <div className="mb-2 flex items-center justify-between gap-3">
                          <div>
                            <div className="font-mono text-sm text-primary">{runId}</div>
                            <div className="text-xs text-muted-foreground">
                              method {String(metadata.method ?? "unknown")} · regime {String(metadata.regime ?? metadata.loop_mode ?? "n/a")}
                            </div>
                          </div>
                          <div className="text-right text-xs text-muted-foreground">
                            <div>Total cost ${totalCost.toFixed(2)}</div>
                            <div>Total unrealized ${totalUnrealized.toFixed(2)}</div>
                          </div>
                        </div>
                        <div className="space-y-2">
                          {runTrades.map((trade) => (
                            <div key={trade.id} className="rounded-md bg-background/50 px-3 py-2 text-xs text-foreground">
                              <span className="font-mono text-primary">{trade.ticker}</span> · {trade.direction} · qty {trade.quantity.toFixed(4)} · {trade.status}
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            ) : null}
          </div>
        )}
      </div>
    </AppLayout>
  );
}
