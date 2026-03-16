import type { ClassificationToggle, Event } from "@/types";

export const CANONICAL_EVENT_CATEGORIES = [
  "Product Launch",
  "Regulatory Approval",
  "Supply Disruption",
  "Capital Expenditure",
  "Legal/Regulatory",
  "Earnings",
  "Partnership",
  "Macro Event",
  "M&A",
  "Management Change",
] as const;

const categoryOrder = new Map(CANONICAL_EVENT_CATEGORIES.map((category, index) => [category, index]));

export function buildDefaultClassificationToggles(): ClassificationToggle[] {
  return CANONICAL_EVENT_CATEGORIES.map((category) => ({ category, enabled: true }));
}

export function getEnabledCategories(toggles: ClassificationToggle[]) {
  return toggles.filter((toggle) => toggle.enabled).map((toggle) => toggle.category);
}

export function filterEventsByEnabledCategories(events: Event[], toggles: ClassificationToggle[]) {
  const enabledCategories = new Set(getEnabledCategories(toggles));

  if (enabledCategories.size === 0) {
    return events;
  }

  return events.filter((event) => enabledCategories.has(event.category));
}

export function sortEventCategories(categories: string[]) {
  return [...categories].sort((left, right) => {
    const leftRank = categoryOrder.get(left) ?? Number.MAX_SAFE_INTEGER;
    const rightRank = categoryOrder.get(right) ?? Number.MAX_SAFE_INTEGER;

    if (leftRank !== rightRank) {
      return leftRank - rightRank;
    }

    return left.localeCompare(right);
  });
}
