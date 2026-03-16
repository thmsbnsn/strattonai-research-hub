from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any
from uuid import NAMESPACE_URL, uuid5


FINANCIAL_NEWS_SOURCE_NAME = "financial_news_local"
EVENT_HINT_ALIASES = {
    "Corporate Earnings Report": "earnings",
    "Major Merger/Acquisition": "acquisition",
    "Supply Chain Disruption": "supply chain disruption",
    "Regulatory Changes": "regulatory",
}
SENTIMENT_ALIASES = {
    "positive": "positive",
    "negative": "negative",
    "neutral": "neutral",
}
NEWS_RECORD_NAMESPACE = uuid5(NAMESPACE_URL, "strattonai/financial-news")


@dataclass(frozen=True, slots=True)
class FinancialNewsCompanyMappingDecision:
    company_name: str
    ticker: str | None
    canonical_entity_name: str | None
    strategy: str
    notes: str

    @property
    def is_supported(self) -> bool:
        return self.ticker is not None


COMPANY_MAPPING_DECISIONS = {
    "apple inc": FinancialNewsCompanyMappingDecision(
        company_name="Apple Inc.",
        ticker="AAPL",
        canonical_entity_name="Apple Inc.",
        strategy="existing_us_primary",
        notes="Existing canonical U.S. primary listing already used across the project.",
    ),
    "boeing": FinancialNewsCompanyMappingDecision(
        company_name="Boeing",
        ticker="BA",
        canonical_entity_name="The Boeing Company",
        strategy="existing_us_primary",
        notes="Existing canonical U.S. primary listing already used across the project.",
    ),
    "exxonmobil": FinancialNewsCompanyMappingDecision(
        company_name="ExxonMobil",
        ticker="XOM",
        canonical_entity_name="Exxon Mobil Corporation",
        strategy="existing_us_primary",
        notes="Existing canonical U.S. primary listing already used across the project.",
    ),
    "goldman sachs": FinancialNewsCompanyMappingDecision(
        company_name="Goldman Sachs",
        ticker="GS",
        canonical_entity_name="The Goldman Sachs Group, Inc.",
        strategy="existing_us_primary",
        notes="Existing canonical U.S. primary listing already used across the project.",
    ),
    "jp morgan chase": FinancialNewsCompanyMappingDecision(
        company_name="JP Morgan Chase",
        ticker="JPM",
        canonical_entity_name="JPMorgan Chase & Co.",
        strategy="existing_us_primary",
        notes="Existing canonical U.S. primary listing already used across the project.",
    ),
    "jpmorgan chase": FinancialNewsCompanyMappingDecision(
        company_name="JPMorgan Chase",
        ticker="JPM",
        canonical_entity_name="JPMorgan Chase & Co.",
        strategy="existing_us_primary",
        notes="Existing canonical U.S. primary listing already used across the project.",
    ),
    "microsoft": FinancialNewsCompanyMappingDecision(
        company_name="Microsoft",
        ticker="MSFT",
        canonical_entity_name="Microsoft Corporation",
        strategy="existing_us_primary",
        notes="Existing canonical U.S. primary listing already used across the project.",
    ),
    "tata motors": FinancialNewsCompanyMappingDecision(
        company_name="Tata Motors",
        ticker="TTM",
        canonical_entity_name="Tata Motors Limited",
        strategy="nyse_adr",
        notes="NYSE ADR ticker TTM is used as the deterministic tradable line because the project currently operates on exchange ticker strings without a separate home-listing convention.",
    ),
    "tesla": FinancialNewsCompanyMappingDecision(
        company_name="Tesla",
        ticker="TSLA",
        canonical_entity_name="Tesla, Inc.",
        strategy="existing_us_primary",
        notes="Existing canonical U.S. primary listing already used across the project.",
    ),
    "samsung electronics": FinancialNewsCompanyMappingDecision(
        company_name="Samsung Electronics",
        ticker=None,
        canonical_entity_name=None,
        strategy="unsupported",
        notes="Skipped because the project does not yet define a canonical foreign-listing convention across KRX primary shares, London GDRs, and OTC lines.",
    ),
    "reliance industries": FinancialNewsCompanyMappingDecision(
        company_name="Reliance Industries",
        ticker=None,
        canonical_entity_name=None,
        strategy="unsupported",
        notes="Skipped because the project does not yet define a canonical foreign-listing convention across NSE, BSE, and depository receipt symbols.",
    ),
}


