import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Save, Plus, X } from "lucide-react";
import { AppLayout } from "@/components/AppLayout";
import { DataSourceStatusBadge } from "@/components/DataSourceStatusBadge";
import { CardSkeleton } from "@/components/LoadingSkeletons";
import { ErrorState } from "@/components/StateDisplays";
import { toast } from "@/components/ui/sonner";
import type { AppSettings, RelationshipMapping, SettingsDataSourceKey } from "@/types";
import {
  getFillGapStatus,
  getMigrationHealth,
  getPriceCoverage,
  getRefreshMarketProxiesStatus,
  refreshMarketProxies,
  runFillGaps,
} from "@/services/traderGatewayService";
import {
  getSettings,
  saveSettings,
  updateDataSourceToggle,
} from "@/services/settingsService";

const relationshipTypeOptions = [
  "Supplier",
  "Competitor",
  "Customer",
  "Sector Peer",
  "Partner",
  "Regulatory Peer",
] as const;

function cloneSettings(settings: AppSettings): AppSettings {
  return JSON.parse(JSON.stringify(settings)) as AppSettings;
}

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const settingsQuery = useQuery({ queryKey: ["settings"], queryFn: getSettings });
  const [draft, setDraft] = useState<AppSettings | null>(null);
  const [isDirty, setIsDirty] = useState(false);
  const loadedUpdatedAt = settingsQuery.data?.settings.updatedAt;
  const priceCoverageQuery = useQuery({ queryKey: ["gateway", "price-coverage"], queryFn: getPriceCoverage, retry: 0 });
  const migrationHealthQuery = useQuery({ queryKey: ["gateway", "migration-health"], queryFn: getMigrationHealth, retry: 0 });
  const fillGapStatusQuery = useQuery({ queryKey: ["gateway", "fill-gap-status"], queryFn: getFillGapStatus, retry: 0 });
  const refreshProxiesStatusQuery = useQuery({ queryKey: ["gateway", "refresh-proxies-status"], queryFn: getRefreshMarketProxiesStatus, retry: 0 });

  useEffect(() => {
    if (!settingsQuery.data) {
      return;
    }

    if (!draft || (!isDirty && draft.updatedAt !== settingsQuery.data.settings.updatedAt)) {
      setDraft(cloneSettings(settingsQuery.data.settings));
    }
  }, [draft, isDirty, loadedUpdatedAt, settingsQuery.data]);

  const saveMutation = useMutation({
    mutationFn: saveSettings,
    onSuccess: (result) => {
      queryClient.setQueryData(["settings"], result);
      queryClient.invalidateQueries({ queryKey: ["dashboard", "data-source-status"] });
      queryClient.invalidateQueries({ queryKey: ["events"] });
      queryClient.invalidateQueries({ queryKey: ["events", "categories"] });
      queryClient.invalidateQueries({ queryKey: ["company", "relationships"] });
      queryClient.invalidateQueries({ queryKey: ["research", "journal"] });
      setDraft(cloneSettings(result.settings));
      setIsDirty(false);
      toast.success("Settings saved", { description: result.detail });
    },
    onError: () => {
      toast.error("Failed to save settings", {
        description: "The Settings page could not persist your changes.",
      });
    },
  });
  const fillGapsMutation = useMutation({
    mutationFn: () => runFillGaps(true),
    onSuccess: () => {
      toast.success("Gap fill job started");
      fillGapStatusQuery.refetch();
    },
    onError: (error) => {
      toast.error("Gap fill failed to start", { description: error instanceof Error ? error.message : "Gateway request failed." });
    },
  });
  const refreshProxiesMutation = useMutation({
    mutationFn: () => refreshMarketProxies(),
    onSuccess: () => {
      toast.success("Market proxy refresh started");
      refreshProxiesStatusQuery.refetch();
      queryClient.invalidateQueries({ queryKey: ["gateway", "price-coverage"] });
    },
    onError: (error) => {
      toast.error("Proxy refresh failed to start", { description: error instanceof Error ? error.message : "Gateway request failed." });
    },
  });

  const hasUnsavedChanges = useMemo(() => {
    if (!draft || !settingsQuery.data) {
      return false;
    }

    return JSON.stringify(draft) !== JSON.stringify(settingsQuery.data.settings);
  }, [draft, settingsQuery.data]);

  const updateDraft = (updater: (current: AppSettings) => AppSettings) => {
    setDraft((current) => {
      if (!current) {
        return current;
      }

      const next = updater(current);
      setIsDirty(true);
      return next;
    });
  };

  const toggleDataSource = (key: SettingsDataSourceKey) => {
    if (!draft) {
      return;
    }

    const currentValue = draft.dataSources.find((source) => source.key === key)?.enabled ?? false;
    updateDraft((current) => updateDataSourceToggle(current, key, !currentValue));
  };

  const toggleClassification = (category: string) => {
    if (!draft) {
      return;
    }

    const enabledCount = draft.classification.filter((toggle) => toggle.enabled).length;
    const currentToggle = draft.classification.find((toggle) => toggle.category === category);

    if (currentToggle?.enabled && enabledCount === 1) {
      toast.error("One category must remain enabled", {
        description: "Event filters and studies need at least one active classification category.",
      });
      return;
    }

    updateDraft((current) => ({
      ...current,
      classification: current.classification.map((toggle) =>
        toggle.category === category ? { ...toggle, enabled: !toggle.enabled } : toggle
      ),
    }));
  };

  const addRelationship = () => {
    updateDraft((current) => ({
      ...current,
      relationshipMappings: [
        ...current.relationshipMappings,
        {
          id: crypto.randomUUID(),
          company: "",
          related: "",
          type: "Supplier",
          strength: 0.75,
        },
      ],
    }));
  };

  const removeRelationship = (id: string) => {
    updateDraft((current) => ({
      ...current,
      relationshipMappings: current.relationshipMappings.filter((relationship) => relationship.id !== id),
    }));
  };

  const updateRelationship = (id: string, field: keyof RelationshipMapping, value: string) => {
    updateDraft((current) => ({
      ...current,
      relationshipMappings: current.relationshipMappings.map((relationship) =>
        relationship.id === id
          ? {
              ...relationship,
              [field]: field === "company" || field === "related" ? value.toUpperCase() : value,
            }
          : relationship
      ),
    }));
  };

  const toggleNotification = (key: keyof AppSettings["notifications"]) => {
    updateDraft((current) => ({
      ...current,
      notifications: {
        ...current.notifications,
        [key]: !current.notifications[key],
      },
    }));
  };

  const handleSave = () => {
    if (!draft) {
      return;
    }

    saveMutation.mutate(draft);
  };

  if (settingsQuery.isLoading || !draft) {
    return (
      <AppLayout>
        <div className="space-y-4 max-w-3xl">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
      </AppLayout>
    );
  }

  if (settingsQuery.isError) {
    return (
      <AppLayout>
        <ErrorState
          message="Failed to load settings"
          onRetry={() => settingsQuery.refetch()}
        />
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="space-y-6 max-w-3xl">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Settings</h1>
          <p className="text-sm text-muted-foreground mt-1">Configure data sources, classifications, and preferences</p>
          <div className="mt-3 inline-flex items-center gap-2 rounded-full border border-border bg-muted/40 px-3 py-1 text-xs text-muted-foreground">
            <span className="font-medium text-foreground">Persistence:</span>
            <span>{settingsQuery.data?.detail ?? "Persisted locally on this device."}</span>
          </div>
        </div>

        <div className="terminal-card p-5">
          <div className="mb-4 flex flex-col gap-3">
            <h3 className="text-sm font-semibold text-foreground">Data Sources</h3>
            <DataSourceStatusBadge />
          </div>
          <div className="space-y-3">
            {draft.dataSources.map((source) => (
              <div key={source.key} className="flex items-center justify-between gap-4 p-3 rounded-lg bg-muted/30">
                <div className="min-w-0">
                  <p className="text-sm text-foreground">{source.label}</p>
                  <p className="text-xs text-muted-foreground">{source.description}</p>
                </div>
                <button
                  type="button"
                  onClick={() => toggleDataSource(source.key)}
                  className={`w-10 h-5 rounded-full flex items-center transition-colors ${
                    source.enabled ? "bg-primary justify-end" : "bg-muted justify-start"
                  }`}
                  aria-label={`Toggle ${source.label}`}
                >
                  <span className="w-4 h-4 rounded-full bg-foreground mx-0.5" />
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="terminal-card p-5">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-semibold text-foreground">Price Coverage</h3>
              <p className="text-xs text-muted-foreground mt-1">Event tickers mapped against live `daily_prices` row counts and migration health.</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => refreshProxiesMutation.mutate()}
                disabled={refreshProxiesMutation.isPending}
                className="rounded-md border border-border px-3 py-2 text-xs font-medium text-foreground hover:bg-muted/60 disabled:opacity-60"
              >
                Refresh Proxies
              </button>
              <button
                onClick={() => fillGapsMutation.mutate()}
                disabled={fillGapsMutation.isPending}
                className="rounded-md bg-primary px-3 py-2 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
              >
                Fill Gaps
              </button>
            </div>
          </div>
          <div className="mb-3 text-xs text-muted-foreground space-y-1">
            <div>Migrations: {migrationHealthQuery.data?.all_verified ? "verified" : "pending"} · Gap status: {String(fillGapStatusQuery.data?.job ?? "idle")}</div>
            <div>Proxy refresh: {String(refreshProxiesStatusQuery.data?.job ?? "idle")}</div>
          </div>
          <div className="space-y-2">
            {(priceCoverageQuery.data ?? []).slice(0, 20).map((row) => (
              <div key={row.ticker} className="flex items-center justify-between rounded-md bg-muted/30 px-3 py-2 text-xs">
                <span className="font-mono text-foreground">{row.ticker}</span>
                <span
                  className={`rounded-full px-2 py-0.5 ${
                    row.row_count >= 252 ? "bg-success/10 text-success" : row.row_count >= 60 ? "bg-warning/10 text-warning" : "bg-danger/10 text-danger"
                  }`}
                >
                  {row.row_count} rows
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="terminal-card p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">Event Classification</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {draft.classification.map((toggle) => (
              <label key={toggle.category} className="flex items-center gap-2 p-2 rounded-lg bg-muted/30 cursor-pointer">
                <input
                  type="checkbox"
                  checked={toggle.enabled}
                  onChange={() => toggleClassification(toggle.category)}
                  className="rounded border-border accent-primary"
                />
                <span className="text-xs text-foreground">{toggle.category}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="terminal-card p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-foreground">Relationship Mapping</h3>
              <p className="text-xs text-muted-foreground mt-1">Saved mappings are merged into the company graph immediately after save.</p>
            </div>
            <button
              onClick={addRelationship}
              className="flex items-center gap-1 text-xs bg-primary/10 text-primary px-3 py-1.5 rounded-lg hover:bg-primary/20 transition-colors"
            >
              <Plus className="h-3 w-3" /> Add
            </button>
          </div>
          <div className="space-y-2">
            {draft.relationshipMappings.map((relationship) => (
              <div key={relationship.id} className="flex items-center gap-2">
                <input
                  value={relationship.company}
                  onChange={(event) => updateRelationship(relationship.id, "company", event.target.value)}
                  placeholder="Company"
                  className="flex-1 bg-muted border border-border rounded-md px-2 py-1.5 text-xs text-foreground font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                />
                <span className="text-xs text-muted-foreground">→</span>
                <input
                  value={relationship.related}
                  onChange={(event) => updateRelationship(relationship.id, "related", event.target.value)}
                  placeholder="Related"
                  className="flex-1 bg-muted border border-border rounded-md px-2 py-1.5 text-xs text-foreground font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                />
                <select
                  value={relationship.type}
                  onChange={(event) => updateRelationship(relationship.id, "type", event.target.value)}
                  className="bg-muted border border-border rounded-md px-2 py-1.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  {relationshipTypeOptions.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
                <button
                  onClick={() => removeRelationship(relationship.id)}
                  className="text-muted-foreground hover:text-danger transition-colors p-1"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="terminal-card p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">Notification Preferences</h3>
          <div className="space-y-3">
            {Object.entries(draft.notifications).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                <span className="text-sm text-foreground capitalize">
                  {key.replace(/([A-Z])/g, " $1").trim()}
                </span>
                <button
                  type="button"
                  onClick={() => toggleNotification(key as keyof AppSettings["notifications"])}
                  className={`w-10 h-5 rounded-full flex items-center transition-colors ${
                    value ? "bg-primary justify-end" : "bg-muted justify-start"
                  }`}
                  aria-label={`Toggle ${key}`}
                >
                  <span className="w-4 h-4 rounded-full bg-foreground mx-0.5" />
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="terminal-card p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">Trading</h3>
          <div className="space-y-4">
            <div className="grid gap-3 md:grid-cols-2">
              <label className="rounded-lg bg-muted/30 p-3">
                <span className="mb-2 block text-xs text-muted-foreground">Alpaca Mode</span>
                <div className="flex gap-2">
                  {(["paper", "live"] as const).map((mode) => (
                    <button
                      key={mode}
                      type="button"
                      onClick={() =>
                        updateDraft((current) => ({
                          ...current,
                          trading: {
                            ...current.trading,
                            alpacaMode: mode,
                          },
                        }))
                      }
                      className={`rounded-md px-3 py-2 text-xs font-medium ${
                        draft.trading.alpacaMode === mode
                          ? mode === "paper"
                            ? "bg-primary text-primary-foreground"
                            : "bg-danger text-white"
                          : "bg-background/50 text-muted-foreground"
                      }`}
                    >
                      {mode === "paper" ? "Paper" : "Live"}
                    </button>
                  ))}
                </div>
              </label>

              <label className="rounded-lg bg-muted/30 p-3">
                <span className="mb-2 block text-xs text-muted-foreground">Starting Capital</span>
                <input
                  type="number"
                  min={0}
                  step={10}
                  value={draft.trading.startingCapital}
                  onChange={(event) =>
                    updateDraft((current) => ({
                      ...current,
                      trading: {
                        ...current.trading,
                        startingCapital: Number(event.target.value) || 0,
                      },
                    }))
                  }
                  className="w-full rounded-md border border-border bg-background/50 px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </label>
            </div>

            <label className="flex items-start gap-3 rounded-lg bg-muted/30 p-3">
              <input
                type="checkbox"
                checked={draft.trading.liveTradingConfirmed}
                onChange={() =>
                  updateDraft((current) => ({
                    ...current,
                    trading: {
                      ...current.trading,
                      liveTradingConfirmed: !current.trading.liveTradingConfirmed,
                    },
                  }))
                }
                className="mt-0.5 rounded border-border accent-primary"
              />
              <span className="text-sm text-foreground">
                I understand this uses real money. Starting capital is limited to the amount I deposited.
              </span>
            </label>

            <div className="flex items-center justify-between rounded-lg bg-muted/30 p-3">
              <div>
                <p className="text-sm text-foreground">Penny Stock Universe</p>
                <p className="text-xs text-muted-foreground">Enables the separate Alpaca-backed penny-stock sandbox.</p>
              </div>
              <button
                type="button"
                onClick={() =>
                  updateDraft((current) => ({
                    ...current,
                    trading: {
                      ...current.trading,
                      pennyStockUniverseEnabled: !current.trading.pennyStockUniverseEnabled,
                    },
                  }))
                }
                className={`w-10 h-5 rounded-full flex items-center transition-colors ${
                  draft.trading.pennyStockUniverseEnabled ? "bg-primary justify-end" : "bg-muted justify-start"
                }`}
                aria-label="Toggle penny stock universe"
              >
                <span className="w-4 h-4 rounded-full bg-foreground mx-0.5" />
              </button>
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={handleSave}
          disabled={!hasUnsavedChanges || saveMutation.isPending}
          className="flex items-center gap-2 bg-primary text-primary-foreground px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:cursor-not-allowed disabled:opacity-60"
        >
          <Save className="h-4 w-4" />
          {saveMutation.isPending ? "Saving..." : "Save Settings"}
        </button>
      </div>
    </AppLayout>
  );
}
