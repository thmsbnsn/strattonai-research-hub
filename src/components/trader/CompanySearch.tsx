import { useCallback, useDeferredValue, useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { searchCompanies } from "@/services/companyService";

interface CompanySearchProps {
  onSearch: (query: string) => void;
  initialQuery?: string;
}

export function CompanySearch({ onSearch, initialQuery = "" }: CompanySearchProps) {
  const [query, setQuery] = useState(initialQuery);
  const trimmedQuery = query.trim();
  const deferredQuery = useDeferredValue(trimmedQuery);

  useEffect(() => {
    setQuery(initialQuery);
  }, [initialQuery]);

  const suggestionsQuery = useQuery({
    queryKey: ["companies", "search", deferredQuery],
    queryFn: () => searchCompanies(deferredQuery),
    enabled: deferredQuery.length > 0,
  });

  const suggestions = useMemo(() => suggestionsQuery.data ?? [], [suggestionsQuery.data]);
  const shouldShowSuggestions =
    trimmedQuery.length > 0 &&
    !(
      suggestions.length === 1 &&
      suggestions[0].ticker.toUpperCase() === trimmedQuery.toUpperCase()
    );

  const submitTicker = useCallback(
    (ticker: string) => {
      const normalizedTicker = ticker.trim().toUpperCase();
      if (!normalizedTicker) {
        return;
      }

      setQuery(normalizedTicker);
      onSearch(normalizedTicker);
    },
    [onSearch]
  );

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!trimmedQuery) {
        return;
      }

      const exactSuggestion = suggestions.find((suggestion) => {
        const normalizedTicker = suggestion.ticker.toUpperCase();
        const normalizedName = suggestion.name.toUpperCase();
        const normalizedQuery = trimmedQuery.toUpperCase();

        return normalizedTicker === normalizedQuery || normalizedName === normalizedQuery;
      });

      if (exactSuggestion) {
        submitTicker(exactSuggestion.ticker);
        return;
      }

      const freshSuggestions = await searchCompanies(trimmedQuery);
      if (freshSuggestions[0]) {
        submitTicker(freshSuggestions[0].ticker);
        return;
      }

      submitTicker(trimmedQuery);
    },
    [submitTicker, suggestions, trimmedQuery]
  );

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl">
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search company name or ticker…"
          className="w-full h-9 pl-9 pr-3 rounded-lg bg-muted/50 border border-border text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          aria-label="Search company name or ticker"
        />
        </div>
        <button
          type="submit"
          className="h-9 px-4 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          Search
        </button>
      </div>

      {shouldShowSuggestions ? (
        <div className="mt-2 rounded-lg border border-border bg-card/70 p-2">
          {suggestionsQuery.isLoading ? (
            <p className="px-2 py-1 text-xs text-muted-foreground">Searching companies...</p>
          ) : suggestions.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {suggestions.slice(0, 6).map((suggestion) => (
                <button
                  key={suggestion.ticker}
                  type="button"
                  onClick={() => submitTicker(suggestion.ticker)}
                  className="rounded-md border border-border bg-muted/40 px-2.5 py-1.5 text-left hover:bg-accent transition-colors"
                >
                  <span className="block font-mono text-xs font-semibold text-foreground">
                    {suggestion.ticker}
                  </span>
                  <span className="block text-[11px] text-muted-foreground">
                    {suggestion.name}
                  </span>
                </button>
              ))}
            </div>
          ) : (
            <p className="px-2 py-1 text-xs text-muted-foreground">
              No direct company match found. Press Search to use the typed ticker.
            </p>
          )}
        </div>
      ) : null}
    </form>
  );
}
