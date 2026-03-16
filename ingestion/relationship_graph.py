from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

try:
    from .models import CanonicalRelationship
    from .relationship_rules import normalize_relationship_type
except ImportError:  # pragma: no cover - script execution fallback
    from models import CanonicalRelationship  # type: ignore
    from relationship_rules import normalize_relationship_type  # type: ignore


RELATIONSHIP_GRAPH_NAMESPACE = uuid5(NAMESPACE_URL, "strattonai/company-relationship-graph")


@dataclass(frozen=True, slots=True)
class GraphMatch:
    relationship: CanonicalRelationship
    source_ticker: str
    target_ticker: str
    source_name: str | None
    target_name: str | None
    used_reverse: bool = False


def _seed_path() -> Path:
    return Path(__file__).resolve().with_name("relationship_seed.json")


def _clean_ticker(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9.\\-]", "", str(value).strip().upper())
    if not cleaned:
        raise ValueError("Relationship graph tickers must not be empty.")
    return cleaned


def _build_relationship_id(source_ticker: str, target_ticker: str, relationship_type: str) -> str:
    return str(uuid5(RELATIONSHIP_GRAPH_NAMESPACE, "||".join((source_ticker, target_ticker, relationship_type))))


class RelationshipGraph:
    def __init__(self, relationships: tuple[CanonicalRelationship, ...]):
        self.relationships = relationships

    def find_related(self, ticker: str) -> tuple[GraphMatch, ...]:
        normalized_ticker = _clean_ticker(ticker)
        matches: list[GraphMatch] = []

        for relationship in self.relationships:
            if relationship.source_ticker == normalized_ticker:
                matches.append(
                    GraphMatch(
                        relationship=relationship,
                        source_ticker=relationship.source_ticker,
                        target_ticker=relationship.target_ticker,
                        source_name=relationship.source_name,
                        target_name=relationship.target_name,
                    )
                )
            elif not relationship.is_directional and relationship.target_ticker == normalized_ticker:
                matches.append(
                    GraphMatch(
                        relationship=relationship,
                        source_ticker=normalized_ticker,
                        target_ticker=relationship.source_ticker,
                        source_name=relationship.target_name,
                        target_name=relationship.source_name,
                        used_reverse=True,
                    )
                )

        matches.sort(key=lambda item: (item.target_ticker, item.relationship.relationship_type))
        return tuple(matches)


@lru_cache(maxsize=1)
def load_relationship_graph() -> RelationshipGraph:
    payload = json.loads(_seed_path().read_text(encoding="utf-8"))
    relationships: list[CanonicalRelationship] = []

    for entry in payload.get("relationships", []):
        source_ticker = _clean_ticker(entry["source_ticker"])
        target_ticker = _clean_ticker(entry["target_ticker"])
        relationship_type = normalize_relationship_type(entry.get("relationship_type"))
        relationships.append(
            CanonicalRelationship(
                id=entry.get("id") or _build_relationship_id(source_ticker, target_ticker, relationship_type),
                source_ticker=source_ticker,
                target_ticker=target_ticker,
                relationship_type=relationship_type,
                strength=float(entry.get("strength", 0.5)),
                is_directional=bool(entry.get("is_directional", True)),
                source_name=entry.get("source_name"),
                target_name=entry.get("target_name"),
                notes=entry.get("notes"),
                provenance=entry.get("provenance", {}) if isinstance(entry.get("provenance"), dict) else {},
            )
        )

    return RelationshipGraph(tuple(relationships))
