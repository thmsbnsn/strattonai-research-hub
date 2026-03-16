from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ContextCitation:
    kind: str
    title: str
    detail: str
    ticker: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class LocalAIContext:
    ticker: str | None
    company_name: str | None
    profile: dict[str, Any] = field(default_factory=dict)
    latest_price: dict[str, Any] | None = None
    signals: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    relationships: list[dict[str, Any]] = field(default_factory=list)
    studies: list[dict[str, Any]] = field(default_factory=list)
    insights: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    retrieval_mode: str = "structured"

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticker": self.ticker,
            "company_name": self.company_name,
            "profile": self.profile,
            "latest_price": self.latest_price,
            "signals": self.signals,
            "events": self.events,
            "relationships": self.relationships,
            "studies": self.studies,
            "insights": self.insights,
            "notes": self.notes,
            "retrieval_mode": self.retrieval_mode,
        }
