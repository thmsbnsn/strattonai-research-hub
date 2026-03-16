from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:
    from .rules import (
        collect_metadata_terms,
        collect_search_terms,
        match_category_by_alias,
        match_category_by_source_hint,
        resolve_sentiment_alias,
        resolve_sentiment_keywords,
        score_categories_by_keywords,
    )
    from .taxonomy import CategoryDefinition, get_category_definition, load_taxonomy_config
except ImportError:  # pragma: no cover - script execution fallback
    from rules import (  # type: ignore
        collect_metadata_terms,
        collect_search_terms,
        match_category_by_alias,
        match_category_by_source_hint,
        resolve_sentiment_alias,
        resolve_sentiment_keywords,
        score_categories_by_keywords,
    )
    from taxonomy import CategoryDefinition, get_category_definition, load_taxonomy_config  # type: ignore


@dataclass(frozen=True, slots=True)
class ClassificationInput:
    source_name: str | None
    event_type_hint: str | None
    sentiment_hint: str | None
    headline: str | None
    summary: str | None
    extracted_tags: tuple[str, ...]
    form_type: str | None
    metadata: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    category: str
    sentiment: str
    matched_rules: tuple[str, ...]
    explanation: str
    confidence: str
    confidence_note: str

    def as_metadata(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "sentiment": self.sentiment,
            "matched_rules": list(self.matched_rules),
            "explanation": self.explanation,
            "confidence": self.confidence,
            "confidence_note": self.confidence_note,
        }


def _build_explanation(category: CategoryDefinition, matched_rules: list[str], confidence: str) -> str:
    if matched_rules:
        return f"{category.name} selected via {', '.join(matched_rules)}."
    return f"{category.name} selected by fallback rule."


def classify_event(input_data: ClassificationInput) -> ClassificationResult:
    config = load_taxonomy_config()
    search_terms = collect_search_terms(
        input_data.event_type_hint,
        input_data.headline,
        input_data.summary,
        input_data.form_type,
        extracted_tags=input_data.extracted_tags,
    )
    search_terms.extend(collect_metadata_terms(input_data.metadata))

    matched_rules: list[str] = []
    confidence = "Low"

    category, alias_rules = match_category_by_alias(config, input_data.event_type_hint)
    if category is not None:
        matched_rules.extend(alias_rules)
        confidence = "High"
    else:
        category, keyword_rules = score_categories_by_keywords(config, search_terms)
        if category is not None:
            matched_rules.extend(keyword_rules)
            confidence = "Moderate"
        else:
            category, source_rules = match_category_by_source_hint(config, input_data.source_name, input_data.form_type)
            if category is not None:
                matched_rules.extend(source_rules)
                confidence = "Low"

    if category is None:
        category = get_category_definition("Macro Event")
        if category is None:  # pragma: no cover - invalid config guard
            raise RuntimeError("Taxonomy config must define 'Macro Event'.")
        matched_rules.append("fallback:macro_event")
        confidence = "Low"

    sentiment, sentiment_rules = resolve_sentiment_alias(config, input_data.sentiment_hint)
    if sentiment is not None:
        matched_rules.extend(sentiment_rules)
        confidence = "High" if confidence == "High" else "Moderate"
    else:
        sentiment, keyword_sentiment_rules = resolve_sentiment_keywords(config, search_terms)
        if sentiment is not None:
            matched_rules.extend(keyword_sentiment_rules)
            confidence = "Moderate" if confidence != "High" else confidence

    if sentiment is None:
        sentiment = category.default_sentiment
        matched_rules.append(f"default_sentiment:{category.default_sentiment}")

    explanation = _build_explanation(category, matched_rules, confidence)
    return ClassificationResult(
        category=category.name,
        sentiment=sentiment,
        matched_rules=tuple(matched_rules),
        explanation=explanation,
        confidence=confidence,
        confidence_note=category.confidence_note,
    )
