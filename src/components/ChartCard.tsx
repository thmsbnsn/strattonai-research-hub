import { memo, type ReactNode } from "react";

interface ChartCardProps {
  title: string;
  children: ReactNode;
  height?: string;
}

export const ChartCard = memo(function ChartCard({ title, children, height = "h-64" }: ChartCardProps) {
  return (
    <div className="terminal-card p-5">
      <h3 className="text-sm font-semibold text-foreground mb-4">{title}</h3>
      <div className={height}>
        {children}
      </div>
    </div>
  );
});
