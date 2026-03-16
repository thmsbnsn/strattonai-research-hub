from __future__ import annotations

from uuid import NAMESPACE_URL, uuid5

try:
    from .models import NormalizedEvent, NormalizedRelatedCompany
    from .relationship_graph import GraphMatch, RelationshipGraph, load_relationship_graph
    from .relationship_rules import get_expansion_rule
except ImportError:  # pragma: no cover - script execution fallback
    from models import NormalizedEvent, NormalizedRelatedCompany  # type: ignore
    from relationship_graph import GraphMatch, RelationshipGraph, load_relationship_graph  # type: ignore
    from relationship_rules import get_expansion_rule  # type: ignore


RELATED_COMPANY_NAMESPACE = uuid5(NAMESPACE_URL, "strattonai/related-companies")


def _build_related_company_id(event_id: str, source_ticker: str, target_ticker: str, relationship: str) -> str:
    return str(uuid5(RELATED_COMPANY_NAMESPACE, "||".join((event_id, source_ticker, target_ticker, relationship))))


def _build_inferred_related_company(
    event: NormalizedEvent,
    match: GraphMatch,
    priority_rank: int,
) -> NormalizedRelatedCompany:
    relationship = match.relationship.relationship_type
    notes = match.relationship.notes or f"Inferred from canonical relationship graph for {event.category}."
    rationale = {
        "origin": "inferred",
        "event_category": event.category,
        "relationship_type": relationship,
        "priority_rank": priority_rank,
        "graph_strength": match.relationship.strength,
        "graph_relationship_id": match.relationship.id,
        "used_reverse_edge": match.used_reverse,
        "graph_notes": match.relationship.notes,
        "graph_provenance": match.relationship.provenance,
        "rule_name": f"{event.category.lower().replace('/', '_').replace(' ', '_')}_expansion",
    }

    return NormalizedRelatedCompany(
        id=_build_related_company_id(event.id, event.ticker, match.target_ticker, relationship),
        event_id=event.id,
        source_ticker=event.ticker,
        target_ticker=match.target_ticker,
        name=match.target_name or match.target_ticker,
        relationship=relationship,
        strength=match.relationship.strength,
        origin_type="inferred",
        notes=notes,
        rationale=rationale,
        graph_relationship_id=match.relationship.id,
    )


def expand_related_entities(
    event: NormalizedEvent,
    graph: RelationshipGraph | None = None,
) -> list[NormalizedRelatedCompany]:
    graph = graph or load_relationship_graph()
    rule = get_expansion_rule(event.category)

    explicit_related = list(event.related_companies)
    explicit_targets = {related.target_ticker for related in explicit_related}
    max_total = max(rule.max_total, len(explicit_related))
    available_slots = min(rule.max_inferred, max(max_total - len(explicit_related), 0))

    if available_slots == 0:
        return explicit_related

    ranked_candidates: list[tuple[int, float, str, str, GraphMatch]] = []
    for match in graph.find_related(event.ticker):
        relationship_type = match.relationship.relationship_type
        priority_rank = rule.priority_rank(relationship_type)

        if priority_rank is None:
            continue

        if match.relationship.strength < rule.min_strength:
            continue

        if match.target_ticker == event.ticker or match.target_ticker in explicit_targets:
            continue

        ranked_candidates.append(
            (
                priority_rank,
                -match.relationship.strength,
                match.target_ticker,
                relationship_type,
                match,
            )
        )

    ranked_candidates.sort()

    inferred_related: list[NormalizedRelatedCompany] = []
    seen_targets = set(explicit_targets)

    for priority_rank, _negative_strength, _target_ticker, _relationship_type, match in ranked_candidates:
        if match.target_ticker in seen_targets:
            continue

        inferred_related.append(_build_inferred_related_company(event, match, priority_rank))
        seen_targets.add(match.target_ticker)

        if len(inferred_related) >= available_slots:
            break

    return [*explicit_related, *inferred_related]
