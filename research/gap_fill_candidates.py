from __future__ import annotations

from collections.abc import Iterable

from .coverage_models import BackfillCandidate, GapRecord, PriceHistoryGap, WeakSignalCategory


def _examples_needed(current_sample_size: int, required_sample_size: int, missing_horizons: tuple[str, ...]) -> int:
    return max(required_sample_size - current_sample_size, len(missing_horizons), 1)


def _candidate_from_gap(gap: GapRecord, priority_rank: int) -> BackfillCandidate:
    required_examples = _examples_needed(gap.current_sample_size, gap.required_sample_size, gap.missing_horizons)

    if gap.gap_kind == "primary":
        title = f"Need {required_examples} more {gap.event_category} examples for {gap.ticker} primary studies"
        recommendation = (
            f"Add more structured {gap.event_category} history for {gap.ticker} so exact primary slices stop relying on category summaries."
        )
    elif gap.gap_kind == "related":
        title = f"Need {required_examples} more {gap.event_category} examples for {gap.ticker} related slices"
        recommendation = (
            f"Target {gap.event_category} examples that attach {gap.ticker} as a {gap.relationship_type} related company."
        )
    elif gap.gap_kind == "relationship":
        title = f"Need {required_examples} more {gap.event_category} examples for {gap.relationship_type} relationship studies"
        recommendation = (
            f"Backfill more {gap.event_category} events that exercise the {gap.relationship_type} relationship path across multiple tickers."
        )
    else:
        title = f"Need broader {gap.event_category} category depth"
        recommendation = (
            f"Add more balanced {gap.event_category} history so category summaries can produce stronger signal confidence separation."
        )

    return BackfillCandidate(
        candidate_key=gap.gap_key,
        priority_rank=priority_rank,
        gap_score=gap.gap_score,
        title=title,
        recommendation=recommendation,
        event_category=gap.event_category,
        target_type=gap.target_type,
        ticker=gap.ticker,
        relationship_type=gap.relationship_type,
        required_additional_examples=required_examples,
        rationale=gap.rationale,
    )


def _candidate_from_price_gap(price_gap: PriceHistoryGap, priority_rank: int) -> BackfillCandidate:
    title = f"Need broader price history for {price_gap.ticker}"
    recommendation = (
        f"Extend local price history for {price_gap.ticker} to at least {price_gap.required_days} trading days so its study slices remain usable."
    )
    return BackfillCandidate(
        candidate_key=f"price::{price_gap.ticker}",
        priority_rank=priority_rank,
        gap_score=price_gap.gap_score,
        title=title,
        recommendation=recommendation,
        event_category=None,
        target_type=None,
        ticker=price_gap.ticker,
        relationship_type=None,
        required_additional_examples=max(price_gap.required_days - price_gap.available_days, 1),
        rationale=(
            f"{price_gap.ticker} has {price_gap.available_days} price rows, "
            f"appears as primary {price_gap.referenced_as_primary} times and related {price_gap.referenced_as_related} times."
        ),
    )


def _candidate_from_weak_category(weak_category: WeakSignalCategory, priority_rank: int) -> BackfillCandidate:
    examples_needed = max(5 - weak_category.high, 1)
    return BackfillCandidate(
        candidate_key=f"category::{weak_category.event_category}",
        priority_rank=priority_rank,
        gap_score=weak_category.gap_score,
        title=f"Need {examples_needed} more {weak_category.event_category} examples to improve confidence mix",
        recommendation=(
            f"Expand {weak_category.event_category} history across primary and related slices so more signals move out of the low-confidence band."
        ),
        event_category=weak_category.event_category,
        target_type=None,
        ticker=None,
        relationship_type=None,
        required_additional_examples=examples_needed,
        rationale=(
            f"{weak_category.event_category} currently has {weak_category.high} high-confidence signals out of "
            f"{weak_category.total_signals} total."
        ),
    )


def generate_gap_fill_candidates(
    gaps: Iterable[GapRecord],
    price_gaps: Iterable[PriceHistoryGap],
    weak_categories: Iterable[WeakSignalCategory],
    limit: int = 12,
) -> list[BackfillCandidate]:
    ranked_inputs: list[tuple[float, str, object]] = []

    for gap in gaps:
        ranked_inputs.append((gap.gap_score, gap.gap_key, gap))

    for price_gap in price_gaps:
        ranked_inputs.append((price_gap.gap_score, f"price::{price_gap.ticker}", price_gap))

    for weak_category in weak_categories:
        ranked_inputs.append((weak_category.gap_score, f"category::{weak_category.event_category}", weak_category))

    ranked_inputs.sort(key=lambda item: (-item[0], item[1]))

    candidates: list[BackfillCandidate] = []
    for index, (_, _key, item) in enumerate(ranked_inputs[:limit], start=1):
        if isinstance(item, GapRecord):
            candidates.append(_candidate_from_gap(item, index))
        elif isinstance(item, PriceHistoryGap):
            candidates.append(_candidate_from_price_gap(item, index))
        else:
            candidates.append(_candidate_from_weak_category(item, index))

    return candidates
