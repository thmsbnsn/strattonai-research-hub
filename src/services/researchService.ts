import { api } from "@/api/client";
import type { ResearchInsight, JournalEntry } from "@/types";

export const getResearchInsights = () => api.get<ResearchInsight[]>("/research/insights");

export const getJournalEntries = () => api.get<JournalEntry[]>("/research/journal");
