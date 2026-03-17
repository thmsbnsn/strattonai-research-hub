import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Building2,
  ExternalLink,
  Layers,
  Shield,
  Target,
  Users,
} from "lucide-react";
import { ListSkeleton } from "@/components/LoadingSkeletons";
import { RelationshipStudyTable } from "@/components/research/RelationshipStudyTable";
import { EvidenceSliceDrawer } from "@/components/research/EvidenceSliceDrawer";
import { getCompanyBriefing } from "@/services/traderGatewayService";
import type { CompanyBriefingPayload } from "@/models";

interface CompanyBriefingProps {
  ticker: string;
  tradingMode?: "paper" | "live";
}

function ConfidenceBadge({ band }: { band: "High" | "Moderate" | "Low" }) {
  return (
    <span
      className={`text-[10px] px-2 py-0.5 rounded-full font-medium uppercase tracking-wider ${
        band === "High"
          ? "bg-success/10 text-success"
          : band === "Moderate"
          ? "bg-warning/10 text-warning"
          : "bg-muted text-muted-foreground"
      }`}
    >
      {band} Confidence
    </span>
  );
}

function RiskFlags({ briefing }: { briefing: CompanyBriefingPayload }) {
  if (briefing.riskFlags.length === 0) {
    return (
      <p className="text-xs text-muted-foreground">
        No immediate structural warnings were detected for the current evidence bundle.
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {briefing.riskFlags.map((flag) => (
        <div key={flag} className="p-2 rounded-md bg-warning/10 border border-warning/20">
          <div className="flex items-center gap-1.5">
            <AlertTriangle className="h-3 w-3 text-warning shrink-0" />
            <p className="text-[11px] text-warning">{flag}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

export function CompanyBriefing({ ticker, tradingMode = "paper" }: CompanyBriefingProps) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const navigate = useNavigate();
  const briefingQuery = useQuery({
    queryKey: ["trader", "company-briefing", ticker, tradingMode],
    queryFn: () => getCompanyBriefing(ticker, tradingMode),
  });

  if (briefingQuery.isLoading) {
    return <ListSkeleton count={5} />;
  }

  const briefing = briefingQuery.data;
  if (!briefing) {
    return (
      <div className="terminal-card p-5">
        <p className="text-xs text-muted-foreground">No company briefing data is available for {ticker}.</p>
      </div>
    );
  }

  const bestSignal = briefing.topSignals[0];
  const profileContext = [briefing.profile.sector, briefing.profile.industry].filter(Boolean).join(" · ");

  return (
    <div className="space-y-4">
      <div className="terminal-card p-5">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
            <Building2 className="h-6 w-6 text-primary" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-3 flex-wrap">
              <h2 className="text-xl font-bold text-foreground font-mono tracking-wide">{briefing.ticker}</h2>
              {bestSignal ? <ConfidenceBadge band={bestSignal.confidenceBand} /> : null}
            </div>
            <p className="text-sm text-foreground mt-0.5">{briefing.profile.name}</p>
            <p className="text-xs text-muted-foreground mt-0.5">
              Intelligence Briefing
              {profileContext ? ` · ${profileContext}` : ""}
              {briefing.latestPrice.tradeDate ? ` · price as of ${briefing.latestPrice.tradeDate}` : ""}
            </p>
          </div>
          <div className="text-right text-xs text-muted-foreground">
            <div>Price rows: <span className="font-mono text-foreground">{briefing.latestPrice.rowCount}</span></div>
            <div>
              Last close:{" "}
              <span className="font-mono text-foreground">
                {typeof briefing.latestPrice.close === "number" ? briefing.latestPrice.close.toFixed(2) : "N/A"}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="terminal-card p-5">
        <div className="flex items-center gap-2 mb-3">
          <Target className="h-4 w-4 text-primary" />
          <h4 className="text-sm font-semibold text-foreground">Outlook & Forward Projection</h4>
        </div>
        <div className="space-y-3">
          <p className="text-sm text-foreground leading-relaxed">{briefing.thesisSummary}</p>
          <p className="text-xs text-muted-foreground">{briefing.evidenceSummary}</p>
          {bestSignal ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="rounded-lg bg-muted/30 p-3 text-center">
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Score</p>
                <p className="font-mono text-sm font-bold text-foreground">{bestSignal.score.toFixed(1)}</p>
              </div>
              <div className="rounded-lg bg-muted/30 p-3 text-center">
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Avg Return</p>
                <p className={`font-mono text-sm font-bold ${bestSignal.avgReturn >= 0 ? "text-success" : "text-danger"}`}>
                  {bestSignal.avgReturn >= 0 ? "+" : ""}{bestSignal.avgReturn.toFixed(2)}%
                </p>
              </div>
              <div className="rounded-lg bg-muted/30 p-3 text-center">
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Win Rate</p>
                <p className="font-mono text-sm font-bold text-foreground">{bestSignal.winRate.toFixed(1)}%</p>
              </div>
              <div className="rounded-lg bg-muted/30 p-3 text-center">
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Sample Size</p>
                <p className="font-mono text-sm font-bold text-foreground">n={bestSignal.sampleSize}</p>
              </div>
            </div>
          ) : null}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="terminal-card p-4">
          <div className="flex items-center justify-between gap-2 mb-3">
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-primary" />
              <h4 className="text-sm font-semibold text-foreground">Current Event Context</h4>
            </div>
            <button
              onClick={() => navigate(`/events?ticker=${encodeURIComponent(briefing.ticker)}`)}
              className="inline-flex items-center gap-1 text-[11px] text-primary hover:text-primary/80"
            >
              Open Feed <ExternalLink className="h-3 w-3" />
            </button>
          </div>
          {briefing.recentEvents.length === 0 ? (
            <p className="text-xs text-muted-foreground">No recent primary events detected for {briefing.ticker}.</p>
          ) : (
            <div className="space-y-2">
              {briefing.recentEvents.map((event) => (
                <div key={event.id} className="p-2.5 rounded-md bg-muted/30">
                  <p className="text-xs text-foreground leading-snug line-clamp-2">{event.headline}</p>
                  <div className="mt-1 flex items-center gap-2 text-[10px] text-muted-foreground">
                    <span>{event.category}</span>
                    <span>{event.sentiment}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="terminal-card p-4">
          <div className="flex items-center justify-between gap-2 mb-3">
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-primary" />
              <h4 className="text-sm font-semibold text-foreground">Active Signals</h4>
            </div>
            <button
              onClick={() => navigate(`/studies?ticker=${encodeURIComponent(briefing.ticker)}`)}
              className="inline-flex items-center gap-1 text-[11px] text-primary hover:text-primary/80"
            >
              Open Studies <ExternalLink className="h-3 w-3" />
            </button>
          </div>
          {briefing.topSignals.length === 0 ? (
            <p className="text-xs text-muted-foreground">No signals scored for {briefing.ticker}.</p>
          ) : (
            <div className="space-y-2">
              {briefing.topSignals.slice(0, 4).map((signal) => (
                <button
                  key={signal.id}
                  onClick={() =>
                    navigate(
                      `/studies?ticker=${encodeURIComponent(briefing.ticker)}&category=${encodeURIComponent(signal.eventCategory)}`
                    )
                  }
                  className="flex w-full items-center justify-between p-2.5 rounded-md bg-muted/30 text-left hover:bg-muted/50"
                >
                  <div>
                    <p className="text-xs text-foreground">{signal.eventCategory}</p>
                    <span className="text-[10px] text-muted-foreground">
                      {signal.horizon} · {signal.confidenceBand}
                    </span>
                  </div>
                  <span className="font-mono text-sm font-semibold text-foreground">{signal.score.toFixed(1)}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="terminal-card p-4">
          <div className="flex items-center gap-2 mb-3">
            <Users className="h-4 w-4 text-primary" />
            <h4 className="text-sm font-semibold text-foreground">Peers & Related Companies</h4>
          </div>
          {briefing.relationships.length === 0 ? (
            <p className="text-xs text-muted-foreground">No company-graph relationships are available for {briefing.ticker}.</p>
          ) : (
            <div className="space-y-2">
              {briefing.relationships.map((relationship) => (
                <button
                  key={`${relationship.counterpartyTicker}:${relationship.relationshipType}`}
                  onClick={() => navigate(`/companies?search=${encodeURIComponent(relationship.counterpartyTicker)}`)}
                  className="flex w-full items-center justify-between rounded-md bg-muted/30 px-3 py-2 text-left hover:bg-muted/50"
                >
                  <div>
                    <p className="font-mono text-xs font-semibold text-foreground">{relationship.counterpartyTicker}</p>
                    <p className="text-[10px] text-muted-foreground">{relationship.relationshipType}</p>
                  </div>
                  <span className="font-mono text-[11px] text-muted-foreground">{(relationship.strength * 100).toFixed(0)}%</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="terminal-card p-4">
          <div className="flex items-center gap-2 mb-3">
            <Layers className="h-4 w-4 text-primary" />
            <h4 className="text-sm font-semibold text-foreground">Evidence & Confidence</h4>
          </div>
          <div className="space-y-3">
            <RiskFlags briefing={briefing} />
            <div className="text-xs text-muted-foreground space-y-1">
              <p>
                <span className="text-foreground font-medium">{briefing.outlook.signalCount}</span> active signal(s)
              </p>
              <p>
                <span className="text-foreground font-medium">{briefing.studySlices.length}</span> related study slice(s)
              </p>
              <p>
                <span className="text-foreground font-medium">{briefing.relationships.length}</span> relationship edge(s)
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-2">
        <RelationshipStudyTable ticker={briefing.ticker} compact maxRows={5} />
        <button onClick={() => setDrawerOpen(true)} className="text-xs text-primary hover:text-primary/80">
          See all studies →
        </button>
      </div>
      <EvidenceSliceDrawer ticker={briefing.ticker} open={drawerOpen} onOpenChange={setDrawerOpen} />
    </div>
  );
}

export function CompanyBriefingEmpty() {
  return (
    <div className="terminal-card p-8 flex flex-col items-center justify-center text-center min-h-[360px]">
      <div className="w-14 h-14 rounded-2xl bg-primary/5 border border-border flex items-center justify-center mb-4">
        <Shield className="h-6 w-6 text-muted-foreground" />
      </div>
      <h3 className="text-sm font-semibold text-foreground mb-1">Company Intelligence Briefing</h3>
      <p className="text-xs text-muted-foreground max-w-sm leading-relaxed">
        Search for a ticker above to load a full intelligence briefing including outlook, active signals, peer context,
        evidence strength, and live-readiness guardrails.
      </p>
      <div className="flex gap-2 mt-5 flex-wrap justify-center">
        {["NVDA", "AAPL", "TSLA", "MSFT"].map((ticker) => (
          <span
            key={ticker}
            className="font-mono text-[10px] px-2.5 py-1 rounded-md bg-muted/40 text-muted-foreground border border-border"
          >
            {ticker}
          </span>
        ))}
      </div>
    </div>
  );
}
