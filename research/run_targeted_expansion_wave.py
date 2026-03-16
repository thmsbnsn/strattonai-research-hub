from __future__ import annotations

import argparse
import logging
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

try:
    from ingestion.backfill_historical_events import configure_logging as configure_backfill_logging
    from ingestion.run_ingestion import load_records, normalize_records
    from ingestion.write_to_supabase import SupabaseWriter
except ImportError:  # pragma: no cover - script execution fallback
    from backfill_historical_events import configure_logging as configure_backfill_logging  # type: ignore
    from run_ingestion import load_records, normalize_records  # type: ignore
    from write_to_supabase import SupabaseWriter  # type: ignore

from .build_targeted_backfill_plan import build_targeted_backfill_plan, write_targeted_backfill_plan
from .coverage_audit import run_coverage_audit, write_coverage_reports
from .coverage_audit_diff import (
    FOCUSED_PRIMARY_SLICES,
    FOCUSED_RELATED_SLICES,
    CoverageSnapshotRepository,
    build_comparison_summary,
    parse_focus_slices_from_gap_keys,
    write_comparison_artifacts,
)
from .event_study_engine import aggregate_observations, build_price_map, compute_event_study_observations
from .low_confidence_diagnostics import (
    LowConfidenceDiagnosticsRepository,
    build_low_confidence_diagnostics_report,
    build_low_confidence_diff,
    records_from_signal_scores,
    write_low_confidence_diff,
    write_low_confidence_reports,
)
from .price_dataset import collect_study_tickers, describe_resolution, load_resolved_price_series, resolve_price_dataset_path
from .signal_scoring import index_studies, score_event_signals
from .targeted_expansion_baseline import build_targeted_expansion_baseline
from .write_event_studies_to_supabase import EventStudySupabaseWriter
from .write_signals_to_supabase import SignalSupabaseWriter


LOGGER = logging.getLogger("research.run_targeted_expansion_wave")


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Execute the next targeted historical expansion wave end-to-end.")
    parser.add_argument(
        "--market-input",
        default=str(repo_root / "ingestion" / "targeted_expansion_wave_market_events.json"),
        help="Structured market-event batch for this targeted expansion wave.",
    )
    parser.add_argument(
        "--sec-input",
        default=str(repo_root / "ingestion" / "targeted_expansion_wave_sec_filings.json"),
        help="Structured SEC-filing batch for this targeted expansion wave.",
    )
    parser.add_argument(
        "--price-file",
        default=None,
        help="Optional explicit price dataset path (.parquet, .csv, or .json). Defaults resolve to Parquet first.",
    )
    parser.add_argument(
        "--before-json",
        default=str(repo_root / "reports" / "coverage_audit_before.json"),
        help="Before-snapshot coverage audit JSON path.",
    )
    parser.add_argument(
        "--before-markdown",
        default=str(repo_root / "reports" / "coverage_audit_before.md"),
        help="Before-snapshot coverage audit Markdown path.",
    )
    parser.add_argument(
        "--after-json",
        default=str(repo_root / "reports" / "coverage_audit_after.json"),
        help="After-snapshot coverage audit JSON path.",
    )
    parser.add_argument(
        "--after-markdown",
        default=str(repo_root / "reports" / "coverage_audit_after.md"),
        help="After-snapshot coverage audit Markdown path.",
    )
    parser.add_argument(
        "--diff-markdown",
        default=str(repo_root / "reports" / "coverage_audit_diff.md"),
        help="Markdown comparison path.",
    )
    parser.add_argument(
        "--diff-json",
        default=str(repo_root / "reports" / "coverage_audit_diff.json"),
        help="JSON comparison path.",
    )
    parser.add_argument(
        "--after-plan-json",
        default=str(repo_root / "reports" / "targeted_backfill_plan_after.json"),
        help="Targeted backfill plan JSON path after recomputation.",
    )
    parser.add_argument(
        "--after-plan-markdown",
        default=str(repo_root / "reports" / "targeted_backfill_plan_after.md"),
        help="Targeted backfill plan Markdown path after recomputation.",
    )
    parser.add_argument(
        "--before-low-confidence-json",
        default=None,
        help="Optional before-snapshot low-confidence diagnostics JSON path.",
    )
    parser.add_argument(
        "--before-low-confidence-markdown",
        default=None,
        help="Optional before-snapshot low-confidence diagnostics Markdown path.",
    )
    parser.add_argument(
        "--after-low-confidence-json",
        default=None,
        help="Optional after-snapshot low-confidence diagnostics JSON path.",
    )
    parser.add_argument(
        "--after-low-confidence-markdown",
        default=None,
        help="Optional after-snapshot low-confidence diagnostics Markdown path.",
    )
    parser.add_argument(
        "--low-confidence-diff-json",
        default=None,
        help="Optional low-confidence diagnostics diff JSON path.",
    )
    parser.add_argument(
        "--low-confidence-diff-markdown",
        default=None,
        help="Optional low-confidence diagnostics diff Markdown path.",
    )
    parser.add_argument("--plan-limit", type=int, default=12, help="Number of plan items to keep.")
    parser.add_argument("--dry-run", action="store_true", help="Validate normalization and snapshot reporting without writing.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")
    return parser.parse_args()


