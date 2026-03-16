import { useQuery } from "@tanstack/react-query";
import { Target, FileText, Lightbulb, CheckCircle, Rss, TrendingUp } from "lucide-react";
import { getSignalScores, getSignalsForTicker } from "@/services/signalService";
import { getEvents } from "@/services/eventService";
import { ListSkeleton } from "@/components/LoadingSkeletons";

export function TopRankedSignals({ ticker }: { ticker?: string | null }) {
  const { data, isLoading } = useQuery({
    queryKey: ["signals", "top", ticker ?? "all"],
    queryFn: () => (ticker ? getSignalsForTicker(ticker) : getSignalScores()),
  });

  const top = data?.slice(0, 4) ?? [];

  return (
    <div className="terminal-card p-4">
      <div className="flex items-center gap-2 mb-3">
        <Target className="h-4 w-4 text-primary" />
        <h4 className="text-sm font-semibold text-foreground">
          {ticker ? `${ticker} Signals` : "Top Ranked Signals"}
        </h4>
      </div>
      {isLoading ? (
        <ListSkeleton count={3} />
      ) : top.length === 0 ? (
        <p className="text-xs text-muted-foreground">No signals available.</p>
      ) : (
        <div className="space-y-2">
          {top.map((s) => (
            <div key={s.id} className="flex items-center justify-between p-2 rounded-md bg-muted/30">
              <div>
                <span className="font-mono text-xs font-bold text-primary">{s.targetTicker}</span>
                <span className="text-xs text-muted-foreground ml-2">{s.horizon}</span>
              </div>
              <span className="font-mono text-sm font-semibold text-foreground">{s.score.toFixed(1)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function TradeThesisCard({ ticker }: { ticker?: string | null }) {
  return (
    <div className="terminal-card p-4">
      <div className="flex items-center gap-2 mb-3">
        <Lightbulb className="h-4 w-4 text-warning" />
        <h4 className="text-sm font-semibold text-foreground">Trade Thesis</h4>
      </div>
      <p className="text-xs text-muted-foreground leading-relaxed">
        {ticker
          ? `Use ${ticker}'s signal stack, event context, and peer reactions to build a deterministic trade thesis.`
          : "Select a company above to generate a research-backed trade thesis based on recent events and signal scores."}
      </p>
    </div>
  );
}

export function EvidenceSummaryCard({ ticker }: { ticker?: string | null }) {
  return (
    <div className="terminal-card p-4">
      <div className="flex items-center gap-2 mb-3">
        <FileText className="h-4 w-4 text-primary" />
        <h4 className="text-sm font-semibold text-foreground">Research Evidence</h4>
      </div>
      <p className="text-xs text-muted-foreground leading-relaxed">
        {ticker
          ? `Event-study evidence, analog event summaries, and research notes for ${ticker} will accumulate here.`
          : "Evidence summaries from event studies and historical analogs will appear here when a company is selected."}
      </p>
    </div>
  );
}

export function PaperTradeIdeaCard({ ticker }: { ticker?: string | null }) {
  return (
    <div className="terminal-card p-4">
      <div className="flex items-center gap-2 mb-3">
        <TrendingUp className="h-4 w-4 text-success" />
        <h4 className="text-sm font-semibold text-foreground">Paper Trade Idea</h4>
      </div>
      <p className="text-xs text-muted-foreground leading-relaxed">
        {ticker
          ? `Once ${ticker} has a validated thesis, suggest a paper-trade entry, stop, target, and time horizon here.`
          : "Once a thesis is formed, a suggested paper trade entry will appear here with target, stop, and horizon."}
      </p>
    </div>
  );
}

export function LiveReadinessChecklist({ ticker }: { ticker?: string | null }) {
  const items = [
    { label: "Research signals scored", done: Boolean(ticker) },
    { label: "Event study evidence reviewed", done: false },
    { label: "Risk flags assessed", done: false },
    { label: "Paper trade validated", done: false },
    { label: "Broker connection verified", done: false },
  ];

  return (
    <div className="terminal-card p-4">
      <div className="flex items-center gap-2 mb-3">
        <CheckCircle className="h-4 w-4 text-primary" />
        <h4 className="text-sm font-semibold text-foreground">Live Trade Readiness</h4>
      </div>
      <div className="space-y-1.5">
        {items.map((item) => (
          <div key={item.label} className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full border ${item.done ? "bg-success border-success" : "border-border"}`} />
            <span className={`text-xs ${item.done ? "text-foreground" : "text-muted-foreground"}`}>{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function RecentRelatedEvents({ ticker }: { ticker?: string | null }) {
  const { data, isLoading } = useQuery({ queryKey: ["events"], queryFn: getEvents });
  const recent =
    data
      ?.filter((event) =>
        ticker
          ? event.ticker === ticker || event.relatedCompanies.some((company) => company.ticker === ticker)
          : true
      )
      .slice(0, 4) ?? [];

  return (
    <div className="terminal-card p-4">
      <div className="flex items-center gap-2 mb-3">
        <Rss className="h-4 w-4 text-primary" />
        <h4 className="text-sm font-semibold text-foreground">
          {ticker ? `${ticker} Event Context` : "Recent Events"}
        </h4>
      </div>
      {isLoading ? (
        <ListSkeleton count={3} />
      ) : recent.length === 0 ? (
        <p className="text-xs text-muted-foreground">No recent events.</p>
      ) : (
        <div className="space-y-2">
          {recent.map((evt) => (
            <div key={evt.id} className="p-2 rounded-md bg-muted/30">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-primary">{evt.ticker}</span>
                <span className="text-xs text-muted-foreground">{evt.category}</span>
              </div>
              <p className="text-xs text-foreground leading-snug line-clamp-1 mt-0.5">{evt.headline}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
