import { memo } from "react";
import type { ResearchInsight } from "@/types";

interface InsightCardProps {
  insight: ResearchInsight;
}

export const InsightCard = memo(function InsightCard({ insight }: InsightCardProps) {
  return (
    <div className="p-3 rounded-lg bg-muted/30 border-l-2 border-primary/50">
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
  );
});
