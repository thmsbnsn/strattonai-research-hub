import { useQuery } from "@tanstack/react-query";
import { Activity } from "lucide-react";
import { AppLayout } from "@/components/AppLayout";
import { DataSourceStatusBadge } from "@/components/DataSourceStatusBadge";
import { MarketIndexCard } from "@/components/MarketIndexCard";
import { InsightCard } from "@/components/InsightCard";
import { CardSkeleton, ListSkeleton } from "@/components/LoadingSkeletons";
import { ErrorState, EmptyState } from "@/components/StateDisplays";
import { getMarketIndexes, getSectorPerformance, getVolatilityData } from "@/services/marketService";
import { getEvents } from "@/services/eventService";
import { getResearchInsights } from "@/services/researchService";
import { getSignalScores } from "@/services/signalService";

function SentimentBadge({ sentiment }: { sentiment: string }) {
  const colors: Record<string, string> = {
    positive: "bg-success/10 text-success",
    negative: "bg-danger/10 text-danger",
    neutral: "bg-muted text-muted-foreground",
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${colors[sentiment] ?? colors.neutral}`}>
      {sentiment}
    </span>
  );
}

function SignalConfidenceBadge({ band }: { band: "High" | "Moderate" | "Low" }) {
  const colors = {
    High: "bg-success/10 text-success",
    Moderate: "bg-warning/10 text-warning",
    Low: "bg-muted text-muted-foreground",
  } satisfies Record<"High" | "Moderate" | "Low", string>;

  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${colors[band]}`}>
      {band}
    </span>
  );
}

export default function Dashboard() {
  const indexes = useQuery({ queryKey: ["market", "indexes"], queryFn: getMarketIndexes });
  const sectors = useQuery({ queryKey: ["market", "sectors"], queryFn: getSectorPerformance });
  const vix = useQuery({ queryKey: ["market", "volatility"], queryFn: getVolatilityData });
  const events = useQuery({ queryKey: ["events"], queryFn: getEvents });
  const insights = useQuery({ queryKey: ["research", "insights"], queryFn: getResearchInsights });
  const signals = useQuery({ queryKey: ["signals", "scores"], queryFn: getSignalScores });

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Morning market overview — {new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" })}
          </p>
          <div className="mt-3">
            <DataSourceStatusBadge />
          </div>
        </div>

        {/* Market Indexes */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {indexes.isLoading ? (
            <>
              <CardSkeleton />
              <CardSkeleton />
              <CardSkeleton />
            </>
          ) : indexes.isError ? (
            <div className="col-span-3"><ErrorState onRetry={() => indexes.refetch()} /></div>
          ) : (
            indexes.data?.map((idx) => <MarketIndexCard key={idx.ticker} {...idx} />)
          )}
        </div>

        {/* VIX + Sector Heatmap */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="terminal-card p-4">
            <div className="flex items-center gap-2 mb-3">
              <Activity className="h-4 w-4 text-primary" />
              <h3 className="text-sm font-semibold text-foreground">Volatility (VIX)</h3>
            </div>
            {vix.isLoading ? (
              <div className="space-y-2">
                <div className="h-9 bg-muted animate-pulse rounded" />
                <div className="h-4 w-1/2 bg-muted animate-pulse rounded" />
              </div>
            ) : vix.data ? (
              <>
                <p className="font-mono text-3xl font-bold text-foreground">{vix.data.vix}</p>
                <p className={`font-mono text-sm mt-1 ${vix.data.change < 0 ? "text-success" : "text-danger"}`}>
                  {vix.data.change > 0 ? "+" : ""}{vix.data.change} · {vix.data.trend}
                </p>
              </>
            ) : null}
          </div>

          <div className="terminal-card p-4 lg:col-span-2">
            <h3 className="text-sm font-semibold text-foreground mb-3">Sector Performance</h3>
            {sectors.isLoading ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                {Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} className="h-12 bg-muted animate-pulse rounded-md" />
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                {sectors.data?.map((s) => (
                  <div key={s.name} className={`rounded-md p-2 text-center ${s.change >= 0 ? "bg-success/10" : "bg-danger/10"}`}>
                    <p className="text-xs text-muted-foreground truncate">{s.name}</p>
                    <p className={`font-mono text-sm font-semibold ${s.change >= 0 ? "text-success" : "text-danger"}`}>
                      {s.change >= 0 ? "+" : ""}{s.change.toFixed(2)}%
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Events + Insights */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="terminal-card p-4">
            <h3 className="text-sm font-semibold text-foreground mb-3">Today's Key Events</h3>
            {events.isLoading ? (
              <ListSkeleton count={3} />
            ) : events.data?.length === 0 ? (
              <EmptyState title="No events" description="No market events detected today." />
            ) : (
              <div className="space-y-3">
                {events.data?.slice(0, 4).map((evt) => (
                  <div key={evt.id} className="flex items-start gap-3 p-3 rounded-lg bg-muted/30">
                    <span className="font-mono text-xs font-bold text-primary bg-primary/10 px-2 py-1 rounded shrink-0">
                      {evt.ticker}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm text-foreground leading-snug line-clamp-2">{evt.headline}</p>
                      <div className="flex items-center gap-2 mt-1.5">
                        <span className="text-xs text-muted-foreground">{evt.category}</span>
                        <SentimentBadge sentiment={evt.sentiment} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="terminal-card p-4">
            <h3 className="text-sm font-semibold text-foreground mb-3">Recent Research Insights</h3>
            {insights.isLoading ? (
              <ListSkeleton count={3} />
            ) : insights.data?.length === 0 ? (
              <EmptyState title="No insights" description="No research insights available." />
            ) : (
              <div className="space-y-3">
                {insights.data?.map((insight) => (
                  <InsightCard key={insight.id} insight={insight} />
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="terminal-card p-4">
          <h3 className="text-sm font-semibold text-foreground mb-3">Top Signals</h3>
          {signals.isLoading ? (
            <ListSkeleton count={4} />
          ) : signals.data?.length === 0 ? (
            <EmptyState title="No signals" description="No scored event signals are available yet." />
          ) : (
            <div className="space-y-3">
              {signals.data?.slice(0, 5).map((signal) => (
                <div key={signal.id} className="flex items-start justify-between gap-4 p-3 rounded-lg bg-muted/30">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-xs font-bold text-primary bg-primary/10 px-2 py-1 rounded">
                        {signal.targetTicker}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {signal.targetType === "primary" ? "Primary" : signal.relationshipType || "Related"} · {signal.horizon}
                      </span>
                      <SignalConfidenceBadge band={signal.confidenceBand} />
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {signal.eventCategory} · {signal.primaryTicker}
                      {signal.relatedTicker ? ` -> ${signal.relatedTicker}` : ""}
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="font-mono text-lg font-semibold text-foreground">{signal.score.toFixed(1)}</p>
                    <p className="text-xs text-muted-foreground">{signal.horizon}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
