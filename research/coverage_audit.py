from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any

try:
    from ingestion.write_to_supabase import SupabaseWriter
except ImportError:  # pragma: no cover - script execution fallback
    from write_to_supabase import SupabaseWriter  # type: ignore

from .coverage_models import (
    ConfidenceBandDistribution,
    CoverageAuditReport,
    CoverageEvent,
    CoverageRelationshipEdge,
    CoverageRelatedCompany,
    CoverageSignal,
    CoverageStudyStatistic,
    GapRecord,
    PriceHistoryGap,
    SampleSizeDistribution,
    WeakSignalCategory,
)
from .price_dataset import describe_resolution, load_resolved_price_series
from .gap_fill_candidates import generate_gap_fill_candidates


REQUIRED_HORIZONS = ("1D", "3D", "5D", "10D", "20D")
REQUIRED_SAMPLE_SIZES = {
    "primary": 6,
    "related": 5,
    "relationship": 6,
}
REQUIRED_PRICE_DAYS = 40
CATEGORY_IMPORTANCE = {
    "Macro Event": 1.0,
    "Product Launch": 0.95,
    "Earnings": 0.92,
    "Regulatory Approval": 0.9,
    "Legal/Regulatory": 0.88,
    "Supply Disruption": 0.84,
    "Partnership": 0.78,
    "Capital Expenditure": 0.76,
}
RELATIONSHIP_IMPORTANCE = {
    "Supplier": 1.0,
    "Competitor": 0.95,
    "Customer": 0.88,
    "Supply Chain Dependency": 0.9,
    "Regulatory Peer": 0.82,
    "Partner": 0.78,
    "Sector Peer": 0.7,
    "Related": 0.6,
}


def _study_count_key(event_category: str, horizon: str, target_type: str) -> str:
    return f"{event_category}::{horizon}::{target_type}"


def _safe_source_name(value: str | None) -> str:
    cleaned = (value or "unknown").strip()
    return cleaned or "unknown"


def _parse_source_study_target_type(rationale: dict[str, Any] | None) -> str | None:
    if not isinstance(rationale, dict):
        return None
    study = rationale.get("study")
    if not isinstance(study, dict):
        return None
    study_target_type = study.get("study_target_type")
    return str(study_target_type) if study_target_type else None


