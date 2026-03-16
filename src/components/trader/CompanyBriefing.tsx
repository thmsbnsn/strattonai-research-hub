import { useQuery } from "@tanstack/react-query";
import { Building2, TrendingUp, Users, AlertTriangle, BarChart3, Shield } from "lucide-react";
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

  const companyEvents = events.data?.filter((e) => e.ticker === ticker).slice(0, 3) ?? [];
  const topSignals = signals.data?.slice(0, 3) ?? [];

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="terminal-card p-4">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
            <Building2 className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-foreground font-mono">{ticker}</h3>
            <p className="text-xs text-muted-foreground">Company Intelligence Briefing</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Recent Events */}
        <div className="terminal-card p-4">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="h-4 w-4 text-primary" />
            <h4 className="text-sm font-semibold text-foreground">Current Event Context</h4>
          </div>
          {events.isLoading ? (
            <ListSkeleton count={2} />
          ) : companyEvents.length === 0 ? (
            <p className="text-xs text-muted-foreground">No recent events detected for {ticker}.</p>
          ) : (
            <div className="space-y-2">
              {companyEvents.map((evt) => (
                <div key={evt.id} className="p-2 rounded-md bg-muted/30">
                  <p className="text-xs text-foreground leading-snug line-clamp-2">{evt.headline}</p>
                  <span className="text-xs text-muted-foreground">{evt.category}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Signals */}
        <div className="terminal-card p-4">
          <div className="flex items-center gap-2 mb-3">
            <BarChart3 className="h-4 w-4 text-primary" />
            <h4 className="text-sm font-semibold text-foreground">Recent Signals</h4>
          </div>
          {signals.isLoading ? (
            <ListSkeleton count={2} />
          ) : topSignals.length === 0 ? (
            <p className="text-xs text-muted-foreground">No signals scored for {ticker}.</p>
          ) : (
            <div className="space-y-2">
              {topSignals.map((sig) => (
                <div key={sig.id} className="flex items-center justify-between p-2 rounded-md bg-muted/30">
                  <div>
                    <p className="text-xs text-foreground">{sig.eventCategory}</p>
                    <span className="text-xs text-muted-foreground">{sig.horizon} · {sig.confidenceBand}</span>
                  </div>
                  <span className="font-mono text-sm font-semibold text-foreground">{sig.score.toFixed(1)}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Related Companies */}
        <div className="terminal-card p-4">
          <div className="flex items-center gap-2 mb-3">
            <Users className="h-4 w-4 text-primary" />
            <h4 className="text-sm font-semibold text-foreground">Related Companies</h4>
          </div>
          <p className="text-xs text-muted-foreground">
            Peer and relationship context will populate from the company relationship graph once connected.
          </p>
        </div>

        {/* Risk Flags */}
        <div className="terminal-card p-4">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="h-4 w-4 text-warning" />
            <h4 className="text-sm font-semibold text-foreground">Risk Flags</h4>
          </div>
          {topSignals.some((s) => s.confidenceBand === "Low") ? (
            <div className="p-2 rounded-md bg-warning/10 border border-warning/20">
              <p className="text-xs text-warning">Some signals have low confidence — limited evidence depth.</p>
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">No specific risk flags detected for {ticker}.</p>
          )}
        </div>
      </div>

      {/* Outlook Summary */}
      <div className="terminal-card p-4">
        <div className="flex items-center gap-2 mb-3">
          <Shield className="h-4 w-4 text-primary" />
          <h4 className="text-sm font-semibold text-foreground">Outlook Summary</h4>
        </div>
        <p className="text-xs text-muted-foreground leading-relaxed">
          {topSignals.length > 0
            ? `${ticker} has ${topSignals.length} active signal(s). Top signal scores ${topSignals[0]?.score.toFixed(1)} on a ${topSignals[0]?.horizon} horizon with ${topSignals[0]?.confidenceBand} confidence. Further analysis recommended before positioning.`
            : `No active signals for ${ticker}. Monitor the event feed for emerging catalysts.`}
        </p>
      </div>
    </div>
  );
}
