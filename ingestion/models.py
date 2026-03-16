from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


ConfidenceLevel = Literal["High", "Moderate", "Low"]
NormalizedSentiment = Literal["positive", "negative", "neutral"]
RelationshipOrigin = Literal["explicit", "inferred"]


@dataclass(slots=True)
class RawRelatedCompanyRecord:
    ticker: str
    name: str | None = None
    relationship: str | None = None
    strength: float | None = None
    notes: str | None = None


@dataclass(slots=True)
class RawResearchInsightRecord:
    title: str
    summary: str
    confidence: str | None = None
    event_count: int | None = None


@dataclass(slots=True)
class RawEventRecord:
    source_name: str
    source_record_id: str | None
    headline: str
    primary_ticker: str
    event_type: str | None
    sentiment: str | None
    occurred_at: str
    historical_analog: str | None = None
    sample_size: int | None = None
    avg_return: float | None = None
    details: str | None = None
    related_companies: list[RawRelatedCompanyRecord] = field(default_factory=list)
    research_insight: RawResearchInsightRecord | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RawSecFilingRecord:
    accession_number: str
    form_type: str
    filing_date: str
    company_name: str
    ticker: str
    headline: str | None = None
    summary: str | None = None
    extracted_tags: list[str] = field(default_factory=list)
    related_tickers: list[str | dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CanonicalRelationship:
    id: str
    source_ticker: str
    target_ticker: str
    relationship_type: str
    strength: float
    is_directional: bool = True
    source_name: str | None = None
    target_name: str | None = None
    notes: str | None = None
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class NormalizedRelatedCompany:
    id: str
    event_id: str
    source_ticker: str
    target_ticker: str
    name: str
    relationship: str
    strength: float | None = None
    origin_type: RelationshipOrigin = "explicit"
    notes: str | None = None
    rationale: dict[str, Any] = field(default_factory=dict)
    graph_relationship_id: str | None = None


@dataclass(slots=True)
class NormalizedResearchInsight:
    id: str
    title: str
    summary: str
    confidence: ConfidenceLevel
    event_count: int


@dataclass(slots=True)
class NormalizedEvent:
    id: str
    source_name: str
    source_record_id: str
    headline: str
    ticker: str
    category: str
    sentiment: NormalizedSentiment
    timestamp: datetime
    historical_analog: str | None
    sample_size: int
    avg_return: float
    details: str | None
    metadata: dict[str, Any] = field(default_factory=dict)
    related_companies: list[NormalizedRelatedCompany] = field(default_factory=list)
    research_insight: NormalizedResearchInsight | None = None


@dataclass(slots=True)
class IngestionFailure:
    record_index: int
    reason: str


@dataclass(slots=True)
class WriteSummary:
    events_upserted: int = 0
    related_companies_upserted: int = 0
    research_insights_upserted: int = 0


@dataclass(slots=True)
class IngestionSummary:
    input_records: int = 0
    normalized_records: int = 0
    skipped_records: int = 0
    failed_records: int = 0
    write_summary: WriteSummary = field(default_factory=WriteSummary)
