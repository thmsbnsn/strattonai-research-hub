export interface PortfolioEquityPoint {
  date: string;
  cumulativePnl: number;
}

export interface PortfolioMetrics {
  sharpeRatio: number;
  sortinoRatio: number;
  maxDrawdown: number;
  turnover: number;
  equityCurve: PortfolioEquityPoint[];
}

export interface PortfolioAllocation {
  ticker: string;
  allocationDollars: number;
  weight: number;
  method: string;
  signalKey?: string;
}

export interface AllocationSimulationResult {
  runId: string;
  method: string;
  capital: number;
  totalAllocated: number;
  allocations: PortfolioAllocation[];
  simulated: Array<{
    tradeId?: string;
    ticker: string;
    qty: number;
    entryPrice: number;
    netCost: number;
    transactionCostPct: number;
    signalKey?: string;
  }>;
  riskBlocked: Array<{
    ticker: string;
    reason: string;
  }>;
  riskWarnings: string[];
  dryRun: boolean;
}

export interface RiskMetric {
  ticker: string;
  annualizedVol: number | null;
  beta: number | null;
  valueAtRisk95: number | null;
  maxDrawdown: number | null;
  sizeFactor: number | null;
  momentum121: number | null;
  blockedHighVol: boolean;
  sector: string | null;
  weight: number;
}

export interface RiskCluster {
  tickers: string[];
  totalWeight: number;
}

export interface RiskReport {
  totalCapital: number;
  metrics: RiskMetric[];
  correlationMatrix: Record<string, Record<string, number>>;
  sectorExposure: Record<string, number>;
  sectorBreachWarnings: string[];
  clusterWarnings: string[];
  blockedHighVol: string[];
  clusters: RiskCluster[];
}

export interface TransactionCostBreakdown {
  spreadCost: number;
  slippageCost: number;
  liquidityCost: number;
  fees: number;
  totalCostDollars: number;
  totalCostPct: number;
  marketCapBucket: string;
  averageDailyVolume: number;
  averageDailyDollarVolume: number;
}

export interface TradeSimulationResult {
  success: boolean;
  status: string;
  id?: string;
  signalKey: string;
  ticker?: string;
  direction?: "Long" | "Short";
  entryPrice?: number;
  exitPrice?: number;
  shares?: number;
  holdDays?: number;
  grossPnl?: number;
  netPnl?: number;
  costs?: TransactionCostBreakdown | null;
  riskReport?: RiskReport;
  riskGate?: {
    approved: boolean;
    hardBlocks: string[];
    softWarnings: string[];
  };
}

export interface MarketRegime {
  label: "bull_low_vol" | "bull_high_vol" | "bear" | "neutral";
  spyPrice: number;
  sma200: number;
  sma50: number;
  vol20d: number;
  drawdownFromHigh: number;
  asOfDate: string;
}

export interface PennyStockCandidate {
  ticker: string;
  signalType: string;
  score: number;
  entryPrice: number;
  suggestedQty: number;
  estimatedCost: number;
  estimatedCostPct: number;
  confidenceBand: string;
}

export interface OrderPreview {
  ticker: string;
  side: string;
  qty: number;
  estimatedEntryPrice: number;
  estimatedSharesValue: number;
  transactionCost: TransactionCostBreakdown;
  netCostAfterFees: number;
  buyingPowerRemaining: number;
  riskFlags: string[];
  regimeLabel: string;
  approved: boolean;
  rejectionReason: string | null;
}

export interface LoopRunSummary {
  job_id: string;
  timestamp: string;
  mode: string;
  universe: string;
  dry_run: boolean;
  capital: number;
  candidates_evaluated: number;
  orders_previewed: number;
  orders_approved: number;
  orders_rejected: number;
  orders_submitted: number;
  realized_pnl_this_run: number;
  regime: string;
  rejection_reasons: Record<string, number>;
}

export interface BriefingRelationship {
  sourceTicker: string;
  sourceName?: string | null;
  targetTicker: string;
  targetName?: string | null;
  relationshipType: string;
  strength: number;
  counterpartyTicker: string;
  counterpartyName?: string | null;
}

export interface BriefingEvent {
  id: string;
  ticker: string;
  category: string;
  headline: string;
  sentiment: string;
  timestamp: string;
}

export interface BriefingStudySlice {
  studyKey: string;
  studyTargetType: string;
  eventCategory: string;
  primaryTicker?: string | null;
  relatedTicker?: string | null;
  relationshipType?: string | null;
  horizon: string;
  avgReturn: number;
  medianReturn: number;
  winRate: number;
  sampleSize: number;
  notes?: string | null;
  metadata: Record<string, unknown>;
}

export interface BriefingReadinessItem {
  key: string;
  label: string;
  done: boolean;
}

export interface CompanyBriefingPayload {
  ticker: string;
  tradingMode: "paper" | "live";
  profile: {
    ticker: string;
    name: string;
    sector?: string | null;
    industry?: string | null;
    marketCap?: string | null;
    marketCapValue?: number | null;
  };
  latestPrice: {
    close?: number | null;
    tradeDate?: string | null;
    rowCount: number;
  };
  topSignals: Array<{
    id: string;
    signalKey?: string;
    eventCategory: string;
    primaryTicker: string;
    targetTicker: string;
    targetType: "primary" | "related";
    relationshipType?: string | null;
    horizon: string;
    score: number;
    confidenceBand: "Low" | "Moderate" | "High";
    evidenceSummary: string;
    sampleSize: number;
    avgReturn: number;
    medianReturn: number;
    winRate: number;
    originType: "primary" | "explicit" | "inferred";
    rationale?: Record<string, unknown>;
    metadata?: Record<string, unknown>;
  }>;
  recentEvents: BriefingEvent[];
  relationships: BriefingRelationship[];
  studySlices: BriefingStudySlice[];
  eventCategoryCounts: Record<string, number>;
  thesisSummary: string;
  evidenceSummary: string;
  riskFlags: string[];
  readiness: {
    mode: string;
    liveConfirmed: boolean;
    accountStatus: string;
    brokerVerified: boolean;
    hardBlockers: string[];
    items: BriefingReadinessItem[];
  };
  outlook: {
    signalCount: number;
    strongestSignal?: CompanyBriefingPayload["topSignals"][number];
    relatedCompanyCount: number;
    latestEventCategory?: string | null;
  };
}
