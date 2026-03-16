from __future__ import annotations

import argparse
import json
import logging
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ingestion.inspect_financial_news_dataset import build_markdown_report as build_inspection_markdown
from ingestion.inspect_financial_news_dataset import inspect_financial_news_dataset
from ingestion.load_price_series_file import inspect_price_series_file
from ingestion.run_ingestion import load_records, normalize_records_with_diagnostics
from ingestion.write_to_supabase import SupabaseWriter

from .build_targeted_backfill_plan import build_targeted_backfill_plan, write_targeted_backfill_plan
from .coverage_audit import run_coverage_audit, write_coverage_reports
from .coverage_audit_diff import CoverageSnapshotRepository, build_comparison_summary, write_comparison_artifacts
from .event_study_engine import aggregate_observations, build_price_map, compute_event_study_observations
from .massive_price_backfill import MassiveBackfillReport, build_markdown_report as build_backfill_markdown
from .massive_price_backfill import run_massive_price_backfill
from .price_dataset import collect_study_tickers, describe_resolution, load_resolved_price_series, resolve_price_dataset_path
from .signal_scoring import index_studies, score_event_signals
from .targeted_expansion_baseline import build_targeted_expansion_baseline
from .write_event_studies_to_supabase import EventStudySupabaseWriter
from .write_signals_to_supabase import SignalSupabaseWriter


LOGGER = logging.getLogger("research.run_financial_news_alignment")
FOCUSED_RELATED_SLICES = (
    ("Capital Expenditure", "ORCL", "Sector Peer"),
    ("Capital Expenditure", "AMZN", "Competitor"),
    ("Capital Expenditure", "GOOGL", "Competitor"),
    ("Legal/Regulatory", "GOOGL", "Sector Peer"),
    ("Legal/Regulatory", "META", "Sector Peer"),
    ("Partnership", "TSM", "Supplier"),
    ("Partnership", "MSFT", "Customer"),
    ("Partnership", "AVGO", "Sector Peer"),
    ("Product Launch", "GOOGL", "Competitor"),
)
FOCUSED_PRIMARY_SLICES = (
    ("Macro Event", "AAPL"),
    ("Macro Event", "MSFT"),
    ("Macro Event", "NVDA"),
)


