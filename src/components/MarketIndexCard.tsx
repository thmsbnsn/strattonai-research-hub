import { memo } from "react";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";
import type { MarketIndex } from "@/types";

interface MarketIndexCardProps extends MarketIndex {}

export const MarketIndexCard = memo(function MarketIndexCard({ ticker, name, price, change, changePercent }: MarketIndexCardProps) {
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
});
