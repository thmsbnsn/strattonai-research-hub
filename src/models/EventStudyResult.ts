export interface EventStudyResult {
  eventCategory?: string;
  horizon: string;
  avgReturn: number;
  medianReturn?: number;
  winRate: number;
  sampleSize: number;
}