class FinancialNewsMappingError(ValueError):
    """Raised when a financial-news row cannot be mapped safely."""


def _clean_text(value: Any, field_name: str) -> str:
    cleaned = str(value or "").strip()
    if not cleaned:
        raise FinancialNewsMappingError(f"{field_name} is required.")
    return cleaned


def _clean_optional_text(value: Any) -> str | None:
    cleaned = str(value or "").strip()
    return cleaned or None


def _normalize_company_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def get_financial_news_company_mapping_decision(company_name: str) -> FinancialNewsCompanyMappingDecision | None:
    normalized = _normalize_company_key(company_name)
    return COMPANY_MAPPING_DECISIONS.get(normalized)


def resolve_financial_news_company_ticker(company_name: str) -> str | None:
    decision = get_financial_news_company_mapping_decision(company_name)
    return decision.ticker if decision is not None else None


def _build_source_record_id(row: dict[str, Any], row_number: int) -> str:
    parts = [
        str(row.get("Date") or "").strip(),
        str(row.get("Source") or "").strip(),
        str(row.get("Headline") or "").strip(),
        str(row.get("Market_Event") or "").strip(),
        str(row.get("Related_Company") or "").strip(),
        str(row_number),
    ]
    return str(uuid5(NEWS_RECORD_NAMESPACE, "||".join(parts)))


def _normalize_sentiment(value: Any) -> str | None:
    cleaned = _clean_optional_text(value)
    if cleaned is None:
        return None
    return SENTIMENT_ALIASES.get(cleaned.lower())


def _normalize_event_hint(value: Any) -> str | None:
    cleaned = _clean_optional_text(value)
    if cleaned is None:
        return None
    return EVENT_HINT_ALIASES.get(cleaned)


def map_financial_news_to_event_payload(raw_row: dict[str, Any], row_number: int) -> dict[str, Any]:
    event_date = _clean_text(raw_row.get("Date"), "Date")
    headline = _clean_text(raw_row.get("Headline"), "Headline")
    company_name = _clean_text(raw_row.get("Related_Company"), "Related_Company")
    mapping_decision = get_financial_news_company_mapping_decision(company_name)
    ticker = mapping_decision.ticker if mapping_decision is not None else None
    if ticker is None:
        if mapping_decision is not None:
            raise FinancialNewsMappingError(f"Unsupported Related_Company mapping: {company_name} ({mapping_decision.notes})")
        raise FinancialNewsMappingError(f"Unsupported Related_Company mapping: {company_name}")

    market_event = _clean_optional_text(raw_row.get("Market_Event"))
    sector = _clean_optional_text(raw_row.get("Sector"))
    market_index = _clean_optional_text(raw_row.get("Market_Index"))
    impact_level = _clean_optional_text(raw_row.get("Impact_Level"))
    source = _clean_optional_text(raw_row.get("Source"))
    news_url = _clean_optional_text(raw_row.get("News_Url"))
    sentiment = _normalize_sentiment(raw_row.get("Sentiment"))

    details_parts = [
        f"Source: {source}." if source else None,
        f"Market event: {market_event}." if market_event else None,
        f"Market index: {market_index}." if market_index else None,
        f"Sector: {sector}." if sector else None,
        f"Impact level: {impact_level}." if impact_level else None,
    ]
    details = " ".join(part for part in details_parts if part) or None

    metadata = {
        "source_type": "financial_news",
        "source_file_format": "csv",
        "company_name": company_name,
        "canonical_entity_name": mapping_decision.canonical_entity_name if mapping_decision is not None else None,
        "company_mapping_strategy": mapping_decision.strategy if mapping_decision is not None else None,
        "company_mapping_notes": mapping_decision.notes if mapping_decision is not None else None,
        "market_event": market_event,
        "market_index": market_index,
        "sector": sector,
        "impact_level": impact_level,
        "news_url": news_url,
        "row_number": row_number,
        "classification_hints": [item for item in [market_event, sector, impact_level, market_index] if item],
    }

    return {
        "source_name": FINANCIAL_NEWS_SOURCE_NAME,
        "source_record_id": _build_source_record_id(raw_row, row_number),
        "headline": headline,
        "primary_ticker": ticker,
        "event_type": _normalize_event_hint(market_event),
        "sentiment": sentiment,
        "occurred_at": f"{event_date}T13:30:00Z",
        "details": details,
        "metadata": metadata,
    }
