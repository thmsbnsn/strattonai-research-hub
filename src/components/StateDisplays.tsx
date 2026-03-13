import { AlertCircle } from "lucide-react";

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({ message = "Failed to load data", onRetry }: ErrorStateProps) {
  return (
    <div className="terminal-card p-8 flex flex-col items-center justify-center text-center">
      <AlertCircle className="h-8 w-8 text-danger mb-3" />
      <p className="text-sm text-foreground font-medium mb-1">{message}</p>
      <p className="text-xs text-muted-foreground mb-4">Please try again or check your connection.</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="text-xs bg-primary/10 text-primary px-4 py-2 rounded-lg hover:bg-primary/20 transition-colors"
        >
          Retry
        </button>
      )}
    </div>
  );
}

interface EmptyStateProps {
  title?: string;
  description?: string;
}

export function EmptyState({ title = "No data", description = "Nothing to display yet." }: EmptyStateProps) {
  return (
    <div className="terminal-card p-8 flex flex-col items-center justify-center text-center">
      <p className="text-sm text-foreground font-medium mb-1">{title}</p>
      <p className="text-xs text-muted-foreground">{description}</p>
    </div>
  );
}
