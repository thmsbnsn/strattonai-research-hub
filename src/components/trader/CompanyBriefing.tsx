import { useQuery } from "@tanstack/react-query";
import {
  Building2,
  TrendingUp,
  Users,
  AlertTriangle,
  BarChart3,
  Shield,
  Target,
  Layers,
  Activity,
} from "lucide-react";
import { getSignalScores } from "@/services/signalService";
import { getEvents } from "@/services/eventService";
import { ListSkeleton } from "@/components/LoadingSkeletons";

interface CompanyBriefingProps {
  ticker: string;
}

export function CompanyBriefing({ ticker }: CompanyBriefingProps) {
  const signals = useQuery({
    queryKey: ["signals", "scores", ticker],
    queryFn: () => getSignalScores(ticker),
  });

  const events = useQuery({ queryKey: ["events"], queryFn: getEvents });

  const companyEvents =
    events.data?.filter((e) => e.ticker === ticker).slice(0, 3) ?? [];
  const topSignals = signals.data?.slice(0, 4) ?? [];
  const bestSignal = topSignals[0];

  return (
    <div className="space-y-4">
      {/* Company identity header */}
      <div className="terminal-card p-5">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
            <Building2 className="h-6 w-6 text-primary" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-bold text-foreground font-mono tracking-wide">
                {ticker}
              </h2>
              {bestSignal && (
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-medium uppercase tracking-wider ${
                    bestSignal.confidenceBand === "High"
                      ? "bg-success/10 text-success"
                      : bestSignal.confidenceBand === "Moderate"
                      ? "bg-warning/10 text-warning"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {bestSignal.confidenceBand} Confidence
                </span>
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              Intelligence Briefing ·{" "}
              {new Date().toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
              })}
            </p>
          </div>
        </div>
      </div>

      {/* Outlook & projection — full width hero */}
      <div className="terminal-card p-5">
        <div className="flex items-center gap-2 mb-3">
          <Target className="h-4 w-4 text-primary" />
          <h4 className="text-sm font-semibold text-foreground">
            Outlook & Forward Projection
          </h4>
        </div>
        {signals.isLoading ? (
          <ListSkeleton count={2} />
        ) : bestSignal ? (
          <div className="space-y-3">
            <p className="text-sm text-foreground leading-relaxed">
              {ticker} has{" "}
              <span className="font-mono font-semibold text-primary">
                {topSignals.length}
              </span>{" "}
              active signal(s). The strongest scores{" "}
              <span className="font-mono font-semibold">
                {bestSignal.score.toFixed(1)}
              </span>{" "}
              on a{" "}
              <span className="font-mono">{bestSignal.horizon}</span>{" "}
              horizon with{" "}
              <span className="font-semibold">
                {bestSignal.confidenceBand}
              </span>{" "}
              confidence, driven by {bestSignal.eventCategory} activity.
            </p>
            <div className="grid grid-cols-3 gap-3">
              <div className="rounded-lg bg-muted/30 p-3 text-center">
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">
                  Avg Return
                </p>
                <p
                  className={`font-mono text-sm font-bold ${
                    bestSignal.avgReturn >= 0
                      ? "text-success"
                      : "text-danger"
                  }`}
                >
                  {bestSignal.avgReturn >= 0 ? "+" : ""}
                  {bestSignal.avgReturn.toFixed(2)}%
                </p>
              </div>
              <div className="rounded-lg bg-muted/30 p-3 text-center">
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">
                  Win Rate
                </p>
                <p className="font-mono text-sm font-bold text-foreground">
                  {(bestSignal.winRate * 100).toFixed(0)}%
                </p>
              </div>
              <div className="rounded-lg bg-muted/30 p-3 text-center">
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">
                  Sample Size
                </p>
                <p className="font-mono text-sm font-bold text-foreground">
                  n={bestSignal.sampleSize}
                </p>
              </div>
            </div>
          </div>
        ) : (
          <p className="text-xs text-muted-foreground">
            No scored signals available for {ticker}. Monitor the event feed
            for emerging catalysts.
          </p>
        )}
      </div>

      {/* 2×2 detail grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Recent Events */}
        <div className="terminal-card p-4">
          <div className="flex items-center gap-2 mb-3">
            <Activity className="h-4 w-4 text-primary" />
            <h4 className="text-sm font-semibold text-foreground">
              Current Event Context
            </h4>
          </div>
          {events.isLoading ? (
            <ListSkeleton count={2} />
          ) : companyEvents.length === 0 ? (
            <p className="text-xs text-muted-foreground">
              No recent events detected for {ticker}.
            </p>
          ) : (
            <div className="space-y-2">
              {companyEvents.map((evt) => (
                <div key={evt.id} className="p-2.5 rounded-md bg-muted/30">
                  <p className="text-xs text-foreground leading-snug line-clamp-2">
                    {evt.headline}
                  </p>
                  <span className="text-[10px] text-muted-foreground mt-1 block">
                    {evt.category}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Active Signals */}
        <div className="terminal-card p-4">
          <div className="flex items-center gap-2 mb-3">
            <BarChart3 className="h-4 w-4 text-primary" />
            <h4 className="text-sm font-semibold text-foreground">
              Active Signals
            </h4>
          </div>
          {signals.isLoading ? (
            <ListSkeleton count={2} />
          ) : topSignals.length === 0 ? (
            <p className="text-xs text-muted-foreground">
              No signals scored for {ticker}.
            </p>
          ) : (
            <div className="space-y-2">
              {topSignals.map((sig) => (
                <div
                  key={sig.id}
                  className="flex items-center justify-between p-2.5 rounded-md bg-muted/30"
                >
                  <div>
                    <p className="text-xs text-foreground">
                      {sig.eventCategory}
                    </p>
                    <span className="text-[10px] text-muted-foreground">
                      {sig.horizon} · {sig.confidenceBand}
                    </span>
                  </div>
                  <span className="font-mono text-sm font-semibold text-foreground">
                    {sig.score.toFixed(1)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Related Companies */}
        <div className="terminal-card p-4">
          <div className="flex items-center gap-2 mb-3">
            <Users className="h-4 w-4 text-primary" />
            <h4 className="text-sm font-semibold text-foreground">
              Peers & Related Companies
            </h4>
          </div>
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground">
              Peer and relationship context from the company graph will populate
              once connected.
            </p>
            <div className="flex gap-2 flex-wrap">
              {["Supplier", "Competitor", "Customer"].map((t) => (
                <span
                  key={t}
                  className="text-[10px] px-2 py-1 rounded-md border border-border text-muted-foreground"
                >
                  {t}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Evidence Strength & Risk */}
        <div className="terminal-card p-4">
          <div className="flex items-center gap-2 mb-3">
            <Layers className="h-4 w-4 text-primary" />
            <h4 className="text-sm font-semibold text-foreground">
              Evidence & Confidence
            </h4>
          </div>
          {topSignals.length > 0 ? (
            <div className="space-y-2.5">
              {topSignals.some((s) => s.confidenceBand === "Low") && (
                <div className="p-2 rounded-md bg-warning/10 border border-warning/20">
                  <div className="flex items-center gap-1.5">
                    <AlertTriangle className="h-3 w-3 text-warning shrink-0" />
                    <p className="text-[11px] text-warning">
                      Some signals have low confidence — limited evidence depth.
                    </p>
                  </div>
                </div>
              )}
              <div className="text-xs text-muted-foreground space-y-1">
                <p>
                  <span className="text-foreground font-medium">
                    {topSignals.filter((s) => s.confidenceBand === "High").length}
                  </span>{" "}
                  High ·{" "}
                  <span className="text-foreground font-medium">
                    {topSignals.filter((s) => s.confidenceBand === "Moderate").length}
                  </span>{" "}
                  Moderate ·{" "}
                  <span className="text-foreground font-medium">
                    {topSignals.filter((s) => s.confidenceBand === "Low").length}
                  </span>{" "}
                  Low
                </p>
                <p>
                  Median sample depth:{" "}
                  <span className="font-mono text-foreground">
                    n=
                    {Math.round(
                      topSignals.reduce((a, s) => a + s.sampleSize, 0) /
                        topSignals.length
                    )}
                  </span>
                </p>
              </div>
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">
              No evidence data available for {ticker}.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

/* Polished empty state shown when no ticker is selected */
export function CompanyBriefingEmpty() {
  return (
    <div className="terminal-card p-8 flex flex-col items-center justify-center text-center min-h-[360px]">
      <div className="w-14 h-14 rounded-2xl bg-primary/5 border border-border flex items-center justify-center mb-4">
        <Shield className="h-6 w-6 text-muted-foreground" />
      </div>
      <h3 className="text-sm font-semibold text-foreground mb-1">
        Company Intelligence Briefing
      </h3>
      <p className="text-xs text-muted-foreground max-w-sm leading-relaxed">
        Search for a ticker above to load a full intelligence briefing — including
        outlook projections, active signals, peer context, evidence strength, and
        risk flags.
      </p>
      <div className="flex gap-2 mt-5 flex-wrap justify-center">
        {["NVDA", "AAPL", "TSLA", "MSFT"].map((t) => (
          <span
            key={t}
            className="font-mono text-[10px] px-2.5 py-1 rounded-md bg-muted/40 text-muted-foreground border border-border"
          >
            {t}
          </span>
        ))}
      </div>
    </div>
  );
}
