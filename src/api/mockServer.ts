import type {
  MarketIndex, SectorPerformance, VolatilityData, PricePoint, EventMarker,
  MarketEvent, EventStudyResult, ReturnDistributionPoint, ForwardCurvePoint,
  CompanyProfile, CompanyRelationship,
  ResearchInsight, JournalEntry,
  PaperTrade, PortfolioPerformancePoint, SignalScore,
} from "@/types";

// Simulate network latency
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));
const LATENCY = 300;

// ── Mock Data ──────────────────────────────────────────

const marketIndexes: MarketIndex[] = [
  { ticker: "SPY", name: "S&P 500", price: 5248.32, change: 0.87, changePercent: 0.42 },
  { ticker: "QQQ", name: "NASDAQ 100", price: 18432.15, change: 156.23, changePercent: 0.86 },
  { ticker: "DIA", name: "Dow Jones", price: 39782.40, change: -42.18, changePercent: -0.11 },
];

const sectorPerformance: SectorPerformance[] = [
  { name: "Technology", change: 1.24, value: 85 },
  { name: "Healthcare", change: 0.67, value: 72 },
  { name: "Financials", change: -0.32, value: 45 },
  { name: "Energy", change: -1.15, value: 28 },
  { name: "Consumer Disc.", change: 0.45, value: 62 },
  { name: "Industrials", change: 0.18, value: 55 },
  { name: "Materials", change: -0.56, value: 38 },
  { name: "Utilities", change: 0.92, value: 68 },
  { name: "Real Estate", change: -0.78, value: 32 },
  { name: "Comm. Services", change: 1.56, value: 90 },
  { name: "Consumer Staples", change: 0.12, value: 52 },
];

const volatilityData: VolatilityData = { vix: 16.42, change: -0.83, trend: "declining" };

const marketEvents: MarketEvent[] = [
  {
    id: "1",
    headline: "NVIDIA announces next-gen AI training chips with 2x performance",
    ticker: "NVDA",
    category: "Product Launch",
    sentiment: "positive",
    timestamp: "2026-03-13T08:32:00Z",
    relatedCompanies: [
      { ticker: "TSM", name: "Taiwan Semi", relationship: "Supplier" },
      { ticker: "AMD", name: "AMD", relationship: "Competitor" },
      { ticker: "AVGO", name: "Broadcom", relationship: "Sector Peer" },
    ],
    historicalAnalog: "12 similar events detected. Supplier stocks averaged +1.8% return over 5 days.",
    sampleSize: 12,
    avgReturn: 1.8,
    details: "NVIDIA unveiled its Blackwell Ultra architecture at GTC 2026, featuring 2x training performance improvements. The new B300 chips are expected to ship Q3 2026. Major cloud providers have already placed advance orders.",
  },
  {
    id: "2",
    headline: "FDA approves Eli Lilly's new weight loss drug for expanded indications",
    ticker: "LLY",
    category: "Regulatory Approval",
    sentiment: "positive",
    timestamp: "2026-03-13T07:15:00Z",
    relatedCompanies: [
      { ticker: "NVO", name: "Novo Nordisk", relationship: "Competitor" },
      { ticker: "AMGN", name: "Amgen", relationship: "Competitor" },
    ],
    historicalAnalog: "8 similar FDA approvals detected. Primary company averaged +3.2% over 3 days.",
    sampleSize: 8,
    avgReturn: 3.2,
    details: "FDA granted expanded approval for tirzepatide for cardiovascular risk reduction in obese patients. This broadens the addressable market significantly.",
  },
  {
    id: "3",
    headline: "Tesla reports production halt at Shanghai Gigafactory due to supply chain issues",
    ticker: "TSLA",
    category: "Supply Disruption",
    sentiment: "negative",
    timestamp: "2026-03-13T06:45:00Z",
    relatedCompanies: [
      { ticker: "RIVN", name: "Rivian", relationship: "Competitor" },
      { ticker: "PANW", name: "Panasonic", relationship: "Supplier" },
    ],
    historicalAnalog: "15 similar disruptions detected. Stock averaged -2.1% over 5 days, competitors +0.5%.",
    sampleSize: 15,
    avgReturn: -2.1,
  },
  {
    id: "4",
    headline: "Microsoft announces $10B AI infrastructure investment in Southeast Asia",
    ticker: "MSFT",
    category: "Capital Expenditure",
    sentiment: "positive",
    timestamp: "2026-03-13T05:20:00Z",
    relatedCompanies: [
      { ticker: "GOOGL", name: "Alphabet", relationship: "Competitor" },
      { ticker: "AMZN", name: "Amazon", relationship: "Competitor" },
      { ticker: "ORCL", name: "Oracle", relationship: "Sector Peer" },
    ],
    historicalAnalog: "6 similar capex announcements. Stock averaged +0.8% over 10 days.",
    sampleSize: 6,
    avgReturn: 0.8,
  },
  {
    id: "5",
    headline: "Apple loses antitrust case in EU, faces $4.5B fine",
    ticker: "AAPL",
    category: "Legal/Regulatory",
    sentiment: "negative",
    timestamp: "2026-03-12T18:30:00Z",
    relatedCompanies: [
      { ticker: "GOOGL", name: "Alphabet", relationship: "Sector Peer" },
      { ticker: "META", name: "Meta", relationship: "Sector Peer" },
    ],
    historicalAnalog: "9 similar antitrust rulings. Stock averaged -1.4% over 3 days, recovered by day 10.",
    sampleSize: 9,
    avgReturn: -1.4,
  },
];

