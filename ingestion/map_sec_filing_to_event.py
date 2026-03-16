from __future__ import annotations

from typing import Any

try:
    from .models import RawSecFilingRecord
    from .normalize import ValidationError, normalize_optional_text
except ImportError:  # pragma: no cover - script execution fallback
    from models import RawSecFilingRecord  # type: ignore
    from normalize import ValidationError, normalize_optional_text  # type: ignore


def _clean_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string.")

    cleaned = value.strip()
    if not cleaned:
        raise ValidationError(f"{field_name} must not be empty.")

    return cleaned


def _parse_sec_filing(payload: dict[str, Any]) -> RawSecFilingRecord:
    extracted_tags = payload.get("extracted_tags") or []
    if not isinstance(extracted_tags, list):
        raise ValidationError("extracted_tags must be an array when provided.")

    related_tickers = payload.get("related_tickers") or []
    if not isinstance(related_tickers, list):
        raise ValidationError("related_tickers must be an array when provided.")

    metadata = payload.get("metadata") or {}
    if not isinstance(metadata, dict):
        raise ValidationError("metadata must be an object when provided.")

    return RawSecFilingRecord(
        accession_number=payload.get("accession_number", ""),
        form_type=payload.get("form_type", ""),
        filing_date=payload.get("filing_date", ""),
        company_name=payload.get("company_name", ""),
        ticker=payload.get("ticker", ""),
        headline=payload.get("headline"),
        summary=payload.get("summary"),
        extracted_tags=[str(tag) for tag in extracted_tags],
        related_tickers=related_tickers,
        metadata=metadata,
    )


def _build_headline(company_name: str, form_type: str, headline: str | None, summary: str | None) -> str:
    if headline:
        return headline

    if summary:
        return summary

    return f"{company_name} filed {form_type} disclosure"


def _build_related_companies(primary_ticker: str, related_tickers: list[str | dict[str, Any]]) -> list[dict[str, Any]]:
    related_companies: list[dict[str, Any]] = []

    for item in related_tickers:
        if isinstance(item, str):
            ticker = item
            record = {"ticker": ticker, "relationship": "Related"}
        elif isinstance(item, dict):
            ticker = item.get("ticker")
            if ticker is None:
                raise ValidationError("related_tickers object entries require a ticker field.")
            record = {
                "ticker": ticker,
                "name": item.get("name"),
                "relationship": item.get("relationship") or "Related",
                "strength": item.get("strength"),
            }
        else:
            raise ValidationError("related_tickers entries must be strings or objects.")

        if str(ticker).strip().upper() == primary_ticker.strip().upper():
            continue

        related_companies.append(record)

    return related_companies


def map_sec_filing_to_event_payload(payload: dict[str, Any]) -> dict[str, Any]:
    filing = _parse_sec_filing(payload)

    accession_number = _clean_text(filing.accession_number, "accession_number")
    form_type = _clean_text(filing.form_type, "form_type")
    filing_date = _clean_text(filing.filing_date, "filing_date")
    company_name = _clean_text(filing.company_name, "company_name")
    ticker = _clean_text(filing.ticker, "ticker")

    headline = _build_headline(company_name, form_type, normalize_optional_text(filing.headline), normalize_optional_text(filing.summary))
    related_companies = _build_related_companies(ticker, filing.related_tickers)

    tags_text = ", ".join(filing.extracted_tags) if filing.extracted_tags else None
    historical_analog = f"Derived from SEC {form_type} filing." if form_type else None
    details = filing.summary or headline

    metadata = {
        "source_type": "sec_filing",
        "accession_number": accession_number,
        "form_type": form_type,
        "company_name": company_name,
        "extracted_tags": filing.extracted_tags,
        "filing_summary": filing.summary,
        "headline_hint": filing.headline,
        **filing.metadata,
    }

    if tags_text:
        metadata["tag_summary"] = tags_text

    return {
        "source_name": "sec_filing",
        "source_record_id": accession_number,
        "headline": headline,
        "primary_ticker": ticker,
        "event_type": None,
        "sentiment": None,
        "occurred_at": f"{filing_date}T00:00:00Z",
        "historical_analog": historical_analog,
        "sample_size": 0,
        "avg_return": 0.0,
        "details": details,
        "related_companies": related_companies,
        "metadata": metadata,
    }
