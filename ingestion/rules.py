from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

from .taxonomy import CategoryDefinition, TaxonomyConfig


def normalize_text(value: str | None) -> str:
    return (value or "").strip().lower()


def collect_search_terms(*values: str | None, extracted_tags: Iterable[str]) -> list[str]:
    combined: list[str] = []
    for value in values:
        normalized = normalize_text(value)
        if normalized:
            combined.append(normalized)
    combined.extend(normalize_text(tag) for tag in extracted_tags if normalize_text(tag))
    return combined


def collect_metadata_terms(metadata: dict[str, Any]) -> list[str]:
    terms: list[str] = []

    for key in ("tag_summary", "company_name", "source_type", "filing_summary", "headline_hint"):
        normalized = normalize_text(str(metadata.get(key))) if metadata.get(key) is not None else ""
        if normalized:
            terms.append(normalized)

    for key in ("filing_sections", "classification_hints"):
        value = metadata.get(key)
        if isinstance(value, list):
            for item in value:
                normalized = normalize_text(str(item))
                if normalized:
                    terms.append(normalized)

    return terms


def match_category_by_alias(
    config: TaxonomyConfig,
    event_type_hint: str | None,
) -> tuple[CategoryDefinition | None, list[str]]:
    normalized_hint = normalize_text(event_type_hint)
    if not normalized_hint:
        return None, []

    for category in config.categories:
        if normalized_hint == category.name.lower() or normalized_hint in category.aliases:
            return category, [f"alias:event_type:{normalized_hint}->{category.name}"]

    return None, []


def score_categories_by_keywords(
    config: TaxonomyConfig,
    search_terms: Iterable[str],
) -> tuple[CategoryDefinition | None, list[str]]:
    normalized_terms = tuple(search_terms)
    scores: dict[str, int] = defaultdict(int)
    matches: dict[str, list[str]] = defaultdict(list)

    for category in config.categories:
        for trigger in category.keyword_triggers:
            for term in normalized_terms:
                if trigger and trigger in term:
                    scores[category.name] += 1
                    matches[category.name].append(f"category_keyword:{trigger}")
                    break

    if not scores:
        return None, []

    ranked = sorted(
        config.categories,
        key=lambda category: (-scores.get(category.name, 0), list(config.categories).index(category)),
    )
    winner = ranked[0]
    return winner, matches[winner.name]


def match_category_by_source_hint(
    config: TaxonomyConfig,
    source_name: str | None,
    form_type: str | None,
) -> tuple[CategoryDefinition | None, list[str]]:
    normalized_source = normalize_text(source_name)
    normalized_form_type = normalize_text(form_type)
    if not normalized_source or not normalized_form_type:
        return None, []

    source_hint = config.source_hints.get(normalized_source)
    if source_hint is None:
        return None, []

    category_name = source_hint.form_type_defaults.get(normalized_form_type)
    if category_name is None:
        return None, []

    for category in config.categories:
        if category.name == category_name:
            return category, [f"source_hint:{normalized_source}:{normalized_form_type}->{category.name}"]

    return None, []


def resolve_sentiment_alias(config: TaxonomyConfig, sentiment_hint: str | None) -> tuple[str | None, list[str]]:
    normalized_hint = normalize_text(sentiment_hint)
    if not normalized_hint:
        return None, []

    mapped = config.sentiment_aliases.get(normalized_hint)
    if mapped is None:
        return None, []

    return mapped, [f"alias:sentiment:{normalized_hint}->{mapped}"]


def resolve_sentiment_keywords(config: TaxonomyConfig, search_terms: Iterable[str]) -> tuple[str | None, list[str]]:
    normalized_terms = tuple(search_terms)
    scores: dict[str, int] = defaultdict(int)
    matches: dict[str, list[str]] = defaultdict(list)

    for sentiment, keywords in config.sentiment_keywords.items():
        for keyword in keywords:
            for term in normalized_terms:
                if keyword and keyword in term:
                    scores[sentiment] += 1
                    matches[sentiment].append(f"sentiment_keyword:{keyword}")
                    break

    if not scores:
        return None, []

    ordered_sentiments = ("positive", "negative", "neutral")
    sentiment = sorted(ordered_sentiments, key=lambda item: (-scores.get(item, 0), ordered_sentiments.index(item)))[0]
    return sentiment, matches[sentiment]
