from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal


StudyTargetType = Literal["category_summary", "primary", "relationship", "related"]
STANDARD_HORIZONS = (1, 3, 5, 10, 20)


@dataclass(frozen=True, slots=True)
class PricePoint:
    date: date
    close: Decimal

    @classmethod
    def from_strings(cls, trade_date: str, close: Any) -> "PricePoint":
        return cls(date=date.fromisoformat(trade_date), close=Decimal(str(close)))


@dataclass(frozen=True, slots=True)
class PriceSeries:
    ticker: str
    prices: tuple[PricePoint, ...]


@dataclass(frozen=True, slots=True)
class StudyRelatedCompany:
    target_ticker: str
    relationship_type: str
    origin_type: str


@dataclass(frozen=True, slots=True)
class StudyEvent:
    id: str
    ticker: str
    category: str
    timestamp: datetime
    related_companies: tuple[StudyRelatedCompany, ...] = ()


@dataclass(frozen=True, slots=True)
class ForwardReturnObservation:
    event_id: str
    study_target_type: StudyTargetType
    event_category: str
    horizon: str
    forward_return: Decimal
    aligned_trade_date: date
    exit_trade_date: date
    primary_ticker: str | None = None
    related_ticker: str | None = None
    relationship_type: str | None = None


@dataclass(frozen=True, slots=True)
class EventStudyAggregate:
    id: str
    study_key: str
    study_target_type: StudyTargetType
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
class EventStudyComputationResult:
    observations: tuple[ForwardReturnObservation, ...]
    aggregates: tuple[EventStudyAggregate, ...]
