import { FlaskConical, Bot } from "lucide-react";
import type { DashboardMode } from "@/hooks/useDashboardMode";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

interface AppHeaderProps {
  mode: DashboardMode;
  onToggle: () => void;
}

export function AppHeader({ mode, onToggle }: AppHeaderProps) {
  const isTrader = mode === "trader";

  return (
    <header className="h-12 border-b border-border bg-card/80 backdrop-blur-sm px-4 md:px-6 shrink-0 z-30">
      <div className="grid h-full grid-cols-[1fr_auto_1fr] items-center gap-3">
        <div className="justify-self-start text-[11px] text-muted-foreground font-medium tracking-wide uppercase hidden sm:block">
          {isTrader ? "AI Trader Mode" : "Research Mode"}
        </div>

        <div className="flex items-center justify-center gap-2.5">
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                onClick={onToggle}
                className={`h-8 w-8 rounded-lg border flex items-center justify-center transition-all duration-200 ${
                  isTrader
                    ? "border-primary/40 bg-primary/15 shadow-[0_0_18px_rgba(59,130,246,0.16)]"
                    : "border-border bg-muted/50 hover:bg-accent"
                }`}
                aria-label={`Switch to ${isTrader ? "Research" : "AI Trader"} Dashboard`}
              >
                <img src="/logo.svg" alt="StrattonAI" className="h-[18px] w-[18px] object-contain" />
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

        <div className="justify-self-end hidden sm:flex items-center gap-1.5 text-[11px] text-muted-foreground font-medium tracking-wide uppercase">
          {isTrader ? (
            <>
              <Bot className="h-3.5 w-3.5 text-primary" />
              <span>AI Trader</span>
            </>
          ) : (
            <>
              <FlaskConical className="h-3.5 w-3.5 text-primary" />
              <span>Research</span>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
