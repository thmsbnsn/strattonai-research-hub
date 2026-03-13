import { memo, type ReactNode } from "react";

interface StatCardProps {
  label: string;
  value: string;
  color?: string;
  icon?: ReactNode;
}

export const StatCard = memo(function StatCard({ label, value, color = "text-foreground", icon }: StatCardProps) {
  return (
    <div className="terminal-card p-4 text-center">
      {icon && <div className="flex justify-center mb-2">{icon}</div>}
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <p className={`font-mono text-2xl font-bold ${color}`}>{value}</p>
    </div>
  );
});
