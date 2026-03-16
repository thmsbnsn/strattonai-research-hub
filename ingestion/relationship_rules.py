from __future__ import annotations

import re
from dataclasses import dataclass


CANONICAL_RELATIONSHIP_TYPES = (
    "Supplier",
    "Customer",
    "Competitor",
    "Sector Peer",
    "Partner",
    "Regulatory Peer",
    "Supply Chain Dependency",
    "Related",
)

RELATIONSHIP_ALIASES = {
    "supplier": "Supplier",
    "customer": "Customer",
    "competitor": "Competitor",
    "sector peer": "Sector Peer",
    "sector_peer": "Sector Peer",
    "partner": "Partner",
    "regulatory peer": "Regulatory Peer",
    "regulatory_peer": "Regulatory Peer",
    "supply chain dependency": "Supply Chain Dependency",
    "supply_chain_dependency": "Supply Chain Dependency",
    "supply dependency": "Supply Chain Dependency",
    "related": "Related",
}


@dataclass(frozen=True, slots=True)
class ExpansionRuleSet:
    prioritized_relationship_types: tuple[str, ...]
    min_strength: float
    max_total: int
    max_inferred: int

    def priority_rank(self, relationship_type: str) -> int | None:
        try:
            return self.prioritized_relationship_types.index(relationship_type)
        except ValueError:
            return None


DEFAULT_EXPANSION_RULE = ExpansionRuleSet(
    prioritized_relationship_types=("Sector Peer", "Competitor", "Partner", "Related"),
    min_strength=0.45,
    max_total=4,
    max_inferred=2,
)

EVENT_CATEGORY_RULES = {
    "Product Launch": ExpansionRuleSet(
        prioritized_relationship_types=("Supplier", "Competitor", "Customer", "Sector Peer", "Partner"),
        min_strength=0.5,
        max_total=5,
        max_inferred=2,
    ),
    "Supply Disruption": ExpansionRuleSet(
        prioritized_relationship_types=("Supplier", "Supply Chain Dependency", "Customer", "Competitor", "Sector Peer"),
        min_strength=0.45,
        max_total=5,
        max_inferred=3,
    ),
    "Regulatory Approval": ExpansionRuleSet(
        prioritized_relationship_types=("Competitor", "Regulatory Peer", "Sector Peer", "Partner"),
        min_strength=0.5,
        max_total=4,
        max_inferred=2,
    ),
    "Legal/Regulatory": ExpansionRuleSet(
        prioritized_relationship_types=("Regulatory Peer", "Sector Peer", "Competitor", "Partner"),
        min_strength=0.5,
        max_total=4,
        max_inferred=2,
    ),
    "Earnings": ExpansionRuleSet(
        prioritized_relationship_types=("Competitor", "Supplier", "Customer", "Sector Peer"),
        min_strength=0.5,
        max_total=4,
        max_inferred=2,
    ),
    "Capital Expenditure": ExpansionRuleSet(
        prioritized_relationship_types=("Supplier", "Customer", "Partner", "Competitor", "Sector Peer"),
        min_strength=0.45,
        max_total=5,
        max_inferred=2,
    ),
    "Partnership": ExpansionRuleSet(
        prioritized_relationship_types=("Partner", "Customer", "Supplier", "Sector Peer"),
        min_strength=0.45,
        max_total=4,
        max_inferred=2,
    ),
    "Macro Event": ExpansionRuleSet(
        prioritized_relationship_types=("Sector Peer", "Competitor", "Regulatory Peer", "Related"),
        min_strength=0.5,
        max_total=4,
        max_inferred=2,
    ),
}


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def normalize_relationship_type(value: str | None) -> str:
    if value is None:
        return "Related"

    cleaned = value.strip()
    if not cleaned:
        return "Related"

    normalized = RELATIONSHIP_ALIASES.get(cleaned.lower())
    if normalized:
        return normalized

    normalized = RELATIONSHIP_ALIASES.get(_slugify(cleaned).replace("_", " "))
    if normalized:
        return normalized

    titled = cleaned.title()
    if titled in CANONICAL_RELATIONSHIP_TYPES:
        return titled

    return cleaned


def get_expansion_rule(event_category: str) -> ExpansionRuleSet:
    return EVENT_CATEGORY_RULES.get(event_category, DEFAULT_EXPANSION_RULE)