@dataclass(frozen=True, slots=True)
class NewsIngestionSummary:
    input_records: int
    normalized_records: int
    skipped_records: int
    failed_records: int
    category_counts: dict[str, int]
    ticker_counts: dict[str, int]
    skip_reason_counts: dict[str, int]
    excluded_event_identities: tuple[dict[str, str], ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PriceCoverageSummary:
    path: str
    format: str
    row_count: int
    distinct_ticker_count: int
    min_date: str | None
    max_date: str | None
    requested_ticker_count: int
    requested_covered_ticker_count: int
    requested_uncovered_tickers: tuple[str, ...]
    resolution_reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class StudyComputationSummary:
    event_count: int
    requested_ticker_count: int
    observation_count: int
    aggregate_count: int
    category_summary_count: int
    missing_primary_series: int
    missing_related_series: int
    missing_horizon: int
    events_with_primary_observation: int
    events_with_any_observation: int
    events_with_related_observation: int
    events_without_any_observation: int
    out_of_range_event_ids_sample: tuple[str, ...]
    resolved_price_dataset: str
    resolution_reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SignalScoringSummary:
    recent_event_count: int
    study_statistic_count: int
    signal_count: int
    confidence_distribution: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format="%(levelname)s %(message)s")


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description="Ingest local financial-news events, extend local price coverage from Massive, and regenerate research outputs."
    )
    parser.add_argument("--news-input-dir", default=str(repo_root.parent / "data" / "events" / "financialNews"))
    parser.add_argument("--price-file", default=None)
    parser.add_argument("--lookback-days", type=int, default=120)
    parser.add_argument("--limit-events", type=int, default=500)
    parser.add_argument("--inspection-json", default=str(repo_root / "reports" / "financial_news_dataset_inspection.json"))
    parser.add_argument("--inspection-markdown", default=str(repo_root / "reports" / "financial_news_dataset_inspection.md"))
    parser.add_argument("--before-coverage-json", default=str(repo_root / "reports" / "coverage_audit_before_news_alignment.json"))
    parser.add_argument("--before-coverage-markdown", default=str(repo_root / "reports" / "coverage_audit_before_news_alignment.md"))
    parser.add_argument("--after-coverage-json", default=str(repo_root / "reports" / "coverage_audit_after_news_alignment.json"))
    parser.add_argument("--after-coverage-markdown", default=str(repo_root / "reports" / "coverage_audit_after_news_alignment.md"))
    parser.add_argument("--coverage-diff-json", default=str(repo_root / "reports" / "coverage_audit_diff_news_alignment.json"))
    parser.add_argument("--coverage-diff-markdown", default=str(repo_root / "reports" / "coverage_audit_diff_news_alignment.md"))
    parser.add_argument("--before-json", default=str(repo_root / "reports" / "financial_news_alignment_before.json"))
    parser.add_argument("--after-json", default=str(repo_root / "reports" / "financial_news_alignment_after.json"))
    parser.add_argument("--diff-json", default=str(repo_root / "reports" / "financial_news_alignment_diff.json"))
    parser.add_argument("--diff-markdown", default=str(repo_root / "reports" / "financial_news_alignment_diff.md"))
    parser.add_argument("--backfill-json", default=str(repo_root / "reports" / "massive_price_backfill.json"))
    parser.add_argument("--backfill-markdown", default=str(repo_root / "reports" / "massive_price_backfill.md"))
    parser.add_argument("--planner-json", default=str(repo_root / "reports" / "targeted_backfill_plan_after_news_alignment.json"))
    parser.add_argument("--planner-markdown", default=str(repo_root / "reports" / "targeted_backfill_plan_after_news_alignment.md"))
    parser.add_argument("--skip-backfill", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def _resolve_base_price_path(repo_root: Path) -> Path:
    try:
        return resolve_price_dataset_path(repo_root, "data/prices/all_stock_data.parquet", allow_sample_fallback=False).path
    except FileNotFoundError:
        return resolve_price_dataset_path(repo_root, "data/prices/all_stock_data.csv", allow_sample_fallback=False).path


def _write_json_and_markdown(payload: dict[str, Any], json_path: Path, markdown_path: Path, markdown: str) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    markdown_path.write_text(markdown, encoding="utf-8")


def _write_json(payload: dict[str, Any], json_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _build_news_ingestion_summary(news_input_file: Path) -> tuple[NewsIngestionSummary, list[Any], list[Any]]:
    raw_records = load_records("financial-news", str(news_input_file))
    normalized_records, failures, skipped = normalize_records_with_diagnostics(
        "financial-news",
        raw_records,
        log_each_record=False,
    )
    summary = NewsIngestionSummary(
        input_records=len(raw_records),
        normalized_records=len(normalized_records),
        skipped_records=len(skipped),
        failed_records=len(failures),
        category_counts=dict(sorted(Counter(event.category for event in normalized_records).items())),
        ticker_counts=dict(sorted(Counter(event.ticker for event in normalized_records).items())),
        skip_reason_counts=dict(sorted(Counter(item.reason for item in skipped).items())),
        excluded_event_identities=tuple(
            {"source_name": event.source_name, "source_record_id": event.source_record_id}
            for event in normalized_records
        ),
    )
    return summary, normalized_records, failures


def _build_price_coverage_summary(repo_root: Path, price_file: str | Path, requested_tickers: set[str]) -> PriceCoverageSummary:
    inspection = inspect_price_series_file(price_file)
    filtered_series, resolved = load_resolved_price_series(
        repo_root,
        price_file,
        tickers=requested_tickers,
        allow_sample_fallback=False,
    )
    covered_tickers = {series.ticker for series in filtered_series}
    return PriceCoverageSummary(
        path=str(resolved.path),
        format=resolved.format,
        row_count=inspection.row_count,
        distinct_ticker_count=inspection.distinct_ticker_count,
        min_date=inspection.min_date,
        max_date=inspection.max_date,
        requested_ticker_count=len(requested_tickers),
        requested_covered_ticker_count=len(covered_tickers),
        requested_uncovered_tickers=tuple(sorted(requested_tickers - covered_tickers)),
        resolution_reason=resolved.resolution_reason,
    )


def _build_study_summary(repo_root: Path, price_file: str | Path, *, write_results: bool) -> StudyComputationSummary:
    writer = EventStudySupabaseWriter(repo_root)
    events = writer.load_study_events()
    requested_tickers = collect_study_tickers(events)
    price_series, resolved = load_resolved_price_series(
        repo_root,
        price_file,
        tickers=requested_tickers,
        allow_sample_fallback=False,
    )
    LOGGER.info("Using price dataset %s for event-study recompute.", describe_resolution(resolved))
    price_map = build_price_map(price_series)
    observations, stats = compute_event_study_observations(events, price_map)
    aggregates = aggregate_observations(observations)

    if write_results:
        writer.upsert_event_study_aggregates(aggregates)
        writer.upsert_ui_summary_rows(aggregates)

    any_observation_ids = {observation.event_id for observation in observations}
    primary_observation_ids = {observation.event_id for observation in observations if observation.study_target_type == "primary"}
    related_observation_ids = {observation.event_id for observation in observations if observation.study_target_type == "related"}
    out_of_range = [event.id for event in events if event.id not in any_observation_ids]

    return StudyComputationSummary(
        event_count=len(events),
        requested_ticker_count=len(requested_tickers),
        observation_count=len(observations),
        aggregate_count=len(aggregates),
        category_summary_count=sum(1 for aggregate in aggregates if aggregate.study_target_type == "category_summary"),
        missing_primary_series=stats["missing_primary_series"],
        missing_related_series=stats["missing_related_series"],
        missing_horizon=stats["missing_horizon"],
        events_with_primary_observation=len(primary_observation_ids),
        events_with_any_observation=len(any_observation_ids),
        events_with_related_observation=len(related_observation_ids),
        events_without_any_observation=len(out_of_range),
        out_of_range_event_ids_sample=tuple(sorted(out_of_range)[:20]),
        resolved_price_dataset=str(resolved.path),
        resolution_reason=resolved.resolution_reason,
    )


def _build_signal_summary(repo_root: Path, *, lookback_days: int, limit_events: int, write_results: bool) -> SignalScoringSummary:
    writer = SignalSupabaseWriter(repo_root)
    events = writer.load_recent_signal_events(lookback_days=lookback_days, limit_events=limit_events)
    studies = writer.load_signal_study_statistics()
    indexed_studies = index_studies(studies)
    now = datetime.now(UTC)
    signals = []
    for event in events:
        signals.extend(score_event_signals(event, indexed_studies, now=now))

    if write_results:
        writer.upsert_signal_scores(signals)

    return SignalScoringSummary(
        recent_event_count=len(events),
        study_statistic_count=len(studies),
        signal_count=len(signals),
        confidence_distribution=dict(sorted(Counter(signal.confidence_band for signal in signals).items())),
    )


def _build_summary_dict(
    *,
    reference_time: datetime,
    news_summary: NewsIngestionSummary,
    price_summary: PriceCoverageSummary,
    study_summary: StudyComputationSummary,
    signal_summary: SignalScoringSummary,
    coverage_report: dict[str, Any],
    backfill_report: MassiveBackfillReport | None = None,
    planner: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "reference_time": reference_time.isoformat(),
        "news_ingestion": news_summary.to_dict(),
        "price_coverage": price_summary.to_dict(),
        "study_recompute": study_summary.to_dict(),
        "signal_scoring": signal_summary.to_dict(),
        "coverage_audit": {
            "event_counts_by_category": coverage_report.get("event_counts_by_category", {}),
            "event_counts_by_source": coverage_report.get("event_counts_by_source", {}),
            "confidence_band_distribution_by_category": coverage_report.get("confidence_band_distribution_by_category", {}),
            "top_gap_candidates": coverage_report.get("top_gap_candidates", [])[:10],
        },
    }
    if backfill_report is not None:
        payload["massive_backfill"] = backfill_report.to_dict()
    if planner is not None:
        payload["targeted_backfill_plan"] = {
            "plan_items": planner.get("plan_items", [])[:12],
            "groups": planner.get("groups", []),
        }
    return payload


def _build_alignment_diff(
    before_summary: dict[str, Any],
    after_summary: dict[str, Any],
    coverage_diff_summary: dict[str, Any],
) -> dict[str, Any]:
    before_categories = before_summary["coverage_audit"]["event_counts_by_category"]
    after_categories = after_summary["coverage_audit"]["event_counts_by_category"]
    category_names = sorted(set(before_categories) | set(after_categories))
    return {
        "total_events": {
            "before": sum(before_categories.values()),
            "after": sum(after_categories.values()),
            "delta": sum(after_categories.values()) - sum(before_categories.values()),
        },
        "news_ingested_event_count": after_summary["news_ingestion"]["normalized_records"],
        "event_counts_by_category": [
            {
                "event_category": category,
                "before": before_categories.get(category, 0),
                "after": after_categories.get(category, 0),
                "delta": after_categories.get(category, 0) - before_categories.get(category, 0),
            }
            for category in category_names
        ],
        "price_coverage": {
            "before_max_date": before_summary["price_coverage"]["max_date"],
            "after_max_date": after_summary["price_coverage"]["max_date"],
            "requested_uncovered_tickers_before": before_summary["price_coverage"]["requested_uncovered_tickers"],
            "requested_uncovered_tickers_after": after_summary["price_coverage"]["requested_uncovered_tickers"],
        },
        "study_recompute": {
            "observations_before": before_summary["study_recompute"]["observation_count"],
            "observations_after": after_summary["study_recompute"]["observation_count"],
            "observation_delta": after_summary["study_recompute"]["observation_count"] - before_summary["study_recompute"]["observation_count"],
            "aggregate_rows_before": before_summary["study_recompute"]["aggregate_count"],
            "aggregate_rows_after": after_summary["study_recompute"]["aggregate_count"],
            "aggregate_row_delta": after_summary["study_recompute"]["aggregate_count"] - before_summary["study_recompute"]["aggregate_count"],
            "events_without_any_observation_before": before_summary["study_recompute"]["events_without_any_observation"],
            "events_without_any_observation_after": after_summary["study_recompute"]["events_without_any_observation"],
        },
        "signal_scoring": {
            "signals_before": before_summary["signal_scoring"]["signal_count"],
            "signals_after": after_summary["signal_scoring"]["signal_count"],
            "signal_delta": after_summary["signal_scoring"]["signal_count"] - before_summary["signal_scoring"]["signal_count"],
            "confidence_before": before_summary["signal_scoring"]["confidence_distribution"],
            "confidence_after": after_summary["signal_scoring"]["confidence_distribution"],
        },
        "coverage_diff": coverage_diff_summary,
        "remaining_top_gap_candidates": after_summary["coverage_audit"]["top_gap_candidates"],
        "remaining_uncovered_event_ids_sample": after_summary["study_recompute"]["out_of_range_event_ids_sample"],
    }


def _build_alignment_diff_markdown(diff: dict[str, Any]) -> str:
    lines = [
        "# Financial News Alignment Diff",
        "",
        "## Events",
        f"- Total events: {diff['total_events']['before']} -> {diff['total_events']['after']} (delta {diff['total_events']['delta']:+d})",
        f"- News-ingested events added through the deterministic pipeline: {diff['news_ingested_event_count']}",
        "",
        "## Category Counts",
    ]
    for item in diff["event_counts_by_category"]:
        lines.append(f"- {item['event_category']}: {item['before']} -> {item['after']} (delta {item['delta']:+d})")

    lines.extend(
        [
            "",
            "## Price Coverage",
            f"- Local price max date: {diff['price_coverage']['before_max_date']} -> {diff['price_coverage']['after_max_date']}",
            "- Requested uncovered tickers before: " + (", ".join(diff["price_coverage"]["requested_uncovered_tickers_before"]) or "None"),
            "- Requested uncovered tickers after: " + (", ".join(diff["price_coverage"]["requested_uncovered_tickers_after"]) or "None"),
            "",
            "## Event Studies",
            f"- Valid observations: {diff['study_recompute']['observations_before']} -> {diff['study_recompute']['observations_after']} (delta {diff['study_recompute']['observation_delta']:+d})",
            f"- Aggregate study rows: {diff['study_recompute']['aggregate_rows_before']} -> {diff['study_recompute']['aggregate_rows_after']} (delta {diff['study_recompute']['aggregate_row_delta']:+d})",
            (
                f"- Events without any valid observation: {diff['study_recompute']['events_without_any_observation_before']} -> "
                f"{diff['study_recompute']['events_without_any_observation_after']}"
            ),
            "",
            "## Signals",
            f"- Signal count: {diff['signal_scoring']['signals_before']} -> {diff['signal_scoring']['signals_after']} (delta {diff['signal_scoring']['signal_delta']:+d})",
            f"- Confidence bands before: {diff['signal_scoring']['confidence_before']}",
            f"- Confidence bands after: {diff['signal_scoring']['confidence_after']}",
            "",
            "## Remaining Weak Slices",
        ]
    )
    for candidate in diff["remaining_top_gap_candidates"]:
        lines.append(f"- {candidate['candidate_key']}: needs {candidate['required_additional_examples']} more example(s).")

    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)

    repo_root = Path(__file__).resolve().parent.parent
    reference_time = datetime.now(UTC)

    inspection_report = inspect_financial_news_dataset(Path(args.news_input_dir))
    _write_json_and_markdown(
        inspection_report,
        Path(args.inspection_json),
        Path(args.inspection_markdown),
        build_inspection_markdown(inspection_report),
    )
    canonical_news_file = Path(inspection_report["canonical_file"])
    news_summary, normalized_news_events, failures = _build_news_ingestion_summary(canonical_news_file)
    if failures:
        for failure in failures:
            LOGGER.error("Financial-news normalization failure for record %s: %s", failure.record_index, failure.reason)
        return 1

    excluded_identities = {
        (record["source_name"], record["source_record_id"])
        for record in news_summary.excluded_event_identities
    }
    base_price_path = _resolve_base_price_path(repo_root)
    before_baseline = build_targeted_expansion_baseline(
        repo_root=repo_root,
        price_file=base_price_path,
        excluded_identities=excluded_identities,
        now=reference_time,
        focused_related_slices=FOCUSED_RELATED_SLICES,
        focused_primary_slices=FOCUSED_PRIMARY_SLICES,
    )
    before_coverage_report = before_baseline.report
    write_coverage_reports(before_coverage_report, Path(args.before_coverage_json), Path(args.before_coverage_markdown))

    before_requested_tickers = collect_study_tickers(
        EventStudySupabaseWriter(repo_root).load_study_events()
    ) | {event.ticker for event in normalized_news_events}
    before_price_summary = _build_price_coverage_summary(repo_root, base_price_path, before_requested_tickers)
    before_study_summary = StudyComputationSummary(
        event_count=before_baseline.study_event_count,
        requested_ticker_count=len(before_requested_tickers),
        observation_count=before_baseline.observation_count,
        aggregate_count=len(before_baseline.coverage_studies),
        category_summary_count=sum(1 for study in before_baseline.coverage_studies if study.study_target_type == "category_summary"),
        missing_primary_series=before_baseline.observation_stats["missing_primary_series"],
        missing_related_series=before_baseline.observation_stats["missing_related_series"],
        missing_horizon=before_baseline.observation_stats["missing_horizon"],
        events_with_primary_observation=sum(1 for value in before_baseline.snapshot["focused_primary_slices"].values() if value["min_sample_size"] > 0),
        events_with_any_observation=min(before_baseline.observation_count, before_baseline.study_event_count),
        events_with_related_observation=sum(1 for value in before_baseline.snapshot["focused_related_slices"].values() if value["min_sample_size"] > 0),
        events_without_any_observation=max(before_baseline.study_event_count - min(before_baseline.observation_count, before_baseline.study_event_count), 0),
        out_of_range_event_ids_sample=(),
        resolved_price_dataset=before_baseline.price_dataset_path,
        resolution_reason=before_coverage_report.notes.get("price_resolution_reason", "explicit_override"),
    )
    before_signal_summary = SignalScoringSummary(
        recent_event_count=before_baseline.signal_event_count,
        study_statistic_count=len(before_baseline.coverage_studies),
        signal_count=len(before_baseline.coverage_signals),
        confidence_distribution=dict(sorted(Counter(signal.confidence_band for signal in before_baseline.coverage_signals).items())),
    )
    before_summary = _build_summary_dict(
        reference_time=reference_time,
        news_summary=news_summary,
        price_summary=before_price_summary,
        study_summary=before_study_summary,
        signal_summary=before_signal_summary,
        coverage_report=before_coverage_report.to_dict(),
    )
    _write_json(before_summary, Path(args.before_json))

    if args.dry_run:
        LOGGER.info(
            "Dry run complete. normalized=%s skipped=%s base_price_max=%s",
            news_summary.normalized_records,
            news_summary.skipped_records,
            before_price_summary.max_date,
        )
        return 0

    writer = SupabaseWriter(repo_root)
    write_summary = writer.upsert_events(normalized_news_events)
    LOGGER.info(
        "Financial-news ingestion complete. events=%s related_companies=%s research_insights=%s",
        write_summary.events_upserted,
        write_summary.related_companies_upserted,
        write_summary.research_insights_upserted,
    )

    backfill_report: MassiveBackfillReport | None = None
    if args.skip_backfill:
        resolved_after_dataset = resolve_price_dataset_path(repo_root, args.price_file, allow_sample_fallback=False)
        after_price_path = resolved_after_dataset.path
        LOGGER.info("Skipping Massive backfill and using existing local price dataset %s", describe_resolution(resolved_after_dataset))
    else:
        backfill_report = run_massive_price_backfill(repo_root, start_date=None, end_date=None, ticker_overrides=[], dry_run=False)
        _write_json_and_markdown(
            backfill_report.to_dict(),
            Path(args.backfill_json),
            Path(args.backfill_markdown),
            build_backfill_markdown(backfill_report),
        )
        after_price_path = Path(args.price_file) if args.price_file else Path(backfill_report.extended_parquet_path)
    after_study_summary = _build_study_summary(repo_root, after_price_path, write_results=True)
    after_signal_summary = _build_signal_summary(
        repo_root,
        lookback_days=args.lookback_days,
        limit_events=args.limit_events,
        write_results=True,
    )
    after_coverage_report = run_coverage_audit(repo_root, after_price_path)
    write_coverage_reports(after_coverage_report, Path(args.after_coverage_json), Path(args.after_coverage_markdown))
    write_coverage_reports(after_coverage_report, repo_root / "reports" / "coverage_audit.json", repo_root / "reports" / "coverage_audit.md")

    after_plan = build_targeted_backfill_plan(after_coverage_report.to_dict(), limit=12)
    write_targeted_backfill_plan(after_plan, Path(args.planner_json), Path(args.planner_markdown))
    write_targeted_backfill_plan(after_plan, repo_root / "reports" / "targeted_backfill_plan.json", repo_root / "reports" / "targeted_backfill_plan.md")

    after_snapshot = CoverageSnapshotRepository(repo_root).capture_snapshot(
        focused_related_slices=FOCUSED_RELATED_SLICES,
        focused_primary_slices=FOCUSED_PRIMARY_SLICES,
    )
    coverage_diff_summary = build_comparison_summary(
        before_coverage_report.to_dict(),
        after_coverage_report.to_dict(),
        before_baseline.snapshot,
        after_snapshot,
    )
    write_comparison_artifacts(coverage_diff_summary, Path(args.coverage_diff_markdown), Path(args.coverage_diff_json))

    after_requested_tickers = collect_study_tickers(EventStudySupabaseWriter(repo_root).load_study_events())
    after_price_summary = _build_price_coverage_summary(repo_root, after_price_path, after_requested_tickers)
    after_summary = _build_summary_dict(
        reference_time=reference_time,
        news_summary=news_summary,
        price_summary=after_price_summary,
        study_summary=after_study_summary,
        signal_summary=after_signal_summary,
        coverage_report=after_coverage_report.to_dict(),
        backfill_report=backfill_report,
        planner=after_plan.to_dict(),
    )
    _write_json(after_summary, Path(args.after_json))

    alignment_diff = _build_alignment_diff(before_summary, after_summary, coverage_diff_summary)
    _write_json_and_markdown(
        alignment_diff,
        Path(args.diff_json),
        Path(args.diff_markdown),
        _build_alignment_diff_markdown(alignment_diff),
    )
    LOGGER.info(
        "Financial-news alignment finished. events_before=%s events_after=%s observations_before=%s observations_after=%s signals_before=%s signals_after=%s",
        alignment_diff["total_events"]["before"],
        alignment_diff["total_events"]["after"],
        alignment_diff["study_recompute"]["observations_before"],
        alignment_diff["study_recompute"]["observations_after"],
        alignment_diff["signal_scoring"]["signals_before"],
        alignment_diff["signal_scoring"]["signals_after"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
