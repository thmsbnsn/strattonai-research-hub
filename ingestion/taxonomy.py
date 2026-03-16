from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CategoryDefinition:
    name: str
    aliases: tuple[str, ...]
    keyword_triggers: tuple[str, ...]
    default_sentiment: str
    confidence_note: str


@dataclass(frozen=True, slots=True)
class SourceHints:
    form_type_defaults: dict[str, str]


@dataclass(frozen=True, slots=True)
class TaxonomyConfig:
    categories: tuple[CategoryDefinition, ...]
    sentiment_aliases: dict[str, str]
    sentiment_keywords: dict[str, tuple[str, ...]]
    source_hints: dict[str, SourceHints]


def _config_path() -> Path:
    return Path(__file__).resolve().with_name("taxonomy_config.json")


@lru_cache(maxsize=1)
def load_taxonomy_config() -> TaxonomyConfig:
    payload = json.loads(_config_path().read_text(encoding="utf-8"))

    categories = tuple(
        CategoryDefinition(
            name=entry["name"],
            aliases=tuple(alias.lower() for alias in entry.get("aliases", [])),
            keyword_triggers=tuple(trigger.lower() for trigger in entry.get("keyword_triggers", [])),
            default_sentiment=entry.get("default_sentiment", "neutral"),
            confidence_note=entry.get("confidence_note", ""),
        )
        for entry in payload.get("categories", [])
    )

    sentiment_aliases = {
        key.lower(): value
        for key, value in payload.get("sentiment_aliases", {}).items()
    }

    sentiment_keywords = {
        sentiment: tuple(keyword.lower() for keyword in keywords)
        for sentiment, keywords in payload.get("sentiment_keywords", {}).items()
    }

    source_hints = {
        source_name: SourceHints(
            form_type_defaults={
                form_type.lower(): category
                for form_type, category in source_data.get("form_type_defaults", {}).items()
            }
        )
        for source_name, source_data in payload.get("source_hints", {}).items()
    }

    return TaxonomyConfig(
        categories=categories,
        sentiment_aliases=sentiment_aliases,
        sentiment_keywords=sentiment_keywords,
        source_hints=source_hints,
    )


def get_category_definition(category_name: str) -> CategoryDefinition | None:
    config = load_taxonomy_config()
    for category in config.categories:
        if category.name == category_name:
            return category
    return None
