import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, TrendingDown, TrendingUp } from "lucide-react";
import { getMarketRegime } from "@/services/traderGatewayService";

function tone(label?: string) {
  switch (label) {
    case "bull_low_vol":
      return "border-emerald-500/30 bg-emerald-500/10 text-emerald-300";
    case "bull_high_vol":
      return "border-amber-500/30 bg-amber-500/10 text-amber-300";
    case "bear":
      return "border-red-500/30 bg-red-500/10 text-red-300";
    default:
      return "border-border bg-muted/40 text-muted-foreground";
  }
}

function icon(label?: string) {
  switch (label) {
    case "bull_low_vol":
    case "bull_high_vol":
      return <TrendingUp className="h-3.5 w-3.5" />;
    case "bear":
      return <TrendingDown className="h-3.5 w-3.5" />;
    default:
      return <AlertTriangle className="h-3.5 w-3.5" />;
  }
}

function labelText(label?: string) {
  if (!label) return "Regime offline";
  return label.replace(/_/g, " ");
}

export function RegimeIndicator() {
  const regimeQuery = useQuery({
    queryKey: ["gateway", "market-regime"],
    queryFn: getMarketRegime,
    retry: 0,
  });

  const regime = regimeQuery.data;

  return (
    <div
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-medium uppercase tracking-[0.14em] ${tone(
        regime?.label
      )}`}
      title={
        regime
          ? `SPY ${regime.spyPrice.toFixed(2)} · 50d ${regime.sma50.toFixed(2)} · 200d ${regime.sma200.toFixed(2)}`
          : "Market regime unavailable"
      }
    >
      {icon(regime?.label)}
      <span>{labelText(regime?.label)}</span>
    </div>
  );
}
