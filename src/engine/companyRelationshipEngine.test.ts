import { describe, expect, it } from "vitest";
import { mergeCompanyRelationships, relationshipMappingToGraphEdge } from "./companyRelationshipEngine";

describe("companyRelationshipEngine", () => {
  it("normalizes relationship mapping tickers", () => {
    expect(
      relationshipMappingToGraphEdge({
        id: "custom-1",
        company: " nvda ",
        related: " tsm ",
        type: "Supplier",
        strength: 0.9,
      })
    ).toEqual({
      source: "NVDA",
      target: "TSM",
      relationship: "Supplier",
      strength: 0.9,
    });
  });

  it("lets saved overrides replace base graph edges for the same pair", () => {
    const merged = mergeCompanyRelationships(
      [
        { source: "NVDA", target: "AMD", relationship: "Competitor", strength: 0.85 },
        { source: "NVDA", target: "TSM", relationship: "Supplier", strength: 0.9 },
      ],
      [
        { id: "custom-1", company: "NVDA", related: "AMD", type: "Sector Peer", strength: 0.6 },
        { id: "custom-2", company: "AAPL", related: "QCOM", type: "Supplier", strength: 0.8 },
      ]
    );

    expect(merged).toContainEqual({
      source: "NVDA",
      target: "AMD",
      relationship: "Sector Peer",
      strength: 0.6,
    });
    expect(merged).toContainEqual({
      source: "AAPL",
      target: "QCOM",
      relationship: "Supplier",
      strength: 0.8,
    });
    expect(merged.filter((edge) => edge.source === "NVDA" && edge.target === "AMD")).toHaveLength(1);
  });
});
