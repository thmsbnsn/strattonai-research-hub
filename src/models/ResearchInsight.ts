export type ResearchConfidence = "High" | "Moderate" | "Low";

export interface ResearchInsight {
  id: string;
  title: string;
  summary: string;
  confidence: ResearchConfidence;
  eventCount: number;
}
