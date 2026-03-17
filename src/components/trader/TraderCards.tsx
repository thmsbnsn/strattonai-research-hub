import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { CheckCircle, FileText, Lightbulb, Rss, Target, TrendingUp } from "lucide-react";
import { getSignalScores } from "@/services/signalService";
import { getCompanyBriefing } from "@/services/traderGatewayService";
import { ListSkeleton } from "@/components/LoadingSkeletons";

function useBriefing(ticker?: string | null, tradingMode: "paper" | "live" = "paper") {
  return useQuery({
    queryKey: ["trader", "company-briefing", ticker ?? "none", tradingMode],
    queryFn: () => getCompanyBriefing(ticker || "", tradingMode),
    enabled: Boolean(ticker),
  });
}

export function TopRankedSignals({ ticker }: { ticker?: string | null }) {
  const { data, isLoading } = useQuery({
    queryKey: ["signals", "top", ticker ?? "all"],
    queryFn: () => getSignalScores(ticker ?? undefined),
  });

  const top = data?.slice(0, 4) ?? [];

  return (
    <div className="terminal-card p-4">
      <div className="flex items-center gap-2 mb-3">
        <Target className="h-4 w-4 text-primary" />
        <h4 className="text-sm font-semibold text-foreground">{ticker ? `${ticker} Signals` : "Top Ranked Signals"}</h4>
      </div>
      {isLoading ? (
        <ListSkeleton count={3} />
      ) : top.length === 0 ? (
        <p className="text-xs text-muted-foreground">No signals available.</p>
      ) : (
        <div className="space-y-2">
          {top.map((signal) => (
            <div key={signal.id} className="flex items-center justify-between p-2 rounded-md bg-muted/30">
              <div>
                <span className="font-mono text-xs font-bold text-primary">{signal.targetTicker}</span>
                <span className="text-xs text-muted-foreground ml-2">{signal.eventCategory} · {signal.horizon}</span>
              </div>
              <span className="font-mono text-sm font-semibold text-foreground">{signal.score.toFixed(1)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function TradeThesisCard({
  ticker,
  tradingMode = "paper",
}: {
  ticker?: string | null;
  tradingMode?: "paper" | "live";
}) {
  const briefing = useBriefing(ticker, tradingMode);
  const navigate = useNavigate();

  return (
    <div className="terminal-card p-4">
      <div className="flex items-center gap-2 mb-3">
        <Lightbulb className="h-4 w-4 text-warning" />
        <h4 className="text-sm font-semibold text-foreground">Trade Thesis</h4>
      </div>
      {!ticker ? (
        <p className="text-xs text-muted-foreground leading-relaxed">
          Select a company above to generate a research-backed trade thesis based on recent events and signal scores.
        </p>
      ) : briefing.isLoading ? (
        <ListSkeleton count={2} />
      ) : briefing.data ? (
        <div className="space-y-3">
          <p className="text-xs text-muted-foreground leading-relaxed">{briefing.data.thesisSummary}</p>
          {briefing.data.outlook.strongestSignal ? (
            <button
              onClick={() =>
                navigate(
                  `/studies?ticker=${encodeURIComponent(briefing.data!.ticker)}&category=${encodeURIComponent(
                    briefing.data!.outlook.strongestSignal!.eventCategory
                  )}`
                )
              }
              className="inline-flex items-center gap-1 text-[11px] text-primary hover:text-primary/80"
            >
              Inspect strongest evidence slice
            </button>
          ) : null}
        </div>
      ) : (
        <p className="text-xs text-muted-foreground">No thesis is available.</p>
      )}
    </div>
  );
}

export function EvidenceSummaryCard({
  ticker,
  tradingMode = "paper",
}: {
  ticker?: string | null;
  tradingMode?: "paper" | "live";
}) {
  const briefing = useBriefing(ticker, tradingMode);
  const navigate = useNavigate();

  return (
    <div className="terminal-card p-4">
      <div className="flex items-center gap-2 mb-3">
        <FileText className="h-4 w-4 text-primary" />
        <h4 className="text-sm font-semibold text-foreground">Research Evidence</h4>
      </div>
      {!ticker ? (
        <p className="text-xs text-muted-foreground leading-relaxed">
          Evidence summaries from event studies and historical analogs will appear here when a company is selected.
        </p>
      ) : briefing.isLoading ? (
        <ListSkeleton count={2} />
      ) : briefing.data ? (
        <div className="space-y-3">
          <p className="text-xs text-muted-foreground leading-relaxed">{briefing.data.evidenceSummary}</p>
          <div className="grid grid-cols-3 gap-2">
            <div className="rounded-md bg-muted/30 p-2 text-center">
              <div className="text-[10px] text-muted-foreground">Signals</div>
              <div className="font-mono text-sm text-foreground">{briefing.data.topSignals.length}</div>
            </div>
            <div className="rounded-md bg-muted/30 p-2 text-center">
              <div className="text-[10px] text-muted-foreground">Studies</div>
              <div className="font-mono text-sm text-foreground">{briefing.data.studySlices.length}</div>
            </div>
            <div className="rounded-md bg-muted/30 p-2 text-center">
              <div className="text-[10px] text-muted-foreground">Events</div>
              <div className="font-mono text-sm text-foreground">{briefing.data.recentEvents.length}</div>
            </div>
          </div>
          <button
            onClick={() => navigate(`/companies?search=${encodeURIComponent(briefing.data!.ticker)}`)}
            className="inline-flex items-center gap-1 text-[11px] text-primary hover:text-primary/80"
          >
            Open company evidence view
          </button>
        </div>
      ) : (
        <p className="text-xs text-muted-foreground">No evidence summary is available.</p>
      )}
    </div>
  );
}

export function PaperTradeIdeaCard({
  ticker,
  tradingMode = "paper",
}: {
  ticker?: string | null;
  tradingMode?: "paper" | "live";
}) {
  const briefing = useBriefing(ticker, tradingMode);

  return (
    <div className="terminal-card p-4">
      <div className="flex items-center gap-2 mb-3">
        <TrendingUp className="h-4 w-4 text-success" />
        <h4 className="text-sm font-semibold text-foreground">Paper Trade Idea</h4>
      </div>
      {!ticker ? (
        <p className="text-xs text-muted-foreground leading-relaxed">
          Once a thesis is formed, a suggested paper trade entry will appear here with target, stop, and horizon.
        </p>
      ) : briefing.isLoading ? (
        <ListSkeleton count={2} />
      ) : briefing.data?.outlook.strongestSignal ? (
        <div className="space-y-2 text-xs text-muted-foreground">
          <p>
            Use <span className="font-mono text-foreground">{briefing.data.outlook.strongestSignal.eventCategory}</span> on a{" "}
            <span className="font-mono text-foreground">{briefing.data.outlook.strongestSignal.horizon}</span> horizon as the anchor setup.
          </p>
          <p>
            Keep it paper-only until the live-readiness checklist is green and the evidence stack is not low-confidence heavy.
          </p>
        </div>
      ) : (
        <p className="text-xs text-muted-foreground">No paper-trade idea is available yet.</p>
      )}
    </div>
  );
}

export function LiveReadinessChecklist({
  ticker,
  tradingMode = "paper",
}: {
  ticker?: string | null;
  tradingMode?: "paper" | "live";
}) {
  const briefing = useBriefing(ticker, tradingMode);

  return (
    <div className="terminal-card p-4">
      <div className="flex items-center gap-2 mb-3">
        <CheckCircle className="h-4 w-4 text-primary" />
        <h4 className="text-sm font-semibold text-foreground">Live Trade Readiness</h4>
      </div>
      {!ticker ? (
        <p className="text-xs text-muted-foreground">Select a company to review live-trade guardrails.</p>
      ) : briefing.isLoading ? (
        <ListSkeleton count={4} />
      ) : briefing.data ? (
        <div className="space-y-3">
          <div className="space-y-1.5">
            {briefing.data.readiness.items.map((item) => (
              <div key={item.key} className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full border ${item.done ? "bg-success border-success" : "border-border"}`} />
                <span className={`text-xs ${item.done ? "text-foreground" : "text-muted-foreground"}`}>{item.label}</span>
              </div>
            ))}
          </div>
          {briefing.data.readiness.hardBlockers.length > 0 ? (
            <div className="rounded-md border border-danger/20 bg-danger/10 p-2">
              <div className="text-[10px] uppercase tracking-[0.14em] text-danger mb-1">Hard blockers</div>
              <ul className="space-y-1 text-[11px] text-danger">
                {briefing.data.readiness.hardBlockers.map((blocker) => (
                  <li key={blocker}>{blocker}</li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="text-xs text-success">No structural live-trade blockers are currently reported.</p>
          )}
        </div>
      ) : (
        <p className="text-xs text-muted-foreground">No readiness data is available.</p>
      )}
    </div>
  );
}

export function RecentRelatedEvents({ ticker }: { ticker?: string | null }) {
  const briefing = useBriefing(ticker);
  const navigate = useNavigate();

  return (
    <div className="terminal-card p-4">
      <div className="flex items-center gap-2 mb-3">
        <Rss className="h-4 w-4 text-primary" />
        <h4 className="text-sm font-semibold text-foreground">{ticker ? `${ticker} Event Context` : "Recent Events"}</h4>
      </div>
      {!ticker ? (
        <p className="text-xs text-muted-foreground">Select a ticker to inspect event context.</p>
      ) : briefing.isLoading ? (
        <ListSkeleton count={3} />
      ) : briefing.data?.recentEvents.length ? (
        <div className="space-y-2">
          {briefing.data.recentEvents.slice(0, 4).map((event) => (
            <button
              key={event.id}
              onClick={() =>
                navigate(
                  `/events?ticker=${encodeURIComponent(briefing.data!.ticker)}&category=${encodeURIComponent(event.category)}`
                )
              }
              className="w-full p-2 rounded-md bg-muted/30 text-left hover:bg-muted/50"
            >
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-primary">{event.ticker}</span>
                <span className="text-xs text-muted-foreground">{event.category}</span>
              </div>
              <p className="text-xs text-foreground leading-snug line-clamp-1 mt-0.5">{event.headline}</p>
            </button>
          ))}
        </div>
      ) : (
        <p className="text-xs text-muted-foreground">No recent events.</p>
      )}
    </div>
  );
}
