import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { BarChart, Bar, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Boxes, FlaskConical } from "lucide-react";
import { toast } from "@/components/ui/sonner";
import { getSignalScores, getSignalsForTicker } from "@/services/signalService";
import { constructPortfolio, constructPortfolioWithSimulation } from "@/services/traderGatewayService";
import { ListSkeleton } from "@/components/LoadingSkeletons";
import type { AllocationSimulationResult, PortfolioAllocation } from "@/models";

const METHODS = [
  { key: "mean-variance", label: "Mean-Variance" },
  { key: "kelly", label: "Kelly" },
  { key: "risk-parity", label: "Risk Parity" },
] as const;

export function PortfolioConstructorPanel({
  ticker,
  onAllocationsChange,
}: {
  ticker?: string | null;
  onAllocationsChange?: (allocations: PortfolioAllocation[]) => void;
}) {
  const [method, setMethod] = useState<(typeof METHODS)[number]["key"]>("mean-variance");
  const [capital, setCapital] = useState(1000);
  const [simulateTrades, setSimulateTrades] = useState(true);
  const [simulationDryRun, setSimulationDryRun] = useState(true);

  const signalsQuery = useQuery({
    queryKey: ["signals", "constructor", ticker ?? "all"],
    queryFn: () => (ticker ? getSignalsForTicker(ticker) : getSignalScores()),
  });

  const signalKeys = useMemo(
    () => (signalsQuery.data ?? []).slice(0, 8).map((signal) => signal.signalKey || signal.id),
    [signalsQuery.data]
  );

  const constructMutation = useMutation({
    mutationFn: () => constructPortfolio(method, capital, signalKeys),
    onSuccess: (result) => {
      onAllocationsChange?.(result.allocations);
      toast.success("Portfolio constructed", {
        description: `${result.allocations.length} allocations generated via ${result.method}.`,
      });
    },
    onError: (error) => {
      toast.error("Portfolio construction failed", {
        description: error instanceof Error ? error.message : "Unable to construct portfolio.",
      });
    },
  });

  const simulateAllMutation = useMutation<AllocationSimulationResult>({
    mutationFn: async () =>
      constructPortfolioWithSimulation(
        method,
        capital,
        (constructMutation.data?.allocations ?? []).map((allocation) => allocation.signalKey).filter(Boolean) as string[],
        simulationDryRun
      ),
    onSuccess: (result) => {
      toast.success("Portfolio simulation complete", {
        description: `${result.simulated.length} simulated · ${result.riskBlocked.length} blocked`,
      });
    },
    onError: (error) => {
      toast.error("Simulation dispatch failed", {
        description: error instanceof Error ? error.message : "Unable to simulate the portfolio.",
      });
    },
  });

  useEffect(() => {
    onAllocationsChange?.(constructMutation.data?.allocations ?? []);
  }, [constructMutation.data, onAllocationsChange]);

  const chartData = (constructMutation.data?.allocations ?? []).map((allocation) => ({
    ticker: allocation.ticker,
    weight: allocation.weight * 100,
  }));

  return (
    <div className="terminal-card p-4">
      <div className="mb-4 flex items-center gap-2">
        <Boxes className="h-4 w-4 text-primary" />
        <div>
          <h3 className="text-sm font-semibold text-foreground">Portfolio Constructor</h3>
          <p className="text-xs text-muted-foreground">Build deterministic allocations from the current signal set.</p>
        </div>
      </div>

      <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap gap-2">
          {METHODS.map((option) => (
            <button
              key={option.key}
              onClick={() => setMethod(option.key)}
              className={`rounded-md px-3 py-2 text-xs font-medium transition-colors ${
                method === option.key ? "bg-primary text-primary-foreground" : "bg-muted/40 text-muted-foreground hover:bg-muted"
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-muted-foreground">Capital</label>
          <input
            type="number"
            min={100}
            step={100}
            value={capital}
            onChange={(event) => setCapital(Number(event.target.value) || 0)}
            className="h-8 w-28 rounded-md border border-border bg-muted/40 px-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          />
          <button
            onClick={() => constructMutation.mutate()}
            disabled={constructMutation.isPending || signalKeys.length === 0 || capital <= 0}
            className="rounded-md bg-primary px-3 py-2 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Construct
          </button>
        </div>
      </div>

      {signalsQuery.isLoading ? (
        <ListSkeleton count={3} />
      ) : constructMutation.data?.allocations?.length ? (
        <div className="space-y-4">
          <div className="h-56 rounded-lg border border-border bg-background/50 p-3">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(222 30% 16%)" />
                <XAxis dataKey="ticker" tick={{ fill: "hsl(215 20% 55%)", fontSize: 10 }} axisLine={{ stroke: "hsl(222 30% 16%)" }} />
                <YAxis tick={{ fill: "hsl(215 20% 55%)", fontSize: 10 }} axisLine={{ stroke: "hsl(222 30% 16%)" }} tickFormatter={(value) => `${value.toFixed(0)}%`} />
                <Tooltip
                  contentStyle={{ backgroundColor: "hsl(222 44% 8%)", border: "1px solid hsl(222 30% 16%)", borderRadius: "8px", fontSize: "12px", color: "hsl(210 40% 92%)" }}
                  formatter={(value: number) => [`${value.toFixed(2)}%`, "Weight"]}
                />
                <Bar dataKey="weight" fill="hsl(210 100% 56%)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full data-grid text-xs">
              <thead>
                <tr className="border-b border-border">
                  <th className="px-3 py-2 text-left text-muted-foreground">Ticker</th>
                  <th className="px-3 py-2 text-right text-muted-foreground">Allocation $</th>
                  <th className="px-3 py-2 text-right text-muted-foreground">Weight %</th>
                  <th className="px-3 py-2 text-right text-muted-foreground">Method</th>
                </tr>
              </thead>
              <tbody>
                {constructMutation.data.allocations.map((allocation) => (
                  <tr key={`${allocation.ticker}-${allocation.method}`} className="border-b border-border/50 hover:bg-muted/20">
                    <td className="px-3 py-2 font-mono text-primary">{allocation.ticker}</td>
                    <td className="px-3 py-2 text-right font-mono text-foreground">${allocation.allocationDollars.toFixed(2)}</td>
                    <td className="px-3 py-2 text-right font-mono text-foreground">{(allocation.weight * 100).toFixed(2)}%</td>
                    <td className="px-3 py-2 text-right text-muted-foreground">{allocation.method}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <label className="flex items-center gap-2 text-xs text-muted-foreground">
              <input type="checkbox" checked={simulateTrades} onChange={(event) => setSimulateTrades(event.target.checked)} />
              Simulate Trades
            </label>
            <label className="flex items-center gap-2 text-xs text-muted-foreground">
              <input type="checkbox" checked={simulationDryRun} onChange={(event) => setSimulationDryRun(event.target.checked)} />
              Dry Run
            </label>
            <button
              onClick={() => simulateAllMutation.mutate()}
              disabled={simulateAllMutation.isPending || !simulateTrades || !(constructMutation.data.allocations ?? []).some((allocation) => allocation.signalKey)}
              className="inline-flex items-center gap-2 rounded-md border border-primary/30 bg-primary/10 px-3 py-2 text-xs font-medium text-primary hover:bg-primary/15 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <FlaskConical className="h-3.5 w-3.5" />
              Send to Simulation
            </button>
            {simulateAllMutation.data?.simulated?.length ? (
              <a href={`/paper-trades?run=${encodeURIComponent(simulateAllMutation.data.runId || "")}`} className="text-xs text-primary hover:text-primary/80">
                View in Paper Trades
              </a>
            ) : null}
          </div>
          {simulateAllMutation.data ? (
            <div className="space-y-3 rounded-lg border border-border bg-background/50 p-3">
              <div className="text-xs text-muted-foreground">
                Simulated {simulateAllMutation.data.simulated.length} trades · Risk-blocked {simulateAllMutation.data.riskBlocked.length} tickers
              </div>
              {simulateAllMutation.data.riskWarnings.map((warning) => (
                <div key={warning} className="rounded-md border border-warning/20 bg-warning/10 px-3 py-2 text-xs text-warning">
                  {warning}
                </div>
              ))}
              {simulateAllMutation.data.simulated.length ? (
                <div className="space-y-2">
                  {simulateAllMutation.data.simulated.map((row) => (
                    <div key={`${row.ticker}-${row.signalKey}`} className="rounded-md bg-muted/30 px-3 py-2 text-xs text-foreground">
                      <span className="font-mono text-primary">{row.ticker}</span> · entry ${row.entryPrice.toFixed(2)} · qty {row.qty.toFixed(4)} · net ${row.netCost.toFixed(2)} · fees {(row.transactionCostPct * 100).toFixed(2)}%
                    </div>
                  ))}
                </div>
              ) : null}
              {simulateAllMutation.data.riskBlocked.length ? (
                <div className="space-y-2">
                  {simulateAllMutation.data.riskBlocked.map((row) => (
                    <div key={`${row.ticker}-${row.reason}`} className="rounded-md bg-danger/10 px-3 py-2 text-xs text-danger">
                      <span className="font-mono">{row.ticker}</span> · {row.reason}
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      ) : (
        <p className="text-xs text-muted-foreground">Construct a portfolio from the currently visible signal set to review deterministic weights.</p>
      )}
    </div>
  );
}
