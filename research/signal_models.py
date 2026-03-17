from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal


SignalTargetType = Literal["primary", "related"]
SignalOriginType = Literal["primary", "explicit", "inferred"]
SignalConfidenceBand = Literal["Low", "Moderate", "High"]
ClassifierConfidence = Literal["Low", "Moderate", "High"]


@dataclass(frozen=True, slots=True)
class SignalRelatedCompany:
    target_ticker: str
    relationship_type: str
    origin_type: Literal["explicit", "inferred"]
    rationale: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SignalEvent:
    id: str
    ticker: str
    category: str
    timestamp: datetime
    headline: str
    sentiment: str
    classifier_confidence: ClassifierConfidence
    classifier_rationale: dict[str, Any] = field(default_factory=dict)
    related_companies: tuple[SignalRelatedCompany, ...] = ()


@dataclass(frozen=True, slots=True)
class SignalStudyStatistic:
    study_key: str
    study_target_type: Literal["category_summary", "primary", "relationship", "related"]
    event_category: str
    horizon: str
    sample_size: int
    avg_return: Decimal
    median_return: Decimal
    win_rate: Decimal
    primary_ticker: str | None = None
    related_ticker: str | None = None
    relationship_type: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SignalScore:
    id: str
    signal_key: str
    source_study_key: str
    event_id: str
    event_category: str
    primary_ticker: str
    target_ticker: str
    target_type: SignalTargetType
    relationship_type: str | None
    horizon: str
    score: Decimal
    confidence_band: SignalConfidenceBand
    evidence_summary: str
    rationale: dict[str, Any]
    sample_size: int
    avg_return: Decimal
    median_return: Decimal
    win_rate: Decimal
    origin_type: SignalOriginType
    metadata: dict[str, Any] = field(default_factory=dict)