const researchInsights: ResearchInsight[] = [
  { id: "1", title: "AI Chip Supply Chain Pattern", summary: "Supplier stocks outperform by +1.8% avg within 5 days of major chip announcements.", confidence: "High", eventCount: 12 },
  { id: "2", title: "FDA Approval Momentum", summary: "Pharma stocks show sustained momentum for 10 days post-approval. Competitors show mild weakness.", confidence: "Moderate", eventCount: 8 },
  { id: "3", title: "Supply Chain Disruption Recovery", summary: "EV makers recover from production halts within 15 days on average. Competitors see brief lift.", confidence: "Moderate", eventCount: 15 },
];

const companyProfile: CompanyProfile = {
  ticker: "NVDA", name: "NVIDIA Corporation", sector: "Technology", industry: "Semiconductors",
  marketCap: "$3.2T", pe: 62.4, revenue: "$130.5B", employees: "32,000",
};

const companyProfiles: CompanyProfile[] = [
  companyProfile,
  { ticker: "AAPL", name: "Apple Inc.", sector: "Technology", industry: "Consumer Electronics", marketCap: "$3.1T", pe: 31.2, revenue: "$391.0B", employees: "161,000" },
  { ticker: "MSFT", name: "Microsoft Corporation", sector: "Technology", industry: "Software", marketCap: "$3.0T", pe: 35.7, revenue: "$245.0B", employees: "228,000" },
  { ticker: "TSLA", name: "Tesla, Inc.", sector: "Consumer Discretionary", industry: "Electric Vehicles", marketCap: "$760.0B", pe: 58.4, revenue: "$97.7B", employees: "140,000" },
  { ticker: "AMD", name: "Advanced Micro Devices, Inc.", sector: "Technology", industry: "Semiconductors", marketCap: "$295.0B", pe: 48.1, revenue: "$25.8B", employees: "28,000" },
  { ticker: "GOOGL", name: "Alphabet Inc.", sector: "Communication Services", industry: "Internet Services", marketCap: "$2.0T", pe: 27.4, revenue: "$350.0B", employees: "182,000" },
  { ticker: "TSM", name: "Taiwan Semiconductor Manufacturing Company", sector: "Technology", industry: "Semiconductors", marketCap: "$835.0B", pe: 26.2, revenue: "$90.0B", employees: "76,000" },
];

const relatedCompaniesGraph: CompanyRelationship[] = [
  { source: "NVDA", target: "TSM", relationship: "Supplier", strength: 0.9 },
  { source: "NVDA", target: "AMD", relationship: "Competitor", strength: 0.85 },
  { source: "NVDA", target: "AVGO", relationship: "Sector Peer", strength: 0.6 },
  { source: "NVDA", target: "INTC", relationship: "Competitor", strength: 0.7 },
  { source: "NVDA", target: "MSFT", relationship: "Customer", strength: 0.8 },
  { source: "NVDA", target: "GOOGL", relationship: "Customer", strength: 0.75 },
  { source: "TSM", target: "AVGO", relationship: "Supplier", strength: 0.5 },
  { source: "AMD", target: "INTC", relationship: "Competitor", strength: 0.8 },
];

const priceData: PricePoint[] = Array.from({ length: 90 }, (_, i) => ({
  date: new Date(2026, 0, i + 1).toISOString().split("T")[0],
  price: 850 + Math.sin(i / 10) * 50 + Math.random() * 20 + i * 0.5,
  volume: Math.floor(Math.random() * 50000000) + 20000000,
}));

const eventMarkers: EventMarker[] = [
  { date: "2026-01-15", label: "Product Launch", type: "positive" },
  { date: "2026-02-08", label: "Earnings Beat", type: "positive" },
  { date: "2026-02-22", label: "Supply Issue", type: "negative" },
  { date: "2026-03-05", label: "Partnership", type: "positive" },
];