class CoverageAuditRepository(SupabaseWriter):
    def load_events(self) -> list[CoverageEvent]:
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select id::text, source_name, ticker, category
                    from public.events
                    order by category asc, ticker asc, id asc
                    """
                )
                rows = cursor.fetchall()

        return [
            CoverageEvent(
                id=event_id,
                source_name=_safe_source_name(source_name),
                ticker=ticker,
                category=category,
            )
            for event_id, source_name, ticker, category in rows
        ]

    def load_related_companies(self) -> list[CoverageRelatedCompany]:
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select
                      event_id::text,
                      source_ticker,
                      target_ticker,
                      coalesce(relationship_type, relationship) as relationship_type,
                      origin_type
                    from public.related_companies
                    where event_id is not null
                    order by event_id asc, target_ticker asc
                    """
                )
                rows = cursor.fetchall()

        return [
            CoverageRelatedCompany(
                event_id=event_id,
                source_ticker=source_ticker,
                target_ticker=target_ticker,
                relationship_type=relationship_type or "Related",
                origin_type=origin_type or "explicit",
            )
            for event_id, source_ticker, target_ticker, relationship_type, origin_type in rows
        ]

    def load_relationship_graph(self) -> list[CoverageRelationshipEdge]:
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select source_ticker, target_ticker, relationship_type, strength
                    from public.company_relationship_graph
                    order by source_ticker asc, target_ticker asc, relationship_type asc
                    """
                )
                rows = cursor.fetchall()

        return [
            CoverageRelationshipEdge(
                source_ticker=source_ticker,
                target_ticker=target_ticker,
                relationship_type=relationship_type,
                strength=float(strength or 0),
            )
            for source_ticker, target_ticker, relationship_type, strength in rows
        ]

    def load_study_statistics(self) -> list[CoverageStudyStatistic]:
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select
                      study_key,
                      study_target_type,
                      event_category,
                      primary_ticker,
                      related_ticker,
                      relationship_type,
                      horizon,
                      sample_size
                    from public.event_study_statistics
                    order by study_target_type asc, event_category asc, horizon asc
                    """
                )
                rows = cursor.fetchall()

        return [
            CoverageStudyStatistic(
                study_key=study_key,
                study_target_type=study_target_type,
                event_category=event_category,
                primary_ticker=primary_ticker,
                related_ticker=related_ticker,
                relationship_type=relationship_type,
                horizon=horizon,
                sample_size=sample_size,
            )
            for study_key, study_target_type, event_category, primary_ticker, related_ticker, relationship_type, horizon, sample_size in rows
        ]

    def load_signals(self) -> list[CoverageSignal]:
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select
                      event_category,
                      primary_ticker,
                      target_ticker,
                      target_type,
                      relationship_type,
                      horizon,
                      confidence_band,
                      rationale
                    from public.signal_scores
                    order by event_category asc, target_type asc, target_ticker asc, horizon asc
                    """
                )
                rows = cursor.fetchall()

        return [
            CoverageSignal(
                event_category=event_category,
                primary_ticker=primary_ticker,
                target_ticker=target_ticker,
                target_type=target_type,
                relationship_type=relationship_type,
                horizon=horizon,
                confidence_band=confidence_band,
                source_study_target_type=_parse_source_study_target_type(rationale or {}),
            )
            for event_category, primary_ticker, target_ticker, target_type, relationship_type, horizon, confidence_band, rationale in rows
        ]


def _build_sample_distribution(sample_sizes: list[int]) -> SampleSizeDistribution:
    ordered = sorted(sample_sizes)
    return SampleSizeDistribution(
        count=len(ordered),
        minimum=ordered[0],
        maximum=ordered[-1],
        average=round(sum(ordered) / len(ordered), 2),
        median=round(float(median(ordered)), 2),
    )


def aggregate_confidence_bands_by_category(signals: list[CoverageSignal]) -> dict[str, ConfidenceBandDistribution]:
    distribution: dict[str, Counter[str]] = defaultdict(Counter)
    for signal in signals:
        distribution[signal.event_category][signal.confidence_band] += 1

    return {
        category: ConfidenceBandDistribution(
            high=counts.get("High", 0),
            moderate=counts.get("Moderate", 0),
            low=counts.get("Low", 0),
        )
        for category, counts in sorted(distribution.items())
    }


def detect_missing_price_history(
    events: list[CoverageEvent],
    related_companies: list[CoverageRelatedCompany],
    relationship_graph: list[CoverageRelationshipEdge],
    price_days_by_ticker: dict[str, int],
    required_days: int = REQUIRED_PRICE_DAYS,
) -> list[PriceHistoryGap]:
    primary_counts = Counter(event.ticker for event in events)
    related_counts = Counter(related_company.target_ticker for related_company in related_companies)
    graph_counts = Counter()
    for edge in relationship_graph:
        graph_counts[edge.source_ticker] += 1
        graph_counts[edge.target_ticker] += 1

    all_tickers = sorted(set(primary_counts) | set(related_counts) | set(graph_counts))
    gaps: list[PriceHistoryGap] = []
    for ticker in all_tickers:
        available_days = price_days_by_ticker.get(ticker, 0)
        if available_days >= required_days:
            continue

        gap_score = round(
            (required_days - available_days) * 1.25
            + primary_counts.get(ticker, 0) * 3.0
            + related_counts.get(ticker, 0) * 1.8
            + graph_counts.get(ticker, 0) * 0.5,
            2,
        )
        gaps.append(
            PriceHistoryGap(
                ticker=ticker,
                available_days=available_days,
                required_days=required_days,
                referenced_as_primary=primary_counts.get(ticker, 0),
                referenced_as_related=related_counts.get(ticker, 0),
                graph_degree=graph_counts.get(ticker, 0),
                gap_score=gap_score,
            )
        )

    return sorted(gaps, key=lambda gap: (-gap.gap_score, gap.ticker))


def detect_sparse_study_slices(
    studies: list[CoverageStudyStatistic],
    events: list[CoverageEvent],
    related_companies: list[CoverageRelatedCompany],
    signals: list[CoverageSignal],
) -> tuple[list[GapRecord], list[GapRecord], list[GapRecord]]:
    study_groups: dict[tuple[str, str, str | None, str | None], dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for study in studies:
        if study.study_target_type not in {"primary", "related", "relationship"}:
            continue
        if study.study_target_type == "primary":
            group_key = ("primary", study.event_category, study.primary_ticker, None)
        elif study.study_target_type == "related":
            group_key = ("related", study.event_category, study.related_ticker, study.relationship_type)
        else:
            group_key = ("relationship", study.event_category, None, study.relationship_type)
        study_groups[group_key][study.horizon] += study.sample_size

    primary_event_counts = Counter((event.category, event.ticker) for event in events)
    # Build a direct event lookup for related company category counts.
    event_lookup = {event.id: event for event in events}
    related_slice_counts = Counter()
    relationship_slice_counts = Counter()
    for related_company in related_companies:
        event = event_lookup.get(related_company.event_id)
        if event is None:
            continue
        related_slice_counts[(event.category, related_company.target_ticker, related_company.relationship_type)] += 1
        relationship_slice_counts[(event.category, related_company.relationship_type)] += 1

    primary_signal_usage = Counter((signal.event_category, signal.primary_ticker) for signal in signals if signal.target_type == "primary")
    related_signal_usage = Counter(
        (signal.event_category, signal.target_ticker, signal.relationship_type or "Related")
        for signal in signals
        if signal.target_type == "related"
    )
    relationship_signal_usage = Counter(
        (signal.event_category, signal.relationship_type or "Related")
        for signal in signals
        if signal.target_type == "related"
    )

    primary_fallback_usage = Counter(
        (signal.event_category, signal.primary_ticker)
        for signal in signals
        if signal.target_type == "primary" and signal.source_study_target_type == "category_summary"
    )
    related_fallback_usage = Counter(
        (signal.event_category, signal.target_ticker, signal.relationship_type or "Related")
        for signal in signals
        if signal.target_type == "related" and signal.source_study_target_type == "relationship"
    )

    primary_gaps: list[GapRecord] = []
    related_gaps: list[GapRecord] = []
    relationship_gaps: list[GapRecord] = []

    primary_keys = sorted(set(primary_event_counts) | set(primary_signal_usage) | set(primary_fallback_usage))
    for event_category, ticker in primary_keys:
        horizons = study_groups.get(("primary", event_category, ticker, None), {})
        sample_size = min(horizons.values()) if horizons else 0
        missing_horizons = tuple(horizon for horizon in REQUIRED_HORIZONS if horizon not in horizons)
        fallback_count = primary_fallback_usage.get((event_category, ticker), 0)
        signal_usage = primary_signal_usage.get((event_category, ticker), 0)
        required = REQUIRED_SAMPLE_SIZES["primary"]
        if sample_size >= required and not missing_horizons and fallback_count == 0:
            continue
        importance = CATEGORY_IMPORTANCE.get(event_category, 0.7)
        gap_score = round(
            importance * 14
            + max(required - sample_size, 0) * 5.0
            + len(missing_horizons) * 3.0
            + fallback_count * 2.5
            + signal_usage * 0.8,
            2,
        )
        primary_gaps.append(
            GapRecord(
                gap_key=f"primary::{event_category}::{ticker}",
                gap_kind="primary",
                event_category=event_category,
                target_type="primary",
                ticker=ticker,
                relationship_type=None,
                current_sample_size=sample_size,
                required_sample_size=required,
                missing_horizons=missing_horizons,
                signal_usage_count=signal_usage,
                fallback_usage_count=fallback_count,
                gap_score=gap_score,
                rationale=(
                    f"{event_category} primary slice for {ticker} has sample {sample_size}, "
                    f"missing horizons {list(missing_horizons)}, fallback usage {fallback_count}, signal usage {signal_usage}."
                ),
            )
        )

    related_keys = sorted(set(related_slice_counts) | set(related_signal_usage) | set(related_fallback_usage))
    for event_category, ticker, relationship_type in related_keys:
        horizons = study_groups.get(("related", event_category, ticker, relationship_type), {})
        sample_size = min(horizons.values()) if horizons else 0
        missing_horizons = tuple(horizon for horizon in REQUIRED_HORIZONS if horizon not in horizons)
        fallback_count = related_fallback_usage.get((event_category, ticker, relationship_type), 0)
        signal_usage = related_signal_usage.get((event_category, ticker, relationship_type), 0)
        required = REQUIRED_SAMPLE_SIZES["related"]
        if sample_size >= required and not missing_horizons and fallback_count == 0:
            continue
        importance = CATEGORY_IMPORTANCE.get(event_category, 0.7) + RELATIONSHIP_IMPORTANCE.get(relationship_type, 0.6)
        gap_score = round(
            importance * 8
            + max(required - sample_size, 0) * 4.5
            + len(missing_horizons) * 2.5
            + fallback_count * 2.25
            + signal_usage * 0.7,
            2,
        )
        related_gaps.append(
            GapRecord(
                gap_key=f"related::{event_category}::{ticker}::{relationship_type}",
                gap_kind="related",
                event_category=event_category,
                target_type="related",
                ticker=ticker,
                relationship_type=relationship_type,
                current_sample_size=sample_size,
                required_sample_size=required,
                missing_horizons=missing_horizons,
                signal_usage_count=signal_usage,
                fallback_usage_count=fallback_count,
                gap_score=gap_score,
                rationale=(
                    f"{event_category} related slice for {ticker} / {relationship_type} has sample {sample_size}, "
                    f"missing horizons {list(missing_horizons)}, fallback usage {fallback_count}, signal usage {signal_usage}."
                ),
            )
        )

    relationship_keys = sorted(set(relationship_slice_counts) | set(relationship_signal_usage))
    for event_category, relationship_type in relationship_keys:
        horizons = study_groups.get(("relationship", event_category, None, relationship_type), {})
        sample_size = min(horizons.values()) if horizons else 0
        missing_horizons = tuple(horizon for horizon in REQUIRED_HORIZONS if horizon not in horizons)
        signal_usage = relationship_signal_usage.get((event_category, relationship_type), 0)
        required = REQUIRED_SAMPLE_SIZES["relationship"]
        if sample_size >= required and not missing_horizons:
            continue
        importance = CATEGORY_IMPORTANCE.get(event_category, 0.7) + RELATIONSHIP_IMPORTANCE.get(relationship_type, 0.6)
        gap_score = round(
            importance * 7
            + max(required - sample_size, 0) * 4.0
            + len(missing_horizons) * 2.0
            + signal_usage * 0.6,
            2,
        )
        relationship_gaps.append(
            GapRecord(
                gap_key=f"relationship::{event_category}::{relationship_type}",
                gap_kind="relationship",
                event_category=event_category,
                target_type="related",
                ticker=None,
                relationship_type=relationship_type,
                current_sample_size=sample_size,
                required_sample_size=required,
                missing_horizons=missing_horizons,
                signal_usage_count=signal_usage,
                fallback_usage_count=0,
                gap_score=gap_score,
                rationale=(
                    f"{event_category} relationship slice for {relationship_type} has sample {sample_size}, "
                    f"missing horizons {list(missing_horizons)}, signal usage {signal_usage}."
                ),
            )
        )

    primary_gaps.sort(key=lambda gap: (-gap.gap_score, gap.gap_key))
    related_gaps.sort(key=lambda gap: (-gap.gap_score, gap.gap_key))
    relationship_gaps.sort(key=lambda gap: (-gap.gap_score, gap.gap_key))
    return primary_gaps, related_gaps, relationship_gaps


def identify_weak_signal_categories(signals: list[CoverageSignal]) -> list[WeakSignalCategory]:
    grouped = aggregate_confidence_bands_by_category(signals)
    weak_categories: list[WeakSignalCategory] = []
    for category, distribution in grouped.items():
        total = distribution.high + distribution.moderate + distribution.low
        if total == 0:
            continue
        high_ratio = distribution.high / total
        if distribution.high > 0 and high_ratio >= 0.05:
            continue
        importance = CATEGORY_IMPORTANCE.get(category, 0.7)
        gap_score = round((1 - high_ratio) * 25 + distribution.low * 0.04 + importance * 10, 2)
        weak_categories.append(
            WeakSignalCategory(
                event_category=category,
                total_signals=total,
                high=distribution.high,
                moderate=distribution.moderate,
                low=distribution.low,
                high_confidence_ratio=round(high_ratio, 4),
                gap_score=gap_score,
            )
        )

    weak_categories.sort(key=lambda item: (-item.gap_score, item.event_category))
    return weak_categories


def build_markdown_report(report: CoverageAuditReport) -> str:
    lines = [
        "# Coverage Audit",
        "",
        "## Event Coverage",
    ]
    for category, count in report.event_counts_by_category.items():
        lines.append(f"- {category}: {count} events")

    lines.extend(["", "## Source Coverage"])
    for source_name, count in report.event_counts_by_source.items():
        lines.append(f"- {source_name}: {count} events")

    lines.extend(["", "## Weak Signal Categories"])
    if report.weak_signal_categories:
        for item in report.weak_signal_categories:
            lines.append(
                f"- {item.event_category}: high={item.high}, moderate={item.moderate}, low={item.low}, "
                f"high_ratio={item.high_confidence_ratio:.2%}, gap_score={item.gap_score}"
            )
    else:
        lines.append("- None")

    lines.extend(["", "## Top Gap Candidates"])
    for candidate in report.top_gap_candidates:
        lines.append(
            f"- #{candidate.priority_rank} {candidate.title} (gap_score={candidate.gap_score})"
        )
        lines.append(f"  Recommendation: {candidate.recommendation}")
        lines.append(f"  Rationale: {candidate.rationale}")

    lines.extend(["", "## Sparse Primary Slices"])
    for gap in report.sparse_primary_slices[:10]:
        lines.append(
            f"- {gap.event_category} / {gap.ticker}: sample={gap.current_sample_size}, "
            f"fallbacks={gap.fallback_usage_count}, missing_horizons={list(gap.missing_horizons)}, gap_score={gap.gap_score}"
        )

    lines.extend(["", "## Sparse Related Slices"])
    for gap in report.sparse_related_slices[:10]:
        lines.append(
            f"- {gap.event_category} / {gap.ticker} / {gap.relationship_type}: sample={gap.current_sample_size}, "
            f"fallbacks={gap.fallback_usage_count}, missing_horizons={list(gap.missing_horizons)}, gap_score={gap.gap_score}"
        )

    lines.extend(["", "## Sparse Relationship Slices"])
    for gap in report.sparse_relationship_slices[:10]:
        lines.append(
            f"- {gap.event_category} / {gap.relationship_type}: sample={gap.current_sample_size}, "
            f"missing_horizons={list(gap.missing_horizons)}, gap_score={gap.gap_score}"
        )

    lines.extend(["", "## Missing Price History"])
    if report.missing_price_history:
        for gap in report.missing_price_history:
            lines.append(
                f"- {gap.ticker}: available_days={gap.available_days}, required_days={gap.required_days}, gap_score={gap.gap_score}"
            )
    else:
        lines.append("- No current price-history gaps detected for referenced tickers.")

    return "\n".join(lines) + "\n"


def build_coverage_audit_report(
    events: list[CoverageEvent],
    related_companies: list[CoverageRelatedCompany],
    relationship_graph: list[CoverageRelationshipEdge],
    studies: list[CoverageStudyStatistic],
    signals: list[CoverageSignal],
    price_days_by_ticker: dict[str, int],
    price_file: str | Path,
) -> CoverageAuditReport:
    event_counts_by_category = dict(sorted(Counter(event.category for event in events).items()))
    event_counts_by_source = dict(sorted(Counter(event.source_name for event in events).items()))

    study_counts = Counter(
        _study_count_key(study.event_category, study.horizon, study.study_target_type)
        for study in studies
    )
    study_counts_by_category_horizon_target = dict(sorted(study_counts.items()))

    sample_sizes_by_category: dict[str, list[int]] = defaultdict(list)
    for study in studies:
        sample_sizes_by_category[study.event_category].append(study.sample_size)
    sample_size_distribution_by_category = {
        category: _build_sample_distribution(sample_sizes)
        for category, sample_sizes in sorted(sample_sizes_by_category.items())
    }

    confidence_band_distribution_by_category = aggregate_confidence_bands_by_category(signals)
    sparse_primary, sparse_related, sparse_relationship = detect_sparse_study_slices(
        studies,
        events,
        related_companies,
        signals,
    )
    price_gaps = detect_missing_price_history(events, related_companies, relationship_graph, price_days_by_ticker)
    weak_categories = identify_weak_signal_categories(signals)
    top_candidates = generate_gap_fill_candidates(
        [*sparse_primary, *sparse_related, *sparse_relationship],
        price_gaps,
        weak_categories,
    )

    return CoverageAuditReport(
        event_counts_by_category=event_counts_by_category,
        event_counts_by_source=event_counts_by_source,
        study_counts_by_category_horizon_target=study_counts_by_category_horizon_target,
        sample_size_distribution_by_category=sample_size_distribution_by_category,
        confidence_band_distribution_by_category=confidence_band_distribution_by_category,
        sparse_primary_slices=tuple(sparse_primary),
        sparse_related_slices=tuple(sparse_related),
        sparse_relationship_slices=tuple(sparse_relationship),
        missing_price_history=tuple(price_gaps),
        weak_signal_categories=tuple(weak_categories),
        top_gap_candidates=tuple(top_candidates),
        notes={
            "required_horizons": list(REQUIRED_HORIZONS),
            "required_sample_sizes": REQUIRED_SAMPLE_SIZES,
            "required_price_days": REQUIRED_PRICE_DAYS,
            "price_file": str(price_file),
        },
    )


def run_coverage_audit(repo_root: Path, price_file: str | Path | None) -> CoverageAuditReport:
    repository = CoverageAuditRepository(repo_root)
    events = repository.load_events()
    related_companies = repository.load_related_companies()
    relationship_graph = repository.load_relationship_graph()
    studies = repository.load_study_statistics()
    signals = repository.load_signals()
    requested_tickers = {event.ticker for event in events}
    requested_tickers.update(related_company.target_ticker for related_company in related_companies)
    for edge in relationship_graph:
        requested_tickers.add(edge.source_ticker)
        requested_tickers.add(edge.target_ticker)
    price_series, resolved_price_dataset = load_resolved_price_series(
        repo_root,
        price_file,
        tickers=requested_tickers,
    )
    price_days_by_ticker = {series.ticker: len(series.prices) for series in price_series}

    report = build_coverage_audit_report(
        events=events,
        related_companies=related_companies,
        relationship_graph=relationship_graph,
        studies=studies,
        signals=signals,
        price_days_by_ticker=price_days_by_ticker,
        price_file=resolved_price_dataset.path,
    )
    report.notes["price_resolution_reason"] = resolved_price_dataset.resolution_reason
    report.notes["price_format"] = resolved_price_dataset.format
    report.notes["price_used_sample_fallback"] = resolved_price_dataset.used_sample_fallback
    report.notes["price_ticker_filter_count"] = len(requested_tickers)
    report.notes["price_resolution"] = describe_resolution(resolved_price_dataset)
    return report


def write_coverage_reports(report: CoverageAuditReport, json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    markdown_path.write_text(build_markdown_report(report), encoding="utf-8")
