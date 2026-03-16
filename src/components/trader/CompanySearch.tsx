import { useState, useCallback } from "react";
import { Search } from "lucide-react";

interface CompanySearchProps {
  onSearch: (query: string) => void;
}

export function CompanySearch({ onSearch }: CompanySearchProps) {
  const [query, setQuery] = useState("");

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (query.trim()) onSearch(query.trim().toUpperCase());
    },
    [query, onSearch],
  );

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2 w-full max-w-lg">
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search company name or ticker…"
          className="w-full h-9 pl-9 pr-3 rounded-lg bg-muted/50 border border-border text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
        />
      </div>
      <button
        type="submit"
        className="h-9 px-4 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
      >
        Search
      </button>
    </form>
  );
}
