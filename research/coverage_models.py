from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


GapKind = Literal["category", "primary", "related", "relationship", "price_history"]


@dataclass(frozen=True, slots=True)
class CoverageEvent:
    id: str
    source_name: str
    ticker: str
    category: str


@dataclass(frozen=True, slots=True)
class CoverageRelatedCompany:
    event_id: str
    source_ticker: str
    target_ticker: str
    relationship_type: str
    origin_type: str


@dataclass(frozen=True, slots=True)
class CoverageRelationshipEdge:
    source_ticker: str
    target_ticker: str
    relationship_type: str
    strength: float


@dataclass(frozen=True, slots=True)
class CoverageStudyStatistic:
    study_key: str
    study_target_type: str
    event_category: str
    horizon: str
    sample_size: int
    primary_ticker: str | None = None
    related_ticker: str | None = None
    relationship_type: str | None = None


@dataclass(frozen=True, slots=True)
class CoverageSignal:
    event_category: str
    primary_ticker: str
    target_ticker: str
    target_type: str
    relationship_type: str | None
    horizon: str
    confidence_band: str
    source_study_target_type: str | None


@dataclass(frozen=True, slots=True)
class SampleSizeDistribution:
    count: int
    minimum: int
    maximum: int
    average: float
    median: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ConfidenceBandDistribution:
    high: int
    moderate: int
    low: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class GapRecord:
    gap_key: str
    gap_kind: GapKind
    event_category: str | None
    target_type: str | None
    ticker: str | None
    relationship_type: str | None
    current_sample_size: int
    required_sample_size: int
    missing_horizons: tuple[str, ...]
    signal_usage_count: int
    fallback_usage_count: int
    gap_score: float
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PriceHistoryGap:
    ticker: str
    available_days: int
    required_days: int
    referenced_as_primary: int
    referenced_as_related: int
    graph_degree: int
    gap_score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BackfillCandidate:
    candidate_key: str
    priority_rank: int
    gap_score: float
    title: str
    recommendation: str
    event_category: str | None
    target_type: str | None
    ticker: str | None
    relationship_type: str | None
    required_additional_examples: int
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class WeakSignalCategory:
    event_category: str
    total_signals: int
    high: int
    moderate: int
    low: int
    high_confidence_ratio: float
    gap_score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CoverageAuditReport:
    event_counts_by_category: dict[str, int]
    event_counts_by_source: dict[str, int]
    study_counts_by_category_horizon_target: dict[str, int]
    sample_size_distribution_by_category: dict[str, SampleSizeDistribution]
    confidence_band_distribution_by_category: dict[str, ConfidenceBandDistribution]
    sparse_primary_slices: tuple[GapRecord, ...] = ()
    sparse_related_slices: tuple[GapRecord, ...] = ()
    sparse_relationship_slices: tuple[GapRecord, ...] = ()
    missing_price_history: tuple[PriceHistoryGap, ...] = ()
    weak_signal_categories: tuple[WeakSignalCategory, ...] = ()
    top_gap_candidates: tuple[BackfillCandidate, ...] = ()
    notes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_counts_by_category": self.event_counts_by_category,
            "event_counts_by_source": self.event_counts_by_source,
            "study_counts_by_category_horizon_target": self.study_counts_by_category_horizon_target,
            "sample_size_distribution_by_category": {
                key: value.to_dict() for key, value in self.sample_size_distribution_by_category.items()
            },
            "confidence_band_distribution_by_category": {
                key: value.to_dict() for key, value in self.confidence_band_distribution_by_category.items()
            },
            "sparse_primary_slices": [item.to_dict() for item in self.sparse_primary_slices],
            "sparse_related_slices": [item.to_dict() for item in self.sparse_related_slices],
            "sparse_relationship_slices": [item.to_dict() for item in self.sparse_relationship_slices],
            "missing_price_history": [item.to_dict() for item in self.missing_price_history],
            "weak_signal_categories": [item.to_dict() for item in self.weak_signal_categories],
            "top_gap_candidates": [item.to_dict() for item in self.top_gap_candidates],
            "notes": self.notes,
        }
