import type { ResearchConfidence } from "./ResearchInsight";

export interface JournalEntry {
  id: string;
  date: string;
  title: string;
  events: string[];
  patterns: string;
  hypothesis: string;
  confidence: ResearchConfidence;
}
