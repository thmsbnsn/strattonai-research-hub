import { describe, expect, it } from "vitest";
import { generateJournalEntriesFromSignals } from "./researchJournalEngine";

describe("researchJournalEngine", () => {
  it("builds deterministic journal entries from live events and signals", () => {
    const entries = generateJournalEntriesFromSignals(
      [
        {
          id: "evt-1",
          headline: "NVDA launches next-gen AI platform",
          ticker: "NVDA",
          category: "Product Launch",
          sentiment: "positive",
          timestamp: "2026-03-13T08:30:00Z",
          relatedCompanies: [{ ticker: "TSM", name: "TSM", relationship: "Supplier" }],
          historicalAnalog: "Historical analog.",
          sampleSize: 12,
          avgReturn: 1.8,
        },
      ],
      [
        {
          id: "sig-1",
          eventId: "evt-1",
          eventCategory: "Product Launch",
          primaryTicker: "NVDA",
          targetTicker: "TSM",
          targetType: "related",
          relationshipType: "Supplier",
          horizon: "5D",
          score: 76.4,
          confidenceBand: "High",
          evidenceSummary: "5D supplier signal is bullish with solid sample depth.",
          sampleSize: 12,
          avgReturn: 2.1,
          medianReturn: 1.9,
          winRate: 64,
          originType: "explicit",
        },
      ]
    );

    expect(entries).toHaveLength(1);
    expect(entries[0]).toEqual(
      expect.objectContaining({
        id: "journal-evt-1",
        confidence: "High",
      })
    );
    expect(entries[0].patterns).toContain("bullish");
    expect(entries[0].events).toContain("TSM (Supplier)");
  });
});
