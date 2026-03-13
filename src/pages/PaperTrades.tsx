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
  const trades = useQuery({ queryKey: ["trades"], queryFn: getPaperTrades });
  const performance = useQuery({ queryKey: ["trades", "performance"], queryFn: getPortfolioPerformance });

  const openTrades = trades.data?.filter((t) => t.status === "Open") ?? [];
  const closedTrades = trades.data?.filter((t) => t.status === "Closed") ?? [];
  const totalPnl = openTrades.reduce((sum, t) => {
    const pnl = t.direction === "Long"
      ? (t.currentPrice - t.entryPrice) * t.quantity
      : (t.entryPrice - t.currentPrice) * t.quantity;
    return sum + pnl;
  }, 0);

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
              <StatCard label="Win Rate" value="67%" />
              <StatCard label="Closed Trades" value={String(closedTrades.length)} />
            </>
          )}
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
                    {["Ticker", "Direction", "Signal", "Entry", "Current", "P&L", "Status"].map((h) => (
                      <th key={h} className="text-left py-2 px-3 text-xs text-muted-foreground font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {trades.data?.map((t) => {
                    const pnl = t.direction === "Long"
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
                          <span className={`text-xs px-2 py-0.5 rounded-full ${t.status === "Open" ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"}`}>
                            {t.status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
