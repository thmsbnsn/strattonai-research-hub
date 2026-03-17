import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AlertTriangle, Bot, DollarSign } from "lucide-react";
import { toast } from "@/components/ui/sonner";
import { getPaperTrades } from "@/services/tradeService";
import {
  getAlpacaAccount,
  getAlpacaOrders,
  getAlpacaPositions,
  getPennyStockCandidates,
  getTradingLoopHistory,
  getTradingLoopStatus,
  runTradingLoop,
} from "@/services/traderGatewayService";
import type { TradingSettings } from "@/types";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

export function PennyStockPanel({ tradingSettings }: { tradingSettings: TradingSettings }) {
  const [loopMode, setLoopMode] = useState<"paper" | "live">(tradingSettings.alpacaMode);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const accountQuery = useQuery({ queryKey: ["gateway", "alpaca-account"], queryFn: getAlpacaAccount, retry: 0, refetchInterval: 30000 });
  const positionsQuery = useQuery({ queryKey: ["gateway", "alpaca-positions"], queryFn: getAlpacaPositions, retry: 0, refetchInterval: 30000 });
  const ordersQuery = useQuery({ queryKey: ["gateway", "alpaca-orders"], queryFn: () => getAlpacaOrders("all"), retry: 0 });
  const loopHistoryQuery = useQuery({ queryKey: ["gateway", "loop-history"], queryFn: getTradingLoopHistory, retry: 0 });
  const loopStatusQuery = useQuery({
    queryKey: ["gateway", "loop-status", currentJobId ?? "none"],
    queryFn: () => getTradingLoopStatus(currentJobId || ""),
    enabled: Boolean(currentJobId),
    refetchInterval: (query) => (query.state.data?.status === "running" ? 2000 : false),
  });
  const candidatesQuery = useQuery({
    queryKey: ["gateway", "penny-candidates", tradingSettings.startingCapital],
    queryFn: () => getPennyStockCandidates(tradingSettings.startingCapital, 10),
    enabled: tradingSettings.pennyStockUniverseEnabled,
  });
  const tradesQuery = useQuery({ queryKey: ["trades", "penny"], queryFn: getPaperTrades });

  const runLoopMutation = useMutation({
    mutationFn: (dryRun: boolean) =>
      runTradingLoop({
        capital: tradingSettings.startingCapital,
        universe: "penny",
        mode: loopMode,
        dryRun,
      }),
    onSuccess: (result) => {
      setCurrentJobId(result.job_id);
      toast.success("Trading loop started", {
        description: `Job ${result.job_id} started in ${result.dry_run ? "dry-run" : "execution"} mode.`,
      });
      tradesQuery.refetch();
      positionsQuery.refetch();
      accountQuery.refetch();
      loopHistoryQuery.refetch();
    },
    onError: (error) => {
      toast.error("Trading loop failed", {
        description: error instanceof Error ? error.message : "Unable to run the penny-stock loop.",
      });
    },
  });

  const pennyTrades = useMemo(
    () => (tradesQuery.data ?? []).filter((trade) => trade.universe === "penny"),
    [tradesQuery.data]
  );
  const pnlTotal = pennyTrades.reduce((sum, trade) => {
    const realized = trade.realizedPnl ?? 0;
    const unrealized =
      trade.realizedPnl === undefined
        ? (trade.direction === "Long" ? trade.currentPrice - trade.entryPrice : trade.entryPrice - trade.currentPrice) * trade.quantity
        : 0;
    return sum + realized + unrealized;
  }, 0);
  const liveEnabled = tradingSettings.alpacaMode === "live" && tradingSettings.liveTradingConfirmed;
  const latestLoopSummary = loopStatusQuery.data?.result && typeof loopStatusQuery.data.result === "object" ? (loopStatusQuery.data.result as Record<string, unknown>).summary as Record<string, unknown> | undefined : undefined;

  return (
    <div className="terminal-card p-4">
      <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Bot className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-semibold text-foreground">Penny Stock Sandbox</h3>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            Alpaca-backed penny-stock practice loop. Live execution stays locked until explicitly confirmed in Settings.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setLoopMode("paper")}
            className={`rounded-md px-3 py-2 text-xs font-medium ${loopMode === "paper" ? "bg-primary text-primary-foreground" : "bg-muted/40 text-muted-foreground"}`}
          >
            Paper Mode
          </button>
          <button
            onClick={() => liveEnabled && setLoopMode("live")}
            disabled={!liveEnabled}
            className={`rounded-md px-3 py-2 text-xs font-medium ${loopMode === "live" ? "bg-danger text-white" : "bg-muted/40 text-muted-foreground"} disabled:cursor-not-allowed disabled:opacity-40`}
          >
            Live Mode
          </button>
        </div>
      </div>

      {!liveEnabled ? (
        <div className="mb-4 flex items-start gap-2 rounded-md border border-warning/20 bg-warning/10 px-3 py-2 text-xs text-warning">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>Live mode is disabled until Alpaca live trading is explicitly confirmed in Settings.</span>
        </div>
      ) : null}

      <div className="mb-4 grid gap-3 md:grid-cols-3">
        <div className="rounded-lg bg-muted/30 p-3">
          <div className="mb-1 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Portfolio Value</div>
          <div className="font-mono text-lg font-semibold text-foreground">${Number(accountQuery.data?.portfolio_value || 0).toFixed(2)}</div>
        </div>
        <div className="rounded-lg bg-muted/30 p-3">
          <div className="mb-1 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Buying Power</div>
          <div className="font-mono text-lg font-semibold text-foreground">${Number(accountQuery.data?.buying_power || 0).toFixed(2)}</div>
        </div>
        <div className="rounded-lg bg-muted/30 p-3">
          <div className="mb-1 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Cash / Mode</div>
          <div className="font-mono text-lg font-semibold text-foreground">${Number(accountQuery.data?.cash || 0).toFixed(2)}</div>
          <div className={`mt-1 inline-flex rounded-full px-2 py-0.5 text-[10px] uppercase ${accountQuery.data?.mode === "live" ? "bg-danger/10 text-danger" : "bg-primary/10 text-primary"}`}>
            {accountQuery.data?.mode || "paper"}
          </div>
        </div>
        <div className="rounded-lg bg-muted/30 p-3 md:col-span-3">
          <div className="mb-1 flex items-center gap-1 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
            <DollarSign className="h-3 w-3" />
            Penny P&amp;L
          </div>
          <div className={`font-mono text-lg font-semibold ${pnlTotal >= 0 ? "text-success" : "text-danger"}`}>
            {pnlTotal >= 0 ? "+" : "-"}${Math.abs(pnlTotal).toFixed(2)}
          </div>
        </div>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        <button
          onClick={() => runLoopMutation.mutate(true)}
          disabled={runLoopMutation.isPending || !tradingSettings.pennyStockUniverseEnabled}
          className="rounded-md border border-primary/30 bg-primary/10 px-3 py-2 text-xs font-medium text-primary hover:bg-primary/15 disabled:cursor-not-allowed disabled:opacity-60"
        >
          Run Loop (Dry Run)
        </button>
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <button
              disabled={runLoopMutation.isPending || !tradingSettings.pennyStockUniverseEnabled || (loopMode === "live" && !liveEnabled)}
              className="rounded-md bg-primary px-3 py-2 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60"
            >
              Execute Loop
            </button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Execute penny-stock loop?</AlertDialogTitle>
              <AlertDialogDescription>
                This will process current candidates in {loopMode} mode using your current StrattonAI trading settings.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={() => runLoopMutation.mutate(false)}>Confirm</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.35fr_0.9fr]">
        <div className="overflow-x-auto">
          <table className="w-full data-grid text-xs">
            <thead>
              <tr className="border-b border-border">
                <th className="px-3 py-2 text-left text-muted-foreground">Ticker</th>
                <th className="px-3 py-2 text-right text-muted-foreground">Price</th>
                <th className="px-3 py-2 text-right text-muted-foreground">Score</th>
                <th className="px-3 py-2 text-right text-muted-foreground">Conf</th>
                <th className="px-3 py-2 text-right text-muted-foreground">Qty</th>
                <th className="px-3 py-2 text-right text-muted-foreground">Est. Cost</th>
                <th className="px-3 py-2 text-right text-muted-foreground">Cost %</th>
                <th className="px-3 py-2 text-right text-muted-foreground">Vol Filter</th>
              </tr>
            </thead>
            <tbody>
              {(candidatesQuery.data ?? []).map((candidate) => (
                <tr key={candidate.ticker} className="border-b border-border/50 hover:bg-muted/20">
                  <td className="px-3 py-2 font-mono text-primary">{candidate.ticker}</td>
                  <td className="px-3 py-2 text-right font-mono text-foreground">${candidate.entryPrice.toFixed(2)}</td>
                  <td className="px-3 py-2 text-right font-mono text-foreground">{candidate.score.toFixed(1)}</td>
                  <td className="px-3 py-2 text-right font-mono text-foreground">{candidate.confidenceBand}</td>
                  <td className="px-3 py-2 text-right font-mono text-foreground">{candidate.suggestedQty.toFixed(0)}</td>
                  <td className="px-3 py-2 text-right font-mono text-foreground">${candidate.estimatedCost.toFixed(2)}</td>
                  <td className="px-3 py-2 text-right font-mono text-muted-foreground">{(candidate.estimatedCostPct * 100).toFixed(2)}%</td>
                  <td className="px-3 py-2 text-right text-success">Pass</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="space-y-3">
          <div className="rounded-lg border border-border bg-background/50 p-3">
            <div className="mb-2 flex items-center gap-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
              <DollarSign className="h-3.5 w-3.5" />
              Open Positions
            </div>
            {(positionsQuery.data ?? []).length === 0 ? (
              <p className="text-xs text-muted-foreground">No Alpaca positions are open.</p>
            ) : (
              <div className="space-y-2">
                {positionsQuery.data?.map((position) => (
                  <div key={position.ticker} className="rounded-md bg-muted/30 px-3 py-2 text-xs">
                    <div className="font-mono text-primary">{position.ticker}</div>
                    <div className="text-muted-foreground">
                      Qty {String(position.qty)} · Avg ${Number(position.avg_entry_price || 0).toFixed(2)} · Px ${Number(position.current_price || 0).toFixed(2)} · UPL ${Number(position.unrealized_pl || 0).toFixed(2)} ({(Number(position.unrealized_plpc || 0) * 100).toFixed(2)}%)
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="rounded-lg border border-border bg-background/50 p-3">
            <div className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Recent Loop Runs</div>
            {(loopHistoryQuery.data ?? []).length === 0 ? (
              <p className="text-xs text-muted-foreground">No loop runs recorded yet.</p>
            ) : (
              <div className="space-y-2">
                {(loopHistoryQuery.data ?? []).slice(0, 5).map((run) => (
                  <div key={`${run.job_id}-${run.timestamp}`} className="rounded-md bg-muted/30 px-3 py-2 text-xs text-foreground">
                    <div className="font-mono text-primary">{run.timestamp}</div>
                    <div className="text-muted-foreground">
                      eval {run.candidates_evaluated} · approved {run.orders_approved} · submitted {run.orders_submitted} · pnl ${run.realized_pnl_this_run.toFixed(2)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="rounded-lg border border-border bg-background/50 p-3">
            <div className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Recent Penny Trades</div>
            {pennyTrades.length === 0 ? (
              <p className="text-xs text-muted-foreground">No penny-universe trades recorded yet.</p>
            ) : (
              <div className="space-y-2">
                {pennyTrades.slice(0, 5).map((trade) => (
                  <div key={trade.id} className="rounded-md bg-muted/30 px-3 py-2 text-xs">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono text-primary">{trade.ticker}</span>
                      <span className="text-muted-foreground">{trade.status}</span>
                    </div>
                    <div className="text-muted-foreground">
                      {trade.direction} · qty {trade.quantity.toFixed(0)} · ${trade.entryPrice.toFixed(2)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="rounded-lg border border-border bg-background/50 p-3">
            <div className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Order History</div>
            {(ordersQuery.data ?? []).length === 0 ? (
              <p className="text-xs text-muted-foreground">No Alpaca orders found.</p>
            ) : (
              <div className="space-y-2">
                {(ordersQuery.data ?? []).slice(0, 5).map((order) => (
                  <div key={String(order.order_id)} className="rounded-md bg-muted/30 px-3 py-2 text-xs text-foreground">
                    <div className="font-mono text-primary">{String(order.ticker)}</div>
                    <div className="text-muted-foreground">
                      {String(order.side)} {String(order.qty)} · {String(order.order_type)} · {String(order.status)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {currentJobId ? (
        <div className="mt-4 rounded-lg border border-border bg-background/50 p-3 text-xs text-muted-foreground">
          <div className="font-mono text-primary">Loop Job {currentJobId}</div>
          <div>Status: {loopStatusQuery.data?.status ?? "running"}</div>
          {latestLoopSummary ? (
            <div className="mt-1">
              evaluated {String(latestLoopSummary.candidates_evaluated)} · approved {String(latestLoopSummary.orders_approved)} · submitted {String(latestLoopSummary.orders_submitted)}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
