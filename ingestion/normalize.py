from __future__ import annotations

import re
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any
from uuid import NAMESPACE_URL, uuid5

try:
    from .classify_event import ClassificationInput, classify_event
    from .expand_related_entities import expand_related_entities
    from .models import (
        ConfidenceLevel,
        NormalizedEvent,
        NormalizedRelatedCompany,
        NormalizedResearchInsight,
        RawEventRecord,
        RawRelatedCompanyRecord,
        RawResearchInsightRecord,
    )
    from .relationship_rules import normalize_relationship_type
except ImportError:  # pragma: no cover - script execution fallback
    from classify_event import ClassificationInput, classify_event  # type: ignore
    from expand_related_entities import expand_related_entities  # type: ignore
    from models import (  # type: ignore
        ConfidenceLevel,
        NormalizedEvent,
        NormalizedRelatedCompany,
        NormalizedResearchInsight,
        RawEventRecord,
        RawRelatedCompanyRecord,
        RawResearchInsightRecord,
    )
    from relationship_rules import normalize_relationship_type  # type: ignore

EVENT_NAMESPACE = uuid5(NAMESPACE_URL, "strattonai/events")
RELATED_COMPANY_NAMESPACE = uuid5(NAMESPACE_URL, "strattonai/related-companies")
RESEARCH_INSIGHT_NAMESPACE = uuid5(NAMESPACE_URL, "strattonai/research-insights")

DEFAULT_SOURCE_NAME = "local_structured_feed"
DEFAULT_RELATED_COMPANY_STRENGTH = 0.5

CONFIDENCE_ALIASES: dict[str, ConfidenceLevel] = {
    "high": "High",
    "moderate": "Moderate",
    "medium": "Moderate",
    "low": "Low",
}


class ValidationError(ValueError):
    """Raised when a raw input record cannot be normalized safely."""


def _clean_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string.")

    cleaned = value.strip()
    if not cleaned:
        raise ValidationError(f"{field_name} must not be empty.")

    return cleaned


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def normalize_ticker(value: Any, field_name: str = "ticker") -> str:
    cleaned = _clean_text(value, field_name)
    ticker = re.sub(r"[^A-Za-z0-9.\-]", "", cleaned.upper())

    if not ticker:
        raise ValidationError(f"{field_name} must contain a valid ticker.")

    return ticker


def normalize_relationship(value: Any) -> str:
    if value is None:
        return "Related"

    cleaned = _clean_text(value, "relationship")
    return normalize_relationship_type(cleaned)


def normalize_confidence(value: Any) -> ConfidenceLevel:
    if value is None:
        return "Moderate"

    cleaned = _clean_text(value, "confidence").lower()
    normalized = CONFIDENCE_ALIASES.get(cleaned)

    if not normalized:
        raise ValidationError(f"Unsupported confidence value: {value}")

    return normalized


def normalize_timestamp(value: Any) -> datetime:
    cleaned = _clean_text(value, "occurred_at")
    normalized_input = cleaned.replace("Z", "+00:00")

    try:
        parsed = datetime.fromisoformat(normalized_input)
    except ValueError as exc:
        raise ValidationError(f"Invalid occurred_at timestamp: {cleaned}") from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)

    return parsed.astimezone(UTC)


def normalize_optional_int(value: Any, field_name: str, default: int = 0) -> int:
    if value is None:
        return default

    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be an integer.") from exc

    return max(parsed, 0)


def normalize_optional_float(value: Any, field_name: str, default: float = 0.0) -> float:
    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be numeric.") from exc


def normalize_optional_text(value: Any) -> str | None:
    if value is None:
        return None

    cleaned = str(value).strip()
    return cleaned or None


