import { useState } from "react";
import { ChevronDown, ChevronUp, BookOpen } from "lucide-react";
import { journalEntries } from "@/lib/mockData";
import { AppLayout } from "@/components/AppLayout";

function JournalCard({ entry }: { entry: typeof journalEntries[0] }) {
  const [expanded, setExpanded] = useState(false);

  const confidenceColor = {
    High: "bg-success/10 text-success",
    Moderate: "bg-warning/10 text-warning",
    Low: "bg-danger/10 text-danger",
  };

  return (
    <div className="terminal-card">
      <div
        className="p-4 cursor-pointer flex items-start gap-3"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="shrink-0 mt-0.5">
          <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
            <BookOpen className="h-4 w-4 text-primary" />
          </div>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-xs text-muted-foreground">{entry.date}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full ${confidenceColor[entry.confidence]}`}>
              {entry.confidence}
            </span>
          </div>
          <h3 className="text-sm font-medium text-foreground">{entry.title}</h3>
        </div>
        <button className="shrink-0 text-muted-foreground">
          {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
      </div>

      {expanded && (
        <div className="px-4 pb-4 space-y-3 animate-slide-in border-t border-border pt-3 ml-11">
          <div>
            <h4 className="text-xs font-semibold text-foreground mb-1.5">Detected Events</h4>
            <ul className="space-y-1">
              {entry.events.map((e, i) => (
                <li key={i} className="text-xs text-muted-foreground flex items-start gap-2">
                  <span className="text-primary mt-0.5">•</span> {e}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-semibold text-foreground mb-1.5">Observed Patterns</h4>
            <p className="text-xs text-muted-foreground leading-relaxed">{entry.patterns}</p>
          </div>

          <div className="bg-muted/30 rounded-lg p-3 border-l-2 border-primary/50">
            <h4 className="text-xs font-semibold text-foreground mb-1">Hypothesis</h4>
            <p className="text-xs text-muted-foreground leading-relaxed italic">{entry.hypothesis}</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ResearchJournal() {
  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Research Journal</h1>
          <p className="text-sm text-muted-foreground mt-1">Chronological log of detected patterns and hypotheses</p>
        </div>

        <div className="space-y-3">
          {journalEntries.map((entry) => (
            <JournalCard key={entry.id} entry={entry} />
          ))}
        </div>
      </div>
    </AppLayout>
  );
}
