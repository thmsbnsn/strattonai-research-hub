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
    <header className="h-14 border-b border-border bg-card/80 backdrop-blur-sm flex items-center justify-center px-4 relative shrink-0 z-30">
      {/* Mode toggle button — left side */}
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            onClick={onToggle}
            className={`absolute left-4 md:left-6 w-9 h-9 rounded-lg flex items-center justify-center transition-all duration-200 ${
              isTrader
                ? "bg-primary/20 text-primary glow-blue"
                : "bg-muted text-muted-foreground hover:bg-accent hover:text-accent-foreground"
            }`}
            aria-label={`Switch to ${isTrader ? "Research" : "AI Trader"} Dashboard`}
          >
            {isTrader ? <Bot className="h-4 w-4" /> : <FlaskConical className="h-4 w-4" />}
          </button>
        </TooltipTrigger>
        <TooltipContent side="bottom">
          Switch to {isTrader ? "Research" : "AI Trader"} Dashboard
        </TooltipContent>
      </Tooltip>

      {/* Centered brand */}
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-primary/20 flex items-center justify-center">
          <Zap className="h-3.5 w-3.5 text-primary" />
        </div>
        <span className="text-base font-semibold text-foreground tracking-tight">StrattonAI</span>
      </div>

      {/* Mode label — right side */}
      <span className="absolute right-4 md:right-6 text-xs text-muted-foreground font-medium hidden sm:block">
        {isTrader ? "AI Trader" : "Research"}
      </span>
    </header>
  );
}
