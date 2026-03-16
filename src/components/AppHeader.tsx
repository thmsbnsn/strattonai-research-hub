import { Zap, FlaskConical, Bot } from "lucide-react";
import type { DashboardMode } from "@/hooks/useDashboardMode";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

interface AppHeaderProps {
  mode: DashboardMode;
  onToggle: () => void;
}

export function AppHeader({ mode, onToggle }: AppHeaderProps) {
  const isTrader = mode === "trader";

  return (
    <header className="h-12 border-b border-border bg-card/80 backdrop-blur-sm flex items-center justify-center px-4 relative shrink-0 z-30">
      {/* Centered brand — icon is the mode toggle */}
      <div className="flex items-center gap-2.5">
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              onClick={onToggle}
              className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-200 ${
                isTrader
                  ? "bg-primary/20 text-primary glow-blue"
                  : "bg-muted/60 text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              }`}
              aria-label={`Switch to ${isTrader ? "Research" : "AI Trader"} Dashboard`}
            >
              {isTrader ? <Bot className="h-4 w-4" /> : <FlaskConical className="h-4 w-4" />}
            </button>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="text-xs">
            Switch to {isTrader ? "Research" : "AI Trader"} Dashboard
          </TooltipContent>
        </Tooltip>

        <span className="text-sm font-semibold text-foreground tracking-tight select-none">
          StrattonAI
        </span>
      </div>

      {/* Mode label — right side */}
      <span className="absolute right-4 md:right-6 text-[11px] text-muted-foreground font-medium tracking-wide uppercase hidden sm:block">
        {isTrader ? "AI Trader" : "Research"}
      </span>
    </header>
  );
}
