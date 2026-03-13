import { Skeleton } from "@/components/ui/skeleton";

export function CardSkeleton({ className = "" }: { className?: string }) {
  return (
    <div className={`terminal-card p-4 space-y-3 ${className}`}>
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-8 w-1/2" />
      <Skeleton className="h-3 w-2/3" />
    </div>
  );
}

export function ChartSkeleton({ className = "" }: { className?: string }) {
  return (
    <div className={`terminal-card p-5 ${className}`}>
      <Skeleton className="h-4 w-1/4 mb-4" />
      <Skeleton className="h-64 w-full rounded-lg" />
    </div>
  );
}

export function ListSkeleton({ count = 3, className = "" }: { count?: number; className?: string }) {
  return (
    <div className={`space-y-3 ${className}`}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="terminal-card p-4 space-y-2">
          <div className="flex items-center gap-3">
            <Skeleton className="h-6 w-12 rounded" />
            <Skeleton className="h-4 w-3/4" />
          </div>
          <Skeleton className="h-3 w-1/2" />
        </div>
      ))}
    </div>
  );
}

export function TableSkeleton({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div className="terminal-card p-5 space-y-3">
      <Skeleton className="h-4 w-1/4 mb-4" />
      <div className="space-y-2">
        {Array.from({ length: rows }).map((_, r) => (
          <div key={r} className="flex gap-4">
            {Array.from({ length: cols }).map((_, c) => (
              <Skeleton key={c} className="h-4 flex-1" />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