def _count_event_categories(events: list) -> dict[str, int]:
    return dict(sorted(Counter(event.category for event in events).items()))


def _normalize_wave_inputs(market_input: str, sec_input: str):
    market_records = load_records("market-events", market_input)
    market_events, market_failures = normalize_records("market-events", market_records)

    sec_records = load_records("sec-filings", sec_input)
    sec_events, sec_failures = normalize_records("sec-filings", sec_records)

    failures = [*market_failures, *sec_failures]
    all_events = [*market_events, *sec_events]
    LOGGER.info(
        "Prepared %s targeted wave events. Category coverage=%s",
        len(all_events),
        _count_event_categories(all_events),
    )
    return all_events, failures


def _derive_focus_configuration(wave_events: list) -> tuple[tuple[tuple[str, str, str], ...], tuple[tuple[str, str], ...], tuple[str, ...]]:
    gap_keys: list[str] = []
    for event in wave_events:
        metadata = event.metadata if isinstance(event.metadata, dict) else {}
        gap_keys.extend(str(key) for key in metadata.get("targeted_gap_keys", []))

    parsed_related, parsed_primary = parse_focus_slices_from_gap_keys(gap_keys)
    focused_related = tuple(dict.fromkeys([*FOCUSED_RELATED_SLICES, *parsed_related]))
    focused_primary = tuple(dict.fromkeys([*FOCUSED_PRIMARY_SLICES, *parsed_primary]))
    focus_slice_keys = tuple(
        dict.fromkeys(
            [
                gap_key
                for gap_key in gap_keys
                if gap_key.startswith("related::") or gap_key.startswith("primary::")
            ]
        )
    )
    return focused_related, focused_primary, focus_slice_keys


def _recompute_event_studies(repo_root: Path, price_file: str | Path | None) -> tuple[int, int]:
    writer = EventStudySupabaseWriter(repo_root)
    events = writer.load_study_events()
    price_series, resolved_price_dataset = load_resolved_price_series(
        repo_root,
        price_file,
        tickers=collect_study_tickers(events),
    )
    LOGGER.info("Using price dataset %s", describe_resolution(resolved_price_dataset))
    price_map = build_price_map(price_series)
    observations, stats = compute_event_study_observations(events, price_map)
    aggregates = aggregate_observations(observations)
    detail_count = writer.upsert_event_study_aggregates(aggregates)
    summary_count = writer.upsert_ui_summary_rows(aggregates)
    LOGGER.info(
        "Recomputed event studies. observations=%s aggregates=%s missing_primary=%s missing_related=%s missing_horizon=%s",
        len(observations),
        len(aggregates),
        stats["missing_primary_series"],
        stats["missing_related_series"],
        stats["missing_horizon"],
    )
    return detail_count, summary_count


def _rescore_signals(repo_root: Path, now: datetime) -> int:
    writer = SignalSupabaseWriter(repo_root)
    events = writer.load_recent_signal_events(lookback_days=180, limit_events=1000)
    studies = writer.load_signal_study_statistics()
    indexed_studies = index_studies(studies)
    signals = []
    for event in events:
        signals.extend(score_event_signals(event, indexed_studies, now=now))

    LOGGER.info(
        "Rescored %s signals from %s recent events. Confidence distribution=%s",
        len(signals),
        len(events),
        dict(sorted(Counter(signal.confidence_band for signal in signals).items())),
    )
    return writer.upsert_signal_scores(signals)


