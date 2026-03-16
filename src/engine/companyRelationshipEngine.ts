import type { RelationshipMapping } from "@/models";
import type { CompanyRelationship } from "@/types";

function normalizeTicker(value: string) {
  return value.trim().toUpperCase();
}

function normalizeStrength(value: number | undefined) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return 0.75;
  }

  return Math.min(1, Math.max(0, value));
}

function buildRelationshipKey(source: string, target: string) {
  return `${normalizeTicker(source)}::${normalizeTicker(target)}`;
}

export function normalizeCompanyRelationship(relationship: CompanyRelationship): CompanyRelationship {
  return {
    source: normalizeTicker(relationship.source),
    target: normalizeTicker(relationship.target),
    relationship: relationship.relationship.trim() || "Related",
    strength: normalizeStrength(relationship.strength),
  };
}

export function relationshipMappingToGraphEdge(mapping: RelationshipMapping): CompanyRelationship | null {
  const source = normalizeTicker(mapping.company);
  const target = normalizeTicker(mapping.related);

  if (!source || !target) {
    return null;
  }

  return {
    source,
    target,
    relationship: mapping.type.trim() || "Related",
    strength: normalizeStrength(mapping.strength),
  };
}

export function mergeCompanyRelationships(
  baseRelationships: CompanyRelationship[],
  relationshipMappings: RelationshipMapping[]
) {
  const merged = new Map<string, CompanyRelationship>();

  for (const relationship of baseRelationships) {
    const normalized = normalizeCompanyRelationship(relationship);
    merged.set(buildRelationshipKey(normalized.source, normalized.target), normalized);
  }

  for (const mapping of relationshipMappings) {
    const override = relationshipMappingToGraphEdge(mapping);
    if (!override) {
      continue;
    }

    merged.set(buildRelationshipKey(override.source, override.target), override);
  }

  return [...merged.values()].sort((left, right) => {
    if (left.source !== right.source) {
      return left.source.localeCompare(right.source);
    }

    if (left.target !== right.target) {
      return left.target.localeCompare(right.target);
    }

    return left.relationship.localeCompare(right.relationship);
  });
}
