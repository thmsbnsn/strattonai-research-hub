// Mock data for StrattonAI

export const marketIndexes = [
  { ticker: "SPY", name: "S&P 500", price: 5248.32, change: 0.87, changePercent: 0.42 },
  { ticker: "QQQ", name: "NASDAQ 100", price: 18432.15, change: 156.23, changePercent: 0.86 },
  { ticker: "DIA", name: "Dow Jones", price: 39782.40, change: -42.18, changePercent: -0.11 },
];

export const sectorPerformance = [
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

export const volatilityData = { vix: 16.42, change: -0.83, trend: "declining" as const };

export interface MarketEvent {
  id: string;
  headline: string;
  ticker: string;
  category: string;
  sentiment: "positive" | "negative" | "neutral";
  timestamp: string;
  relatedCompanies: { ticker: string; name: string; relationship: string }[];
  historicalAnalog: string;
  sampleSize: number;
  avgReturn: number;
  details?: string;
}

export const marketEvents: MarketEvent[] = [
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

export const researchInsights = [
  {
    id: "1",
    title: "AI Chip Supply Chain Pattern",
    summary: "Supplier stocks outperform by +1.8% avg within 5 days of major chip announcements.",
    confidence: "High",
    eventCount: 12,
  },
  {
    id: "2",
    title: "FDA Approval Momentum",
    summary: "Pharma stocks show sustained momentum for 10 days post-approval. Competitors show mild weakness.",
    confidence: "Moderate",
    eventCount: 8,
  },
  {
    id: "3",
    title: "Supply Chain Disruption Recovery",
    summary: "EV makers recover from production halts within 15 days on average. Competitors see brief lift.",
    confidence: "Moderate",
    eventCount: 15,
  },
];

export const priceData = Array.from({ length: 90 }, (_, i) => ({
  date: new Date(2026, 0, i + 1).toISOString().split("T")[0],
  price: 850 + Math.sin(i / 10) * 50 + Math.random() * 20 + i * 0.5,
  volume: Math.floor(Math.random() * 50000000) + 20000000,
}));

export const eventMarkers = [
  { date: "2026-01-15", label: "Product Launch", type: "positive" },
  { date: "2026-02-08", label: "Earnings Beat", type: "positive" },
  { date: "2026-02-22", label: "Supply Issue", type: "negative" },
  { date: "2026-03-05", label: "Partnership", type: "positive" },
];

export const companyProfile = {
  ticker: "NVDA",
  name: "NVIDIA Corporation",
  sector: "Technology",
  industry: "Semiconductors",
  marketCap: "$3.2T",
  pe: 62.4,
  revenue: "$130.5B",
  employees: "32,000",
};

export const relatedCompaniesGraph = [
  { source: "NVDA", target: "TSM", relationship: "Supplier", strength: 0.9 },
  { source: "NVDA", target: "AMD", relationship: "Competitor", strength: 0.85 },
  { source: "NVDA", target: "AVGO", relationship: "Sector Peer", strength: 0.6 },
  { source: "NVDA", target: "INTC", relationship: "Competitor", strength: 0.7 },
  { source: "NVDA", target: "MSFT", relationship: "Customer", strength: 0.8 },
  { source: "NVDA", target: "GOOGL", relationship: "Customer", strength: 0.75 },
  { source: "TSM", target: "AVGO", relationship: "Supplier", strength: 0.5 },
  { source: "AMD", target: "INTC", relationship: "Competitor", strength: 0.8 },
];

export const eventStudyResults = [
  { horizon: "1D", avgReturn: 0.45, winRate: 58, sampleSize: 42 },
  { horizon: "3D", avgReturn: 1.12, winRate: 62, sampleSize: 42 },
  { horizon: "5D", avgReturn: 1.78, winRate: 65, sampleSize: 42 },
  { horizon: "10D", avgReturn: 2.34, winRate: 61, sampleSize: 42 },
  { horizon: "20D", avgReturn: 3.15, winRate: 59, sampleSize: 42 },
];

export const returnDistribution = Array.from({ length: 42 }, (_, i) => ({
  id: i,
  return: (Math.random() - 0.3) * 10,
}));

export const forwardCurveData = Array.from({ length: 21 }, (_, i) => ({
  day: i,
  avgReturn: Math.log(1 + i * 0.15) * 2 + (Math.random() - 0.5) * 0.3,
  upperBound: Math.log(1 + i * 0.15) * 2 + 2 + (Math.random() - 0.5) * 0.2,
  lowerBound: Math.log(1 + i * 0.15) * 2 - 1.5 + (Math.random() - 0.5) * 0.2,
}));

export const journalEntries = [
  {
    id: "1",
    date: "2026-03-13",
    title: "AI Chip Supply Chain Analysis",
    events: ["NVDA product launch announcement", "TSM capacity expansion report"],
    patterns: "Supplier stocks consistently outperform following major chip announcements. TSM shows strongest correlation (+0.82) with NVDA product events.",
    hypothesis: "NVDA AI chip announcement detected. Historical analogs suggest supplier stocks often outperform over the following week. Confidence: Moderate.",
    confidence: "Moderate" as const,
  },
  {
    id: "2",
    date: "2026-03-12",
    title: "Pharma Regulatory Pattern",
    events: ["LLY FDA expanded approval", "NVO competitive response analysis"],
    patterns: "FDA approvals for weight-loss drugs create sustained momentum. Competitor stocks show initial weakness but recover within 5 days.",
    hypothesis: "The GLP-1 market is expanding. Each new approval validates the category, potentially lifting all players long-term despite short-term competitive dynamics.",
    confidence: "High" as const,
  },
  {
    id: "3",
    date: "2026-03-11",
    title: "EV Supply Chain Disruption",
    events: ["TSLA Shanghai production halt", "Battery supply constraints detected"],
    patterns: "Production halts typically last 5-10 days. Stock drawdown averages -2.1% but recovers within 15 days. Competitors see temporary lift.",
    hypothesis: "Supply chain issues are becoming less impactful as EV makers diversify suppliers. Recovery times have shortened from 20 days to 15 days over the past 2 years.",
    confidence: "Low" as const,
  },
];

export const paperTrades = [
  {
    id: "1",
    ticker: "TSM",
    direction: "Long" as const,
    signal: "NVDA chip announcement → Supplier outperformance pattern",
    entryPrice: 185.40,
    currentPrice: 189.20,
    entryDate: "2026-03-13",
    quantity: 100,
    status: "Open" as const,
  },
  {
    id: "2",
    ticker: "LLY",
    direction: "Long" as const,
    signal: "FDA approval → Post-approval momentum pattern",
    entryPrice: 892.50,
    currentPrice: 918.30,
    entryDate: "2026-03-13",
    quantity: 20,
    status: "Open" as const,
  },
  {
    id: "3",
    ticker: "TSLA",
    direction: "Short" as const,
    signal: "Production halt → Supply disruption drawdown pattern",
    entryPrice: 242.80,
    currentPrice: 238.10,
    entryDate: "2026-03-13",
    quantity: 50,
    status: "Open" as const,
  },
  {
    id: "4",
    ticker: "AMD",
    direction: "Long" as const,
    signal: "NVDA competitor correlation → Sector momentum pattern",
    entryPrice: 178.60,
    currentPrice: 176.90,
    entryDate: "2026-03-10",
    quantity: 75,
    status: "Closed" as const,
  },
];

export const portfolioPerformance = Array.from({ length: 30 }, (_, i) => ({
  day: i + 1,
  pnl: Math.sin(i / 5) * 500 + i * 50 + (Math.random() - 0.5) * 200,
}));

export const eventCategories = [
  "Product Launch",
  "Regulatory Approval",
  "Supply Disruption",
  "Capital Expenditure",
  "Legal/Regulatory",
  "Earnings",
  "M&A",
  "Management Change",
  "Partnership",
  "Macro Event",
];

export const timeHorizons = ["1D", "3D", "5D", "10D", "20D"];
