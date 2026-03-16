import { beforeEach, describe, expect, it } from "vitest";
import {
  getEnabledClassificationCategories,
  getRelationshipMappings,
  readSettingsSnapshot,
  saveSettings,
  shouldUseSupabaseLiveData,
} from "./settingsService";

describe("settingsService", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("returns sensible defaults when nothing has been saved", () => {
    const snapshot = readSettingsSnapshot();

    expect(snapshot.dataSources).toHaveLength(4);
    expect(snapshot.classification.every((toggle) => toggle.enabled)).toBe(true);
    expect(shouldUseSupabaseLiveData(snapshot)).toBe(true);
  });

  it("persists settings locally and normalizes relationships", async () => {
    const current = readSettingsSnapshot();

    await saveSettings({
      ...current,
      dataSources: current.dataSources.map((source) =>
        source.key === "supabaseLiveData" ? { ...source, enabled: false } : source
      ),
      relationshipMappings: [
        ...current.relationshipMappings,
        {
          id: "custom-1",
          company: " msft ",
          related: " orcl ",
          type: "Partner",
          strength: 1.4,
        },
      ],
    });

    const snapshot = readSettingsSnapshot();

    expect(shouldUseSupabaseLiveData(snapshot)).toBe(false);
    expect(getRelationshipMappings(snapshot)).toContainEqual(
      expect.objectContaining({
        company: "MSFT",
        related: "ORCL",
        type: "Partner",
        strength: 1,
      })
    );
  });

  it("keeps canonical classification categories available", async () => {
    const current = readSettingsSnapshot();

    await saveSettings({
      ...current,
      classification: current.classification.map((toggle, index) => ({
        ...toggle,
        enabled: index === 0,
      })),
    });

    expect(getEnabledClassificationCategories()).toEqual([current.classification[0].category]);
  });
});