def normalize_optional_text_list(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()

    if not isinstance(value, list):
        raise ValidationError("metadata.extracted_tags must be an array when provided.")

    return tuple(str(item).strip() for item in value if str(item).strip())


def _parse_related_companies(value: Any) -> list[RawRelatedCompanyRecord]:
    if value is None:
        return []

    if not isinstance(value, list):
        raise ValidationError("related_companies must be an array.")

    records: list[RawRelatedCompanyRecord] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValidationError("Each related_companies item must be an object.")

        records.append(
            RawRelatedCompanyRecord(
                ticker=item.get("ticker", ""),
                name=item.get("name"),
                relationship=item.get("relationship"),
                strength=item.get("strength"),
            )
        )

    return records


def _parse_research_insight(value: Any) -> RawResearchInsightRecord | None:
    if value is None:
        return None

    if not isinstance(value, dict):
        raise ValidationError("research_insight must be an object when provided.")

    title = value.get("title")
    summary = value.get("summary")

    if title is None or summary is None:
        raise ValidationError("research_insight requires title and summary.")

    return RawResearchInsightRecord(
        title=title,
        summary=summary,
        confidence=value.get("confidence"),
        event_count=value.get("event_count"),
    )


def parse_raw_event_record(payload: dict[str, Any]) -> RawEventRecord:
    return RawEventRecord(
        source_name=str(payload.get("source_name") or DEFAULT_SOURCE_NAME),
        source_record_id=payload.get("source_record_id"),
        headline=payload.get("headline", ""),
        primary_ticker=payload.get("primary_ticker", ""),
        event_type=payload.get("event_type"),
        sentiment=payload.get("sentiment"),
        occurred_at=payload.get("occurred_at", ""),
        historical_analog=payload.get("historical_analog"),
        sample_size=payload.get("sample_size"),
        avg_return=payload.get("avg_return"),
        details=payload.get("details"),
        related_companies=_parse_related_companies(payload.get("related_companies")),
        research_insight=_parse_research_insight(payload.get("research_insight")),
        metadata=payload.get("metadata", {}) if isinstance(payload.get("metadata"), dict) else {},
    )


def _build_source_record_id(raw_record: RawEventRecord) -> str:
    if raw_record.source_record_id:
        return _slugify(raw_record.source_record_id)

    derived = "|".join(
        [
            raw_record.source_name,
            raw_record.primary_ticker,
            raw_record.occurred_at,
            raw_record.headline,
        ]
    )
    return _slugify(derived)


def _stable_uuid(namespace, *parts: str) -> str:
    return str(uuid5(namespace, "||".join(parts)))


def normalize_related_company(
    raw_record: RawRelatedCompanyRecord,
    primary_ticker: str,
    event_id: str,
) -> NormalizedRelatedCompany:
    target_ticker = normalize_ticker(raw_record.ticker, "related_companies.ticker")
    relationship = normalize_relationship(raw_record.relationship)
    strength = raw_record.strength

    if strength is not None:
        try:
            strength = max(0.0, min(float(strength), 1.0))
        except (TypeError, ValueError) as exc:
            raise ValidationError("related_companies.strength must be numeric when provided.") from exc

    return NormalizedRelatedCompany(
        id=_stable_uuid(RELATED_COMPANY_NAMESPACE, event_id, primary_ticker, target_ticker, relationship),
        event_id=event_id,
        source_ticker=primary_ticker,
        target_ticker=target_ticker,
        name=normalize_optional_text(raw_record.name) or target_ticker,
        relationship=relationship,
        strength=strength if strength is not None else DEFAULT_RELATED_COMPANY_STRENGTH,
        origin_type="explicit",
        notes=normalize_optional_text(raw_record.notes) or "Provided by source input.",
        rationale={
            "origin": "explicit",
            "relationship_type": relationship,
            "source": "input_record",
            "provided_strength": strength if strength is not None else DEFAULT_RELATED_COMPANY_STRENGTH,
        },
    )


def normalize_research_insight(
    raw_insight: RawResearchInsightRecord | None,
    sample_size: int,
) -> NormalizedResearchInsight | None:
    if raw_insight is None:
        return None

    title = _clean_text(raw_insight.title, "research_insight.title")
    summary = _clean_text(raw_insight.summary, "research_insight.summary")
    confidence = normalize_confidence(raw_insight.confidence)
    event_count = normalize_optional_int(raw_insight.event_count, "research_insight.event_count", sample_size)

    return NormalizedResearchInsight(
        id=_stable_uuid(RESEARCH_INSIGHT_NAMESPACE, title.lower()),
        title=title,
        summary=summary,
        confidence=confidence,
        event_count=event_count,
    )


def normalize_event_record(payload: dict[str, Any]) -> NormalizedEvent:
    raw_record = parse_raw_event_record(payload)

    headline = _clean_text(raw_record.headline, "headline")
    ticker = normalize_ticker(raw_record.primary_ticker, "primary_ticker")
    timestamp = normalize_timestamp(raw_record.occurred_at)
    source_name = _slugify(raw_record.source_name or DEFAULT_SOURCE_NAME)
    source_record_id = _build_source_record_id(raw_record)
    sample_size = normalize_optional_int(raw_record.sample_size, "sample_size", 0)
    avg_return = normalize_optional_float(raw_record.avg_return, "avg_return", 0.0)
    details = normalize_optional_text(raw_record.details)
    historical_analog = normalize_optional_text(raw_record.historical_analog)
    raw_metadata = dict(raw_record.metadata)
    extracted_tags = normalize_optional_text_list(raw_metadata.get("extracted_tags"))
    form_type = normalize_optional_text(raw_metadata.get("form_type"))
    classification = classify_event(
        ClassificationInput(
            source_name=source_name,
            event_type_hint=normalize_optional_text(raw_record.event_type),
            sentiment_hint=normalize_optional_text(raw_record.sentiment),
            headline=headline,
            summary=details,
            extracted_tags=extracted_tags,
            form_type=form_type,
            metadata=raw_metadata,
        )
    )
    category = classification.category
    sentiment = classification.sentiment
    event_id = _stable_uuid(EVENT_NAMESPACE, source_name, source_record_id)
    metadata = {
        **raw_metadata,
        "classification": classification.as_metadata(),
    }

    related_companies = [
        normalize_related_company(related_company, ticker, event_id)
        for related_company in raw_record.related_companies
        if normalize_ticker(related_company.ticker, "related_companies.ticker") != ticker
    ]

    research_insight = normalize_research_insight(raw_record.research_insight, sample_size)

    normalized_event = NormalizedEvent(
        id=event_id,
        source_name=source_name,
        source_record_id=source_record_id,
        headline=headline,
        ticker=ticker,
        category=category,
        sentiment=sentiment,
        timestamp=timestamp,
        historical_analog=historical_analog,
        sample_size=sample_size,
        avg_return=avg_return,
        details=details,
        metadata=metadata,
        related_companies=related_companies,
        research_insight=research_insight,
    )
    expanded_related_companies = expand_related_entities(normalized_event)
    return replace(normalized_event, related_companies=expanded_related_companies)


def rebind_event_id(event: NormalizedEvent, event_id: str) -> NormalizedEvent:
    if event.id == event_id:
        return event

    rebound_related = [replace(related_company, event_id=event_id) for related_company in event.related_companies]
    return replace(event, id=event_id, related_companies=rebound_related)
