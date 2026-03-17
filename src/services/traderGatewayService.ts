import type {
  AllocationSimulationResult,
  CompanyBriefingPayload,
  LoopRunSummary,
  MarketRegime,
  OrderPreview,
  PennyStockCandidate,
  PortfolioAllocation,
  PortfolioMetrics,
  TradeSimulationResult,
  TransactionCostBreakdown,
} from "@/models";

const DEFAULT_AI_GATEWAY_URL = (import.meta.env.VITE_AI_GATEWAY_URL || "http://127.0.0.1:8787").replace(/\/$/, "");

type GatewayEnvelope<T> = {
  success: boolean;
  data: T;
  error: string | null;
};

type AlpacaAccount = {
  portfolio_value?: string | number;
  cash?: string;
  buying_power?: string;
  equity?: string;
  status?: string;
  mode?: string;
};

type AlpacaPosition = {
  ticker?: string;
  qty?: string;
  market_value?: string;
  avg_entry_price?: string;
  unrealized_pl?: string;
  unrealized_plpc?: string;
  current_price?: string;
  side?: string;
};

function defaultPortfolioMetrics(): PortfolioMetrics {
  return {
    sharpeRatio: 0,
    sortinoRatio: 0,
    maxDrawdown: 0,
    turnover: 0,
    equityCurve: [],
  };
}

async function parseGatewayResponse<T>(response: Response): Promise<T> {
  const payload = (await response.json()) as GatewayEnvelope<T> | T;
  if (payload && typeof payload === "object" && "success" in payload) {
    const envelope = payload as GatewayEnvelope<T>;
    if (!envelope.success) {
      throw new Error(envelope.error || "Gateway request failed.");
    }
    return envelope.data;
  }
  return payload as T;
}

async function fetchGateway<T>(path: string, init?: RequestInit, fallback?: T): Promise<T> {
  try {
    const response = await fetch(`${DEFAULT_AI_GATEWAY_URL}${path}`, init);
    if (!response.ok) {
      throw new Error(`Gateway request failed with status ${response.status}.`);
    }
    return await parseGatewayResponse<T>(response);
  } catch (error) {
    if (fallback !== undefined) {
      return fallback;
    }
    throw error;
  }
}

export async function getPortfolioMetrics() {
  return fetchGateway<PortfolioMetrics>("/portfolio/metrics", undefined, defaultPortfolioMetrics());
}

export async function getCompanyBriefing(ticker: string, tradingMode: "paper" | "live" = "paper") {
  return fetchGateway<CompanyBriefingPayload>(
    `/research/company-briefing?ticker=${encodeURIComponent(ticker.trim().toUpperCase())}&tradingMode=${encodeURIComponent(tradingMode)}`
  );
}

export async function constructPortfolio(method: string, capital: number, signalKeys?: string[]) {
  return fetchGateway<{ runId: string; method: string; capital: number; allocations: PortfolioAllocation[] }>(
    "/portfolio/construct",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ method, capital, signalKeys }),
    }
  );
}

export async function constructPortfolioWithSimulation(
  method: string,
  capital: number,
  signalKeys?: string[],
  dryRun = true
) {
  return fetchGateway<AllocationSimulationResult>("/portfolio/construct", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ method, capital, signalKeys, simulate: true, dryRun }),
  });
}

export async function assessRisk(allocations: Record<string, number>) {
  return fetchGateway<RiskReport>(
    "/risk/assess",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ allocations }),
    }
  );
}

export async function estimateCosts(ticker: string, shares: number, entryPrice?: number) {
  return fetchGateway<TransactionCostBreakdown>(
    "/costs/estimate",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticker, shares, entry_price: entryPrice }),
    }
  );
}

export async function simulateSignalTrade(signalKey: string, capitalAllocation: number, dryRun = false) {
  return fetchGateway<TradeSimulationResult>(
    "/trade/simulate",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ signalKey, capitalAllocation, dryRun, showCosts: true }),
    }
  );
}

export async function getMarketRegime() {
  return fetchGateway<MarketRegime>("/market/regime");
}

export async function getAlpacaAccount() {
  return fetchGateway<AlpacaAccount>(
    "/alpaca/account",
    undefined,
    { cash: "0", buying_power: "0", equity: "0", status: "offline" }
  );
}

export async function getAlpacaPositions() {
  return fetchGateway<AlpacaPosition[]>("/alpaca/positions", undefined, []);
}

export async function getAlpacaOrders(status: "open" | "closed" | "all" = "all") {
  return fetchGateway<Array<Record<string, unknown>>>(`/alpaca/orders?status=${encodeURIComponent(status)}`, undefined, []);
}

export async function getPennyStockCandidates(capital: number, topN = 10) {
  return fetchGateway<PennyStockCandidate[]>(
    `/trading/penny-candidates?capital=${encodeURIComponent(capital)}&topN=${encodeURIComponent(topN)}`,
    undefined,
    []
  );
}

export async function runTradingLoop(request: {
  capital: number;
  universe: "penny" | "main";
  mode: "paper" | "live";
  dryRun: boolean;
  maxPositions?: number;
  maxPositionPct?: number;
}) {
  return fetchGateway<{
    job_id: string;
    dry_run: boolean;
    universe: string;
    capital: number;
  }>(
    "/trading/run-loop",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    }
  );
}

export async function getTradingLoopStatus(jobId: string) {
  return fetchGateway<{ job_id: string; status: string; result: unknown | null; error: string | null }>(
    `/trading/loop-status/${encodeURIComponent(jobId)}`
  );
}

export async function getTradingLoopHistory() {
  return fetchGateway<LoopRunSummary[]>("/trading/loop-history", undefined, []);
}

export async function previewOrder(ticker: string, side: "buy" | "sell", qty: number) {
  return fetchGateway<OrderPreview>("/trading/preview-order", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ticker, side, qty }),
  });
}

export async function getPriceCoverage() {
  return fetchGateway<Array<{ ticker: string; row_count: number }>>("/research/price-coverage", undefined, []);
}

export async function runFillGaps(autoRecompute = true) {
  return fetchGateway<{ job: string; job_id: string }>("/research/fill-gaps", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ auto_recompute: autoRecompute }),
  });
}

export async function getFillGapStatus() {
  return fetchGateway<Record<string, unknown>>("/research/fill-gaps/status", undefined, { job: "idle" });
}

export async function refreshMarketProxies(tickers?: string[]) {
  return fetchGateway<{ job: string; job_id: string }>("/research/refresh-market-proxies", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tickers }),
  });
}

export async function getRefreshMarketProxiesStatus() {
  return fetchGateway<Record<string, unknown>>("/research/refresh-market-proxies/status", undefined, { job: "idle" });
}

export async function getMigrationHealth() {
  return fetchGateway<{
    migrations_checked: string[];
    tables_verified: Record<string, boolean>;
    all_verified: boolean;
  }>("/health/migrations");
}

export async function getFullHealth() {
  return fetchGateway<{ overall: string; checks: Array<{ name: string; status: string; detail: string }> }>("/health/full");
}

export async function getRiskGateLog() {
  return fetchGateway<Array<{ id: string; ticker: string; entryDate: string; hardBlocks: string[] }>>("/risk/gate-log", undefined, []);
}
