import { TrendingUp, TrendingDown, Activity, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { marketIndexes, sectorPerformance, volatilityData, marketEvents, researchInsights } from "@/lib/mockData";
import { AppLayout } from "@/components/AppLayout";

function IndexCard({ ticker, name, price, change, changePercent }: typeof marketIndexes[0]) {
  const isPositive = change >= 0;
  return (
    <div className="terminal-card p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-sm font-semibold text-foreground">{ticker}</span>
        {isPositive ? (
          <ArrowUpRight className="h-4 w-4 text-success" />
        ) : (
          <ArrowDownRight className="h-4 w-4 text-danger" />
        )}
      </div>
      <p className="text-xs text-muted-foreground mb-1">{name}</p>
      <p className="font-mono text-xl font-bold text-foreground">{price.toLocaleString()}</p>
      <p className={`font-mono text-sm mt-1 ${isPositive ? "text-success" : "text-danger"}`}>
        {isPositive ? "+" : ""}{change.toFixed(2)} ({isPositive ? "+" : ""}{changePercent.toFixed(2)}%)
      </p>
    </div>
  );
}

function SentimentBadge({ sentiment }: { sentiment: string }) {
  const colors = {
    positive: "bg-success/10 text-success",
    negative: "bg-danger/10 text-danger",
    neutral: "bg-muted text-muted-foreground",
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${colors[sentiment as keyof typeof colors]}`}>
      {sentiment}
    </span>
  );
}

export default function Dashboard() {
  return (
    <AppLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">Morning market overview — {new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" })}</p>
        </div>

        {/* Market Indexes */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {marketIndexes.map((idx) => (
            <IndexCard key={idx.ticker} {...idx} />
          ))}
        </div>

        {/* VIX + Sector Heatmap */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Volatility */}
          <div className="terminal-card p-4">
            <div className="flex items-center gap-2 mb-3">
              <Activity className="h-4 w-4 text-primary" />
              <h3 className="text-sm font-semibold text-foreground">Volatility (VIX)</h3>
            </div>
            <p className="font-mono text-3xl font-bold text-foreground">{volatilityData.vix}</p>
            <p className={`font-mono text-sm mt-1 ${volatilityData.change < 0 ? "text-success" : "text-danger"}`}>
              {volatilityData.change > 0 ? "+" : ""}{volatilityData.change} · {volatilityData.trend}
            </p>
          </div>

          {/* Sector Heatmap */}
          <div className="terminal-card p-4 lg:col-span-2">
            <h3 className="text-sm font-semibold text-foreground mb-3">Sector Performance</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
              {sectorPerformance.map((s) => (
                <div
                  key={s.name}
                  className={`rounded-md p-2 text-center ${s.change >= 0 ? "bg-success/10" : "bg-danger/10"}`}
                >
                  <p className="text-xs text-muted-foreground truncate">{s.name}</p>
                  <p className={`font-mono text-sm font-semibold ${s.change >= 0 ? "text-success" : "text-danger"}`}>
                    {s.change >= 0 ? "+" : ""}{s.change.toFixed(2)}%
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Events + Insights */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Today's Key Events */}
          <div className="terminal-card p-4">
            <h3 className="text-sm font-semibold text-foreground mb-3">Today's Key Events</h3>
            <div className="space-y-3">
              {marketEvents.slice(0, 4).map((evt) => (
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
          </div>

          {/* Research Insights */}
          <div className="terminal-card p-4">
            <h3 className="text-sm font-semibold text-foreground mb-3">Recent Research Insights</h3>
            <div className="space-y-3">
              {researchInsights.map((insight) => (
                <div key={insight.id} className="p-3 rounded-lg bg-muted/30 border-l-2 border-primary/50">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="text-sm font-medium text-foreground">{insight.title}</h4>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      insight.confidence === "High" ? "bg-success/10 text-success" : "bg-warning/10 text-warning"
                    }`}>
                      {insight.confidence}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground leading-relaxed">{insight.summary}</p>
                  <p className="text-xs text-muted-foreground mt-1 font-mono">n={insight.eventCount}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
