export interface ResearchInsight {
  id: string;
  title: string;
  summary: string;
  confidence: string;
  eventCount: number;
}

export interface JournalEntry {
  id: string;
  date: string;
  title: string;
  events: string[];
  patterns: string;
  hypothesis: string;
  confidence: "High" | "Moderate" | "Low";
}
