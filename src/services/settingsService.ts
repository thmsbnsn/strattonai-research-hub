import { buildDefaultClassificationToggles, CANONICAL_EVENT_CATEGORIES } from "@/engine/eventClassifier";
import type {
  AppSettings,
  ClassificationToggle,
  NotificationPreferences,
  RelationshipMapping,
  SettingsDataSourceKey,
  SettingsEnvelope,
  TradingSettings,
} from "@/types";

const SETTINGS_STORAGE_KEY = "strattonai.settings.v1";
const TRADING_SETTINGS_STORAGE_KEY = "strattonai_trading_settings";

const defaultDataSources: AppSettings["dataSources"] = [
  {
    key: "supabaseLiveData",
    label: "Supabase Event Store",
    description: "Controls whether the UI should read live Supabase tables when they are available.",
    enabled: true,
  },
  {
    key: "structuredMarketEvents",
    label: "Structured Market Events",
    description: "Tracks the local market-event ingestion path that feeds normalized event records.",
    enabled: true,
  },
  {
    key: "secFilings",
    label: "SEC Filings (EDGAR)",
    description: "Tracks the structured SEC-filing ingestion path used by the deterministic classifier.",
    enabled: true,
  },
  {
    key: "mockFallbackMode",
    label: "Mock Fallback Mode",
    description: "Keeps the UI functional when live tables are missing, empty, or unavailable.",
    enabled: true,
  },
];

const defaultRelationshipMappings: RelationshipMapping[] = [
  { id: "rel-nvda-tsm", company: "NVDA", related: "TSM", type: "Supplier", strength: 0.9 },
  { id: "rel-nvda-amd", company: "NVDA", related: "AMD", type: "Competitor", strength: 0.85 },
  { id: "rel-nvda-msft", company: "NVDA", related: "MSFT", type: "Customer", strength: 0.8 },
  { id: "rel-aapl-qcom", company: "AAPL", related: "QCOM", type: "Supplier", strength: 0.78 },
  { id: "rel-tsla-rivn", company: "TSLA", related: "RIVN", type: "Competitor", strength: 0.76 },
];

const defaultNotifications: NotificationPreferences = {
  eventAlerts: true,
  dailyDigest: true,
  tradeSignals: false,
  weeklyReport: true,
};

const defaultTrading: TradingSettings = {
  alpacaMode: "paper",
  liveTradingConfirmed: false,
  startingCapital: 1000,
  pennyStockUniverseEnabled: true,
};

const defaultSettings: AppSettings = {
  version: 1,
  updatedAt: new Date().toISOString(),
  dataSources: defaultDataSources,
  classification: buildDefaultClassificationToggles(),
  relationshipMappings: defaultRelationshipMappings,
  notifications: defaultNotifications,
  trading: defaultTrading,
};

