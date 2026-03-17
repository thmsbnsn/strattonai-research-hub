export type SettingsDataSourceKey =
  | "supabaseLiveData"
  | "structuredMarketEvents"
  | "secFilings"
  | "mockFallbackMode";

export interface DataSourceSetting {
  key: SettingsDataSourceKey;
  label: string;
  description: string;
  enabled: boolean;
}

export interface ClassificationToggle {
  category: string;
  enabled: boolean;
}

export interface RelationshipMapping {
  id: string;
  company: string;
  related: string;
  type: string;
  strength: number;
  notes?: string;
}

export interface NotificationPreferences {
  eventAlerts: boolean;
  dailyDigest: boolean;
  tradeSignals: boolean;
  weeklyReport: boolean;
}

export interface TradingSettings {
  alpacaMode: "paper" | "live";
  liveTradingConfirmed: boolean;
  startingCapital: number;
  pennyStockUniverseEnabled: boolean;
}

export interface AppSettings {
  version: number;
  updatedAt: string;
  dataSources: DataSourceSetting[];
  classification: ClassificationToggle[];
  relationshipMappings: RelationshipMapping[];
  notifications: NotificationPreferences;
  trading: TradingSettings;
}

export interface SettingsEnvelope {
  settings: AppSettings;
  persistenceMode: "local";
  detail: string;
}