const eventStudyResults: EventStudyResult[] = [
  { horizon: "1D", avgReturn: 0.45, winRate: 58, sampleSize: 42 },
  { horizon: "3D", avgReturn: 1.12, winRate: 62, sampleSize: 42 },
  { horizon: "5D", avgReturn: 1.78, winRate: 65, sampleSize: 42 },
  { horizon: "10D", avgReturn: 2.34, winRate: 61, sampleSize: 42 },
  { horizon: "20D", avgReturn: 3.15, winRate: 59, sampleSize: 42 },
];

const returnDistribution: ReturnDistributionPoint[] = Array.from({ length: 12 }, (_, i) => ({
  id: i,
  return: -5.5 + i,
  count: Math.max(1, 12 - Math.abs(5 - i)),
}));

const forwardCurveData: ForwardCurvePoint[] = [
  { day: 1, horizon: "1D", avgReturn: 0.45, upperBound: 0.62, lowerBound: 0.31 },
  { day: 3, horizon: "3D", avgReturn: 1.12, upperBound: 1.38, lowerBound: 0.96 },
  { day: 5, horizon: "5D", avgReturn: 1.78, upperBound: 2.12, lowerBound: 1.51 },
  { day: 10, horizon: "10D", avgReturn: 2.34, upperBound: 2.76, lowerBound: 1.98 },
  { day: 20, horizon: "20D", avgReturn: 3.15, upperBound: 3.62, lowerBound: 2.74 },
];

const journalEntries: JournalEntry[] = [
  {
    id: "1", date: "2026-03-13", title: "AI Chip Supply Chain Analysis",
    events: ["NVDA product launch announcement", "TSM capacity expansion report"],
    patterns: "Supplier stocks consistently outperform following major chip announcements. TSM shows strongest correlation (+0.82) with NVDA product events.",
    hypothesis: "NVDA AI chip announcement detected. Historical analogs suggest supplier stocks often outperform over the following week. Confidence: Moderate.",
    confidence: "Moderate",
  },
  {
    id: "2", date: "2026-03-12", title: "Pharma Regulatory Pattern",
    events: ["LLY FDA expanded approval", "NVO competitive response analysis"],
    patterns: "FDA approvals for weight-loss drugs create sustained momentum. Competitor stocks show initial weakness but recover within 5 days.",
    hypothesis: "The GLP-1 market is expanding. Each new approval validates the category, potentially lifting all players long-term despite short-term competitive dynamics.",
    confidence: "High",
  },
  {
    id: "3", date: "2026-03-11", title: "EV Supply Chain Disruption",
    events: ["TSLA Shanghai production halt", "Battery supply constraints detected"],
    patterns: "Production halts typically last 5-10 days. Stock drawdown averages -2.1% but recovers within 15 days. Competitors see temporary lift.",
    hypothesis: "Supply chain issues are becoming less impactful as EV makers diversify suppliers. Recovery times have shortened from 20 days to 15 days over the past 2 years.",
    confidence: "Low",
  },
];

const paperTrades: PaperTrade[] = [
  { id: "1", ticker: "TSM", direction: "Long", signal: "NVDA chip announcement → Supplier outperformance pattern", entryPrice: 185.40, currentPrice: 189.20, entryDate: "2026-03-13", quantity: 100, status: "Open" },
  { id: "2", ticker: "LLY", direction: "Long", signal: "FDA approval → Post-approval momentum pattern", entryPrice: 892.50, currentPrice: 918.30, entryDate: "2026-03-13", quantity: 20, status: "Open" },
  { id: "3", ticker: "TSLA", direction: "Short", signal: "Production halt → Supply disruption drawdown pattern", entryPrice: 242.80, currentPrice: 238.10, entryDate: "2026-03-13", quantity: 50, status: "Open" },
  { id: "4", ticker: "AMD", direction: "Long", signal: "NVDA competitor correlation → Sector momentum pattern", entryPrice: 178.60, currentPrice: 176.90, entryDate: "2026-03-10", quantity: 75, status: "Closed" },
];