def main() -> int:
    args = parse_args()
    configure_backfill_logging(args.verbose)

    repo_root = Path(__file__).resolve().parent.parent
    snapshot_repository = CoverageSnapshotRepository(repo_root)
    reference_now = datetime.now(UTC)
    resolved_price_dataset = resolve_price_dataset_path(repo_root, args.price_file)
    LOGGER.info("Resolved default price dataset to %s", describe_resolution(resolved_price_dataset))

    wave_events, failures = _normalize_wave_inputs(args.market_input, args.sec_input)
    if failures:
        for failure in failures:
            LOGGER.error("Normalization failure for record %s: %s", failure.record_index, failure.reason)
        return 1

    excluded_identities = {(event.source_name, event.source_record_id) for event in wave_events}
    focused_related_slices, focused_primary_slices, focus_slice_keys = _derive_focus_configuration(wave_events)
    before_artifacts = build_targeted_expansion_baseline(
        repo_root=repo_root,
        price_file=resolved_price_dataset.path,
        excluded_identities=excluded_identities,
        now=reference_now,
        focused_related_slices=focused_related_slices,
        focused_primary_slices=focused_primary_slices,
    )
    before_report = before_artifacts.report
    before_snapshot = before_artifacts.snapshot
    write_coverage_reports(before_report, Path(args.before_json), Path(args.before_markdown))

    if args.before_low_confidence_json and args.before_low_confidence_markdown:
        before_low_confidence = build_low_confidence_diagnostics_report(
            records_from_signal_scores(before_artifacts.scored_signals),
            plan={},
            focus_slice_keys=focus_slice_keys,
        )
        write_low_confidence_reports(
            before_low_confidence,
            Path(args.before_low_confidence_json),
            Path(args.before_low_confidence_markdown),
        )

    if args.dry_run:
        LOGGER.info("Dry run complete. No writes performed.")
        return 0

    writer = SupabaseWriter(repo_root)
    write_summary = writer.upsert_events(wave_events)
    LOGGER.info(
        "Targeted wave upsert complete. events=%s related_companies=%s research_insights=%s",
        write_summary.events_upserted,
        write_summary.related_companies_upserted,
        write_summary.research_insights_upserted,
    )

    _recompute_event_studies(repo_root, resolved_price_dataset.path)
    _rescore_signals(repo_root, now=reference_now)

    after_report = run_coverage_audit(repo_root, resolved_price_dataset.path)
    write_coverage_reports(after_report, Path(args.after_json), Path(args.after_markdown))
    write_coverage_reports(
        after_report,
        repo_root / "reports" / "coverage_audit.json",
        repo_root / "reports" / "coverage_audit.md",
    )

    after_plan = build_targeted_backfill_plan(after_report.to_dict(), limit=args.plan_limit)
    write_targeted_backfill_plan(
        after_plan,
        Path(args.after_plan_json),
        Path(args.after_plan_markdown),
    )
    write_targeted_backfill_plan(
        after_plan,
        repo_root / "reports" / "targeted_backfill_plan.json",
        repo_root / "reports" / "targeted_backfill_plan.md",
    )

    if args.after_low_confidence_json and args.after_low_confidence_markdown:
        diagnostics_repository = LowConfidenceDiagnosticsRepository(repo_root)
        after_low_confidence = build_low_confidence_diagnostics_report(
            diagnostics_repository.load_signal_records(),
            plan=after_plan.to_dict(),
            focus_slice_keys=focus_slice_keys,
        )
        write_low_confidence_reports(
            after_low_confidence,
            Path(args.after_low_confidence_json),
            Path(args.after_low_confidence_markdown),
        )
        if (
            args.before_low_confidence_json
            and args.after_low_confidence_json
            and args.low_confidence_diff_json
            and args.low_confidence_diff_markdown
        ):
            before_low_confidence = build_low_confidence_diagnostics_report(
                records_from_signal_scores(before_artifacts.scored_signals),
                plan={},
                focus_slice_keys=focus_slice_keys,
            )
            low_confidence_diff = build_low_confidence_diff(before_low_confidence, after_low_confidence)
            write_low_confidence_diff(
                low_confidence_diff,
                Path(args.low_confidence_diff_json),
                Path(args.low_confidence_diff_markdown),
            )

    after_snapshot = snapshot_repository.capture_snapshot(
        focused_related_slices=focused_related_slices,
        focused_primary_slices=focused_primary_slices,
    )
    comparison_summary = build_comparison_summary(
        before_report.to_dict(),
        after_report.to_dict(),
        before_snapshot,
        after_snapshot,
    )
    write_comparison_artifacts(
        comparison_summary,
        Path(args.diff_markdown),
        Path(args.diff_json),
    )

    LOGGER.info(
        "Targeted expansion wave finished. Events %s -> %s. Detailed studies %s -> %s. Signals %s -> %s.",
        before_snapshot["total_events"],
        after_snapshot["total_events"],
        before_snapshot["detailed_study_rows"],
        after_snapshot["detailed_study_rows"],
        before_snapshot["signal_count"],
        after_snapshot["signal_count"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
