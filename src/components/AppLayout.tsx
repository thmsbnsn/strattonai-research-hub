import { ReactNode } from "react";
import { AppSidebar } from "@/components/AppSidebar";
import { AppHeader } from "@/components/AppHeader";
import { useDashboardMode } from "@/hooks/useDashboardMode";
import type { DashboardMode } from "@/hooks/useDashboardMode";

interface AppLayoutProps {
  children: ReactNode | ((mode: DashboardMode) => ReactNode);
}

export function AppLayout({ children }: AppLayoutProps) {
  const { mode, toggle } = useDashboardMode();

  return (
    <div className="flex flex-col min-h-screen w-full bg-background">
      <AppHeader mode={mode} onToggle={toggle} />
      <div className="flex flex-1 min-h-0">
        <AppSidebar />
        <main className="flex-1 min-w-0 overflow-auto">
          <div className="p-4 md:p-6 lg:p-8 max-w-[1600px] mx-auto">
            {typeof children === "function" ? children(mode) : children}
          </div>
        </main>
      </div>
    </div>
  );
}
