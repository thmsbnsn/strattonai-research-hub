import type { Event, JournalEntry, SignalScore } from "@/types";

function mapConfidenceBandToResearchConfidence(signal?: SignalScore): JournalEntry["confidence"] {
  if (signal?.confidenceBand === "High" || signal?.confidenceBand === "Moderate" || signal?.confidenceBand === "Low") {
    return signal.confidenceBand;
  }

  return "Moderate";
}

export function generateJournalEntriesFromSignals(events: Event[], signals: SignalScore[]) {
  const signalsByEvent = signals.reduce<Record<string, SignalScore[]>>((accumulator, signal) => {
    accumulator[signal.eventId] = [...(accumulator[signal.eventId] ?? []), signal];
    return accumulator;
  }, {});

  return events
    .map((event) => {
      const rankedSignals = [...(signalsByEvent[event.id] ?? [])].sort((left, right) => right.score - left.score);
      const strongestSignal = rankedSignals[0];
      const relatedTickers = event.relatedCompanies.map((company) => `${company.ticker} (${company.relationship})`);

      return {
        id: `journal-${event.id}`,
        date: event.timestamp.slice(0, 10),
        title: `${event.ticker} ${event.category} Research Note`,
        events: [event.headline, ...relatedTickers].slice(0, 4),
        patterns: strongestSignal
          ? strongestSignal.evidenceSummary
          : `${event.category} events for ${event.ticker} are available, but no ranked signal evidence has been computed yet.`,
        hypothesis: strongestSignal
          ? `${event.ticker} ${event.category.toLowerCase()} setup suggests ${strongestSignal.targetTicker} may be worth review over the ${strongestSignal.horizon} horizon.`
          : `${event.ticker} ${event.category.toLowerCase()} setup has been detected. More historical study depth is needed before promoting a stronger hypothesis.`,
        confidence: mapConfidenceBandToResearchConfidence(strongestSignal),
      } satisfies JournalEntry;
    })
    .sort((left, right) => right.date.localeCompare(left.date));
}
