import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronUp, FlaskConical, Sigma, Target } from "lucide-react";
import { toast } from "@/components/ui/sonner";
import { getSignalScores, getSignalsForTicker } from "@/services/signalService";
import { estimateCosts, simulateSignalTrade } from "@/services/traderGatewayService";
import { ListSkeleton } from "@/components/LoadingSkeletons";
import type { SignalScore } from "@/models";

function confidenceTone(band: SignalScore["confidenceBand"]) {
  if (band === "High") return "bg-success/10 text-success";
  if (band === "Moderate") return "bg-warning/10 text-warning";
  return "bg-danger/10 text-danger";
}

function SignalCostEstimate({ ticker }: { ticker: string }) {
  const costQuery = useQuery({
    queryKey: ["gateway", "cost-estimate", ticker],
    queryFn: () => estimateCosts(ticker, 100),
  });

  if (costQuery.isLoading) {
    return <p className="text-[11px] text-muted-foreground">Estimating transaction costs…</p>;
  }

  if (!costQuery.data) {
    return <p className="text-[11px] text-muted-foreground">Cost estimate unavailable.</p>;
  }

  return (
    <div className="grid grid-cols-2 gap-2 rounded-md border border-border bg-background/50 p-2 text-[11px] text-muted-foreground">
      <div>Spread: <span className="font-mono text-foreground">${costQuery.data.spreadCost.toFixed(2)}</span></div>
      <div>Slippage: <span className="font-mono text-foreground">${costQuery.data.slippageCost.toFixed(2)}</span></div>
      <div>Fees: <span className="font-mono text-foreground">${costQuery.data.fees.toFixed(2)}</span></div>
      <div>Total: <span className="font-mono text-foreground">{(costQuery.data.totalCostPct * 100).toFixed(2)}%</span></div>
    </div>
  );
}

export function SignalReviewPanel({
  ticker,
  onSimulationQueued,
}: {
  ticker?: string | null;
  onSimulationQueued?: () => void;
}) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [capitalAllocation, setCapitalAllocation] = useState(1000);

  const signalsQuery = useQuery({
    queryKey: ["signals", "review", ticker ?? "all"],
    queryFn: () => (ticker ? getSignalsForTicker(ticker) : getSignalScores()),
  });

  const simulateMutation = useMutation({
    mutationFn: ({ signalKey, capital }: { signalKey: string; capital: number }) =>
      simulateSignalTrade(signalKey, capital),
    onSuccess: (result) => {
      toast.success("Signal sent to simulation", {
        description: `${result.ticker} queued with ${result.shares?.toFixed(2) ?? "0"} shares.`,
      });
      onSimulationQueued?.();
    },
    onError: (error) => {
      toast.error("Simulation failed", {
        description: error instanceof Error ? error.message : "Unable to simulate the selected signal.",
      });
    },
  });

  const rows = (signalsQuery.data ?? []).slice(0, ticker ? 8 : 12);

  return (
    <div className="terminal-card p-4">
      <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-2">
          <Sigma className="h-4 w-4 text-primary" />
          <div>
            <h3 className="text-sm font-semibold text-foreground">Signal Review</h3>
            <p className="text-xs text-muted-foreground">
              {ticker ? `Reviewing scored signals touching ${ticker}.` : "Reviewing highest-ranked research signals."}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-muted-foreground">Capital</label>
          <input
            type="number"
            min={100}
            step={100}
            value={capitalAllocation}
            onChange={(event) => setCapitalAllocation(Number(event.target.value) || 0)}
            className="h-8 w-28 rounded-md border border-border bg-muted/40 px-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          />
        </div>
      </div>

      {signalsQuery.isLoading ? (
        <ListSkeleton count={4} />
      ) : rows.length === 0 ? (
        <p className="text-xs text-muted-foreground">No live signal rows are available for review.</p>
      ) : (
        <div className="space-y-3">
          {rows.map((signal) => {
            const expanded = expandedId === signal.id;
            const signalKey = signal.signalKey || signal.id;
            return (
              <div key={signal.id} className="rounded-lg border border-border bg-muted/20">
                <div className="flex flex-col gap-3 p-3 lg:flex-row lg:items-center lg:justify-between">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-xs font-bold text-primary">{signal.targetTicker}</span>
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-[0.12em] ${confidenceTone(signal.confidenceBand)}`}>
                        {signal.confidenceBand}
                      </span>
                      <span className="text-xs text-muted-foreground">{signal.eventCategory}</span>
                      <span className="text-xs text-muted-foreground">{signal.horizon}</span>
                    </div>
                    <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-muted-foreground sm:grid-cols-4">
                      <div>Score <span className="font-mono text-foreground">{signal.score.toFixed(1)}</span></div>
                      <div>Avg <span className={`font-mono ${signal.avgReturn >= 0 ? "text-success" : "text-danger"}`}>{signal.avgReturn.toFixed(2)}%</span></div>
                      <div>Win <span className="font-mono text-foreground">{signal.winRate.toFixed(1)}%</span></div>
                      <div>n <span className="font-mono text-foreground">{signal.sampleSize}</span></div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setExpandedId(expanded ? null : signal.id)}
                      className="inline-flex items-center gap-1 rounded-md border border-border px-3 py-2 text-xs text-muted-foreground hover:bg-muted/40 hover:text-foreground"
                    >
                      {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                      Details
                    </button>
                    <button
                      type="button"
                      onClick={() => simulateMutation.mutate({ signalKey, capital: capitalAllocation })}
                      disabled={simulateMutation.isPending || capitalAllocation <= 0}
                      className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-2 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      <FlaskConical className="h-3.5 w-3.5" />
                      Approve for Simulation
                    </button>
                  </div>
                </div>

                {expanded ? (
                  <div className="border-t border-border px-3 py-3">
                    <div className="mb-2 flex items-center gap-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
                      <Target className="h-3.5 w-3.5" />
                      Evidence Summary
                    </div>
                    <p className="mb-3 text-xs text-foreground">{signal.evidenceSummary}</p>
                    <div className="mb-3">
                      <div className="mb-1 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Estimated Costs</div>
                      <SignalCostEstimate ticker={signal.targetTicker} />
                    </div>
                    <div>
                      <div className="mb-1 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Rationale</div>
                      <pre className="max-h-48 overflow-auto rounded-md border border-border bg-background/50 p-3 text-[11px] leading-relaxed text-muted-foreground">
                        {JSON.stringify(signal.rationale || signal.metadata || {}, null, 2)}
                      </pre>
                    </div>
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
