import { useState } from "react";
import { ChevronDown, ChevronUp, Clock, ExternalLink } from "lucide-react";
import { marketEvents, type MarketEvent } from "@/lib/mockData";
import { AppLayout } from "@/components/AppLayout";

function EventCard({ event }: { event: MarketEvent }) {
  const [expanded, setExpanded] = useState(false);

  const sentimentColor = {
    positive: "text-success border-success/30",
    negative: "text-danger border-danger/30",
    neutral: "text-muted-foreground border-border",
  };

  const ts = new Date(event.timestamp);
  const timeStr = ts.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });

  return (
    <div className={`terminal-card border-l-2 ${sentimentColor[event.sentiment]} transition-all`}>
      <div
        className="p-4 cursor-pointer flex items-start gap-3"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="shrink-0 mt-0.5">
          <span className="font-mono text-xs font-bold text-primary bg-primary/10 px-2 py-1 rounded">
            {event.ticker}
          </span>
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-foreground leading-snug">{event.headline}</h3>
          <div className="flex flex-wrap items-center gap-2 mt-2">
            <span className="text-xs bg-muted px-2 py-0.5 rounded text-muted-foreground">{event.category}</span>
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <Clock className="h-3 w-3" /> {timeStr}
            </span>
          </div>
        </div>
        <button className="shrink-0 text-muted-foreground">
          {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
      </div>

      {expanded && (
        <div className="px-4 pb-4 space-y-3 animate-slide-in border-t border-border pt-3">
          {event.details && (
            <p className="text-xs text-muted-foreground leading-relaxed">{event.details}</p>
          )}

          {/* Related Companies */}
          <div>
            <h4 className="text-xs font-semibold text-foreground mb-2">Related Companies</h4>
            <div className="flex flex-wrap gap-2">
              {event.relatedCompanies.map((c) => (
                <div key={c.ticker} className="flex items-center gap-1.5 bg-muted/50 rounded-md px-2 py-1">
                  <span className="font-mono text-xs font-bold text-primary">{c.ticker}</span>
                  <span className="text-xs text-muted-foreground">· {c.relationship}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Historical Analog */}
          <div className="bg-muted/30 rounded-lg p-3">
            <h4 className="text-xs font-semibold text-foreground mb-1">Historical Analog</h4>
            <p className="text-xs text-muted-foreground leading-relaxed">{event.historicalAnalog}</p>
            <div className="flex gap-4 mt-2">
              <span className="font-mono text-xs text-foreground">
                Avg Return: <span className={event.avgReturn >= 0 ? "text-success" : "text-danger"}>
                  {event.avgReturn >= 0 ? "+" : ""}{event.avgReturn}%
                </span>
              </span>
              <span className="font-mono text-xs text-muted-foreground">n={event.sampleSize}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function EventFeed() {
  const [filter, setFilter] = useState("All");
  const categories = ["All", ...new Set(marketEvents.map((e) => e.category))];
  const filtered = filter === "All" ? marketEvents : marketEvents.filter((e) => e.category === filter);

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Event Feed</h1>
          <p className="text-sm text-muted-foreground mt-1">Real-time detected market events</p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-2">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setFilter(cat)}
              className={`text-xs px-3 py-1.5 rounded-full transition-colors ${
                filter === cat
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-accent"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Event List */}
        <div className="space-y-3">
          {filtered.map((event) => (
            <EventCard key={event.id} event={event} />
          ))}
        </div>
      </div>
    </AppLayout>
  );
}