const topSignals: SignalScore[] = [
  {
    id: "sig-1",
    eventId: "1",
    eventCategory: "Product Launch",
    primaryTicker: "NVDA",
    targetTicker: "NVDA",
    targetType: "primary",
    horizon: "5D",
    score: 84.2,
    confidenceBand: "High",
    evidenceSummary: "5D primary signal is bullish: avg 2.8% / median 2.3% / consistency 67% / sample 18.",
    sampleSize: 18,
    avgReturn: 2.8,
    medianReturn: 2.3,
    winRate: 67,
    originType: "primary",
  },
  {
    id: "sig-2",
    eventId: "1",
    eventCategory: "Product Launch",
    primaryTicker: "NVDA",
    targetTicker: "TSM",
    targetType: "related",
    relationshipType: "Supplier",
    horizon: "5D",
    score: 76.4,
    confidenceBand: "High",
    evidenceSummary: "5D related signal is bullish: avg 2.1% / median 1.9% / consistency 64% / sample 12.",
    sampleSize: 12,
    avgReturn: 2.1,
    medianReturn: 1.9,
    winRate: 64,
    originType: "explicit",
  },
  {
    id: "sig-3",
    eventId: "2",
    eventCategory: "Regulatory Approval",
    primaryTicker: "LLY",
    targetTicker: "LLY",
    targetType: "primary",
    horizon: "3D",
    score: 72.1,
    confidenceBand: "Moderate",
    evidenceSummary: "3D primary signal is bullish: avg 3.0% / median 2.6% / consistency 62% / sample 8.",
    sampleSize: 8,
    avgReturn: 3.0,
    medianReturn: 2.6,
    winRate: 62,
    originType: "primary",
  },
  {
    id: "sig-4",
    eventId: "3",
    eventCategory: "Supply Disruption",
    primaryTicker: "TSLA",
    targetTicker: "RIVN",
    targetType: "related",
    relationshipType: "Competitor",
    horizon: "5D",
    score: 54.8,
    confidenceBand: "Moderate",
    evidenceSummary: "5D related signal is bullish: avg 1.1% / median 0.9% / consistency 58% / sample 11.",
    sampleSize: 11,
    avgReturn: 1.1,
    medianReturn: 0.9,
    winRate: 58,
    originType: "inferred",
  },
];

const portfolioPerformance: PortfolioPerformancePoint[] = Array.from({ length: 30 }, (_, i) => ({
  day: i + 1,
  pnl: Math.sin(i / 5) * 500 + i * 50 + (Math.random() - 0.5) * 200,
}));

const eventCategories = [
  "Product Launch", "Regulatory Approval", "Supply Disruption", "Capital Expenditure",
  "Legal/Regulatory", "Earnings", "M&A", "Management Change", "Partnership", "Macro Event",
];

const timeHorizons = ["1D", "3D", "5D", "10D", "20D"];

// ── Route handler ──────────────────────────────────────

type RouteHandler = (params?: Record<string, string>, body?: unknown) => unknown;

const routes: Record<string, RouteHandler> = {
  "/market/indexes": () => marketIndexes,
  "/market/sectors": () => sectorPerformance,
  "/market/volatility": () => volatilityData,
  "/events": () => marketEvents,
  "/events/categories": () => eventCategories,
  "/events/studies": () => eventStudyResults,
  "/events/distribution": () => returnDistribution,
  "/events/forward-curve": () => forwardCurveData,
  "/events/time-horizons": () => timeHorizons,
  "/companies/profile": (params) => {
    if (params?.ticker) {
      return companyProfiles.find((profile) => profile.ticker === params.ticker) || { ...companyProfile, ticker: params.ticker };
    }
    return companyProfile;
  },
  "/companies/search": (params) => {
    const query = (params?.query || "").trim().toUpperCase();
    if (!query) return [];

    return companyProfiles
      .filter((profile) =>
        profile.ticker.toUpperCase().includes(query) ||
        profile.name.toUpperCase().includes(query)
      )
      .slice(0, 6)
      .map((profile) => ({ ticker: profile.ticker, name: profile.name }));
  },
  "/companies/relationships": () => relatedCompaniesGraph,
  "/companies/price-history": () => priceData,
  "/companies/event-markers": () => eventMarkers,
  "/research/insights": () => researchInsights,
  "/research/journal": () => journalEntries,
  "/signals/top": (params) => topSignals.slice(0, Number(params?.limit || topSignals.length)),
  "/trades": () => paperTrades,
  "/trades/performance": () => portfolioPerformance,
};

export async function mockHandler<T>(endpoint: string, _config: RequestInit): Promise<T> {
  await delay(LATENCY);

  // Parse query params from endpoint
  const [path, queryString] = endpoint.split("?");
  const params: Record<string, string> = {};
  if (queryString) {
    new URLSearchParams(queryString).forEach((v, k) => { params[k] = v; });
  }

  const handler = routes[path];
  if (!handler) {
    throw new Error(`Mock API: No handler for ${path}`);
  }

  return handler(params) as T;
}