function canUseLocalStorage() {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function normalizeTicker(value: string | undefined) {
  return (value || "").trim().toUpperCase();
}

function normalizeRelationshipMappings(mappings: RelationshipMapping[] | undefined) {
  return (mappings ?? [])
    .map((mapping, index) => ({
      id: mapping.id || `relationship-${index + 1}`,
      company: normalizeTicker(mapping.company),
      related: normalizeTicker(mapping.related),
      type: mapping.type?.trim() || "Related",
      strength: typeof mapping.strength === "number" ? Math.min(1, Math.max(0, mapping.strength)) : 0.75,
      notes: mapping.notes?.trim() || undefined,
    }))
    .filter((mapping) => mapping.company && mapping.related);
}

function normalizeClassification(toggles: ClassificationToggle[] | undefined) {
  const enabledByCategory = new Map((toggles ?? []).map((toggle) => [toggle.category, Boolean(toggle.enabled)]));

  return buildDefaultClassificationToggles().map((toggle) => ({
    category: toggle.category,
    enabled: enabledByCategory.get(toggle.category) ?? true,
  }));
}

function normalizeDataSources(settings: AppSettings["dataSources"] | undefined) {
  const enabledByKey = new Map((settings ?? []).map((setting) => [setting.key, Boolean(setting.enabled)]));

  return defaultDataSources.map((setting) => ({
    ...setting,
    enabled: enabledByKey.get(setting.key) ?? setting.enabled,
  }));
}

function normalizeNotifications(value: NotificationPreferences | undefined): NotificationPreferences {
  return {
    eventAlerts: value?.eventAlerts ?? defaultNotifications.eventAlerts,
    dailyDigest: value?.dailyDigest ?? defaultNotifications.dailyDigest,
    tradeSignals: value?.tradeSignals ?? defaultNotifications.tradeSignals,
    weeklyReport: value?.weeklyReport ?? defaultNotifications.weeklyReport,
  };
}

function normalizeTradingSettings(value: TradingSettings | undefined): TradingSettings {
  return {
    alpacaMode: value?.alpacaMode === "live" ? "live" : "paper",
    liveTradingConfirmed: Boolean(value?.liveTradingConfirmed),
    startingCapital:
      typeof value?.startingCapital === "number" && Number.isFinite(value.startingCapital)
        ? Math.max(0, value.startingCapital)
        : defaultTrading.startingCapital,
    pennyStockUniverseEnabled: value?.pennyStockUniverseEnabled ?? defaultTrading.pennyStockUniverseEnabled,
  };
}

export function normalizeSettings(value: Partial<AppSettings> | null | undefined): AppSettings {
  return {
    version: 1,
    updatedAt: value?.updatedAt || new Date().toISOString(),
    dataSources: normalizeDataSources(value?.dataSources),
    classification: normalizeClassification(value?.classification),
    relationshipMappings: normalizeRelationshipMappings(value?.relationshipMappings),
    notifications: normalizeNotifications(value?.notifications),
    trading: normalizeTradingSettings(value?.trading),
  };
}

function readStoredSettings() {
  if (!canUseLocalStorage()) {
    return null;
  }

  try {
    const rawValue = window.localStorage.getItem(SETTINGS_STORAGE_KEY);
    if (!rawValue) {
      return null;
    }

    return JSON.parse(rawValue) as Partial<AppSettings>;
  } catch (error) {
    console.error("[settingsService.readStoredSettings] Failed to parse persisted settings.", error);
    return null;
  }
}

function buildEnvelope(settings: AppSettings): SettingsEnvelope {
  return {
    settings,
    persistenceMode: "local",
    detail: "Persisted locally on this device.",
  };
}

export function readSettingsSnapshot() {
  return normalizeSettings(readStoredSettings() ?? defaultSettings);
}

export async function getSettings(): Promise<SettingsEnvelope> {
  return buildEnvelope(readSettingsSnapshot());
}

export async function saveSettings(settings: AppSettings): Promise<SettingsEnvelope> {
  const normalized = normalizeSettings({
    ...settings,
    updatedAt: new Date().toISOString(),
  });

  if (canUseLocalStorage()) {
    window.localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(normalized));
    window.localStorage.setItem(TRADING_SETTINGS_STORAGE_KEY, JSON.stringify(normalized.trading));
  }

  return buildEnvelope(normalized);
}

export function shouldUseSupabaseLiveData(settings = readSettingsSnapshot()) {
  return settings.dataSources.find((source) => source.key === "supabaseLiveData")?.enabled ?? true;
}

export function isMockFallbackEnabled(settings = readSettingsSnapshot()) {
  return settings.dataSources.find((source) => source.key === "mockFallbackMode")?.enabled ?? true;
}

export function getRelationshipMappings(settings = readSettingsSnapshot()) {
  return normalizeRelationshipMappings(settings.relationshipMappings);
}

export function getEnabledClassificationCategories(settings = readSettingsSnapshot()) {
  const enabledCategories = settings.classification
    .filter((toggle) => toggle.enabled)
    .map((toggle) => toggle.category);

  return enabledCategories.length > 0 ? enabledCategories : [...CANONICAL_EVENT_CATEGORIES];
}

export function readTradingSettingsSnapshot(): TradingSettings {
  if (!canUseLocalStorage()) {
    return normalizeTradingSettings(defaultTrading);
  }

  try {
    const rawValue = window.localStorage.getItem(TRADING_SETTINGS_STORAGE_KEY);
    if (!rawValue) {
      return normalizeTradingSettings(readSettingsSnapshot().trading);
    }
    return normalizeTradingSettings(JSON.parse(rawValue) as TradingSettings);
  } catch {
    return normalizeTradingSettings(readSettingsSnapshot().trading);
  }
}

export function saveTradingSettings(settings: TradingSettings) {
  const normalized = normalizeTradingSettings(settings);
  if (canUseLocalStorage()) {
    window.localStorage.setItem(TRADING_SETTINGS_STORAGE_KEY, JSON.stringify(normalized));
    const base = readSettingsSnapshot();
    window.localStorage.setItem(
      SETTINGS_STORAGE_KEY,
      JSON.stringify(
        normalizeSettings({
          ...base,
          updatedAt: new Date().toISOString(),
          trading: normalized,
        })
      )
    );
  }
  return normalized;
}

export function updateDataSourceToggle(
  settings: AppSettings,
  key: SettingsDataSourceKey,
  enabled: boolean
) {
  return {
    ...settings,
    dataSources: settings.dataSources.map((source) =>
      source.key === key ? { ...source, enabled } : source
    ),
  } satisfies AppSettings;
}
