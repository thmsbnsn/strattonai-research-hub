from __future__ import annotations

import argparse
import json
import logging
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ingestion.inspect_financial_news_dataset import build_markdown_report as build_inspection_markdown
from ingestion.inspect_financial_news_dataset import inspect_financial_news_dataset, resolve_canonical_file
from ingestion.map_financial_news_to_event import get_financial_news_company_mapping_decision
from ingestion.run_ingestion import load_records, normalize_records, normalize_records_with_diagnostics
from ingestion.write_to_supabase import SupabaseWriter

from .build_targeted_backfill_plan import build_targeted_backfill_plan, write_targeted_backfill_plan
from .coverage_audit import write_coverage_reports
from .coverage_audit_diff import build_comparison_summary, parse_focus_slices_from_gap_keys, write_comparison_artifacts
from .low_confidence_diagnostics import (
    build_low_confidence_diagnostics_report,
    build_low_confidence_diff,
    records_from_signal_scores,
    write_low_confidence_diff,
    write_low_confidence_reports,
)
from .massive_price_backfill import MassiveBackfillReport, build_markdown_report as build_backfill_markdown
from .massive_price_backfill import run_massive_price_backfill
from .price_dataset import describe_resolution, resolve_price_dataset_path
from .targeted_expansion_baseline import TargetedExpansionBaselineArtifacts, build_targeted_expansion_baseline
from .write_event_studies_to_supabase import EventStudySupabaseWriter
from .write_signals_to_supabase import SignalSupabaseWriter


LOGGER = logging.getLogger("research.run_precision_evidence_quality_pass")


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format="%(levelname)s %(message)s")


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Run the precision evidence-quality pass end-to-end.")
    parser.add_argument("--news-input-dir", default=str(repo_root.parent / "data" / "events" / "financialNews"))
    parser.add_argument("--market-input", default=str(repo_root / "ingestion" / "targeted_expansion_wave_quality_market_events.json"))
    parser.add_argument("--sec-input", default=str(repo_root / "ingestion" / "targeted_expansion_wave_quality_sec_filings.json"))
    parser.add_argument("--price-file", default=None)
    parser.add_argument("--mapping-report-json", default=str(repo_root / "reports" / "financial_news_mapping_expansion.json"))
    parser.add_argument("--mapping-report-markdown", default=str(repo_root / "reports" / "financial_news_mapping_expansion.md"))
    parser.add_argument("--before-summary-json", default=str(repo_root / "reports" / "evidence_quality_pass_before.json"))
    parser.add_argument("--after-summary-json", default=str(repo_root / "reports" / "evidence_quality_pass_after.json"))
    parser.add_argument("--diff-summary-json", default=str(repo_root / "reports" / "evidence_quality_pass_diff.json"))
    parser.add_argument("--diff-summary-markdown", default=str(repo_root / "reports" / "evidence_quality_pass_diff.md"))
    parser.add_argument("--before-coverage-json", default=str(repo_root / "reports" / "coverage_audit_before_evidence_quality.json"))
    parser.add_argument("--before-coverage-markdown", default=str(repo_root / "reports" / "coverage_audit_before_evidence_quality.md"))
    parser.add_argument("--after-coverage-json", default=str(repo_root / "reports" / "coverage_audit_after_evidence_quality.json"))
    parser.add_argument("--after-coverage-markdown", default=str(repo_root / "reports" / "coverage_audit_after_evidence_quality.md"))
    parser.add_argument("--coverage-diff-json", default=str(repo_root / "reports" / "coverage_audit_diff_evidence_quality.json"))
    parser.add_argument("--coverage-diff-markdown", default=str(repo_root / "reports" / "coverage_audit_diff_evidence_quality.md"))
    parser.add_argument("--before-low-confidence-json", default=str(repo_root / "reports" / "low_confidence_diagnostics_before_evidence_quality.json"))
    parser.add_argument("--before-low-confidence-markdown", default=str(repo_root / "reports" / "low_confidence_diagnostics_before_evidence_quality.md"))
    parser.add_argument("--after-low-confidence-json", default=str(repo_root / "reports" / "low_confidence_diagnostics_after_evidence_quality.json"))
    parser.add_argument("--after-low-confidence-markdown", default=str(repo_root / "reports" / "low_confidence_diagnostics_after_evidence_quality.md"))
    parser.add_argument("--low-confidence-diff-json", default=str(repo_root / "reports" / "low_confidence_diagnostics_diff_evidence_quality.json"))
    parser.add_argument("--low-confidence-diff-markdown", default=str(repo_root / "reports" / "low_confidence_diagnostics_diff_evidence_quality.md"))
    parser.add_argument("--planner-json", default=str(repo_root / "reports" / "targeted_backfill_plan_after_evidence_quality.json"))
    parser.add_argument("--planner-markdown", default=str(repo_root / "reports" / "targeted_backfill_plan_after_evidence_quality.md"))
    parser.add_argument("--massive-json", default=str(repo_root / "reports" / "massive_price_backfill_precision_quality.json"))
    parser.add_argument("--massive-markdown", default=str(repo_root / "reports" / "massive_price_backfill_precision_quality.md"))
    parser.add_argument("--plan-limit", type=int, default=12)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_json_and_markdown(path_json: Path, path_markdown: Path, payload: dict[str, Any], markdown: str) -> None:
    path_json.parent.mkdir(parents=True, exist_ok=True)
    path_markdown.parent.mkdir(parents=True, exist_ok=True)
    path_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    path_markdown.write_text(markdown, encoding="utf-8")


def _load_existing_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _build_financial_news_normalization_summary(news_input_dir: Path) -> tuple[dict[str, Any], list[Any]]:
    canonical_file, _alternate_files = resolve_canonical_file(news_input_dir)
    raw_records = load_records("financial-news", str(canonical_file))
    normalized_records, failures, skipped = normalize_records_with_diagnostics(
        "financial-news",
        raw_records,
        log_each_record=False,
    )
    summary = {
        "input_records": len(raw_records),
        "normalized_records": len(normalized_records),
        "skipped_records": len(skipped),
        "failed_records": len(failures),
        "category_counts": dict(sorted(Counter(event.category for event in normalized_records).items())),
        "ticker_counts": dict(sorted(Counter(event.ticker for event in normalized_records).items())),
        "skip_reason_counts": dict(sorted(Counter(item.reason for item in skipped).items())),
    }
    return summary, normalized_records


def _build_mapping_expansion_report(
    repo_root: Path,
    news_input_dir: Path,
    before_report: dict[str, Any],
    after_inspection: dict[str, Any],
    after_summary: dict[str, Any],
    before_source_count: int,
    after_source_count: int,
) -> tuple[dict[str, Any], str]:
    before_inspection = _load_existing_json(repo_root / "reports" / "financial_news_dataset_inspection.json")
    before_alignment = before_report or _load_existing_json(repo_root / "reports" / "financial_news_alignment_after.json")

    before_news = before_alignment.get("news_ingestion", {})
    before_mapped = before_inspection.get("mapped_company_tickers", {})
    before_unmapped = before_inspection.get("unmapped_companies", {})
    after_mapped = after_inspection.get("mapped_company_tickers", {})
    after_unmapped = after_inspection.get("unmapped_companies", {})

    newly_supported = sorted(set(after_mapped) - set(before_mapped))
    still_unsupported = sorted(set(after_unmapped))
    added_mapping_details = []
    for company_name in newly_supported:
        decision = get_financial_news_company_mapping_decision(company_name)
        if decision is None:
            continue
        added_mapping_details.append(
            {
                "company_name": company_name,
                "ticker": decision.ticker,
                "canonical_entity_name": decision.canonical_entity_name,
                "strategy": decision.strategy,
                "notes": decision.notes,
            }
        )

    unsupported_details = []
    for company_name in still_unsupported:
        decision = get_financial_news_company_mapping_decision(company_name)
        unmapped_entry = after_unmapped[company_name]
        if isinstance(unmapped_entry, dict):
            row_count = unmapped_entry.get("row_count", 0)
            fallback_reason = unmapped_entry.get("reason")
        else:
            row_count = unmapped_entry
            fallback_reason = "No deterministic company mapping has been configured for this name."
        unsupported_details.append(
            {
                "company_name": company_name,
                "row_count": row_count,
                "notes": decision.notes if decision is not None else fallback_reason,
            }
        )

    payload = {
        "input_dir": str(news_input_dir),
        "before": {
            "normalized_records": int(before_news.get("normalized_records", 0)),
            "skipped_records": int(before_news.get("skipped_records", 0)),
            "stored_financial_news_rows": before_source_count,
            "mapped_companies": before_mapped,
            "unmapped_companies": before_unmapped,
        },
        "after": {
            "normalized_records": after_summary["normalized_records"],
            "skipped_records": after_summary["skipped_records"],
            "stored_financial_news_rows": after_source_count,
            "mapped_companies": after_mapped,
            "unmapped_companies": after_unmapped,
            "skip_reason_counts": after_summary["skip_reason_counts"],
        },
        "delta": {
            "normalized_records": after_summary["normalized_records"] - int(before_news.get("normalized_records", 0)),
            "stored_financial_news_rows": after_source_count - before_source_count,
        },
        "added_mappings": added_mapping_details,
        "unsupported_companies": unsupported_details,
    }

    lines = [
        "# Financial News Mapping Expansion",
        "",
        f"- Normalized records: {payload['before']['normalized_records']} -> {payload['after']['normalized_records']} (delta {payload['delta']['normalized_records']:+d})",
        f"- Stored `financial_news_local` rows: {payload['before']['stored_financial_news_rows']} -> {payload['after']['stored_financial_news_rows']} (delta {payload['delta']['stored_financial_news_rows']:+d})",
        "",
        "## Added Mappings",
    ]
    if added_mapping_details:
        for item in added_mapping_details:
            lines.append(f"- {item['company_name']} -> {item['ticker']} ({item['strategy']}): {item['notes']}")
    else:
        lines.append("- None added in this pass.")

    lines.extend(["", "## Still Unsupported"])
    for item in unsupported_details:
        lines.append(f"- {item['company_name']}: {item['row_count']} rows. {item['notes']}")

    return payload, "\n".join(lines) + "\n"


def _normalize_wave_inputs(market_input: str, sec_input: str) -> tuple[list[Any], dict[str, Any]]:
    market_records = load_records("market-events", market_input)
    market_events, market_failures = normalize_records("market-events", market_records)
    sec_records = load_records("sec-filings", sec_input)
    sec_events, sec_failures = normalize_records("sec-filings", sec_records)

    failures = [*market_failures, *sec_failures]
    if failures:
        messages = [f"Record {failure.record_index}: {failure.reason}" for failure in failures]
        raise ValueError("Wave normalization failed:\n" + "\n".join(messages))

    events = [*market_events, *sec_events]
    return events, {
        "normalized_records": len(events),
        "category_counts": dict(sorted(Counter(event.category for event in events).items())),
        "source_names": dict(sorted(Counter(event.source_name for event in events).items())),
    }


def _derive_focus_slice_keys(wave_events: list[Any]) -> tuple[tuple[tuple[str, str, str], ...], tuple[tuple[str, str], ...], tuple[str, ...]]:
    gap_keys: list[str] = []
    for event in wave_events:
        metadata = event.metadata if isinstance(event.metadata, dict) else {}
        gap_keys.extend(str(key) for key in metadata.get("targeted_gap_keys", []))

    related_slices, primary_slices = parse_focus_slices_from_gap_keys(gap_keys)
    return related_slices, primary_slices, tuple(dict.fromkeys(gap_keys))


def _recompute_event_studies(repo_root: Path, price_file: str | Path) -> dict[str, Any]:
    writer = EventStudySupabaseWriter(repo_root)
    before_detail_count, before_summary_count = writer.current_counts()

    from .event_study_engine import aggregate_observations, build_price_map, compute_event_study_observations
    from .price_dataset import collect_study_tickers, load_resolved_price_series

    events = writer.load_study_events()
    price_series, _resolved = load_resolved_price_series(repo_root, price_file, tickers=collect_study_tickers(events))
    observations, stats = compute_event_study_observations(events, build_price_map(price_series))
    aggregates = aggregate_observations(observations)
    detail_count = writer.upsert_event_study_aggregates(aggregates)
    summary_count = writer.upsert_ui_summary_rows(aggregates)

    return {
        "observation_count": len(observations),
        "detail_before": before_detail_count,
        "detail_after": detail_count,
        "summary_before": before_summary_count,
        "summary_after": summary_count,
        "stats": stats,
    }


def _rescore_signals(repo_root: Path, now: datetime) -> dict[str, Any]:
    writer = SignalSupabaseWriter(repo_root)
    before_count, before_distribution = writer.current_distribution()

    from .signal_scoring import index_studies, score_event_signals

    events = writer.load_recent_signal_events(lookback_days=120, limit_events=500)
    studies = writer.load_signal_study_statistics()
    indexed_studies = index_studies(studies)
    signals = []
    for event in events:
        signals.extend(score_event_signals(event, indexed_studies, now=now))

    upserted = writer.upsert_signal_scores(signals)
    after_count, after_distribution = writer.current_distribution()
    return {
        "event_count": len(events),
        "computed_count": len(signals),
        "computed_distribution": dict(sorted(Counter(signal.confidence_band for signal in signals).items())),
        "before_count": before_count,
        "before_distribution": before_distribution,
        "after_count": after_count,
        "after_distribution": after_distribution,
        "upserted": upserted,
    }


def _count_events_by_source(report: Any, source_name: str) -> int:
    return int(report.to_dict().get("event_counts_by_source", {}).get(source_name, 0))


def _build_pass_summary(
    *,
    reference_time: datetime,
    phase: str,
    news_mapping_report: dict[str, Any],
    wave_summary: dict[str, Any],
    baseline: TargetedExpansionBaselineArtifacts,
    plan: dict[str, Any],
    low_confidence: dict[str, Any],
    price_dataset_path: str,
    backfill_report: MassiveBackfillReport | None = None,
) -> dict[str, Any]:
    payload = {
        "phase": phase,
        "reference_time": reference_time.isoformat(),
        "price_dataset_path": price_dataset_path,
        "mapping_expansion": news_mapping_report,
        "targeted_wave": wave_summary,
        "coverage_audit": baseline.report.to_dict(),
        "snapshot": baseline.snapshot,
        "study_observation_count": baseline.observation_count,
        "study_observation_stats": baseline.observation_stats,
        "signal_event_count": baseline.signal_event_count,
        "targeted_backfill_plan": {
            "plan_items": plan.get("plan_items", [])[:12],
            "groups": plan.get("groups", []),
        },
        "low_confidence_diagnostics": low_confidence,
    }
    if backfill_report is not None:
        payload["massive_backfill"] = backfill_report.to_dict()
    return payload


def _build_pass_diff(
    *,
    before_summary: dict[str, Any],
    after_summary: dict[str, Any],
    coverage_diff: dict[str, Any],
    low_confidence_diff: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    before_coverage = before_summary["coverage_audit"]
    after_coverage = after_summary["coverage_audit"]
    before_mapping = before_summary["mapping_expansion"]
    after_mapping = after_summary["mapping_expansion"]
    before_signals = before_summary["snapshot"]["confidence_bands"]
    after_signals = after_summary["snapshot"]["confidence_bands"]

    payload = {
        "total_events": {
            "before": before_summary["snapshot"]["total_events"],
            "after": after_summary["snapshot"]["total_events"],
            "delta": after_summary["snapshot"]["total_events"] - before_summary["snapshot"]["total_events"],
        },
        "events_unlocked_by_mapping_expansion": after_mapping["delta"]["stored_financial_news_rows"],
        "normalized_events_unlocked_by_mapping_expansion": after_mapping["delta"]["normalized_records"],
        "event_counts_by_category": coverage_diff["event_counts_by_category"],
        "partnership_count": {
            "before": before_coverage.get("event_counts_by_category", {}).get("Partnership", 0),
            "after": after_coverage.get("event_counts_by_category", {}).get("Partnership", 0),
            "delta": after_coverage.get("event_counts_by_category", {}).get("Partnership", 0)
            - before_coverage.get("event_counts_by_category", {}).get("Partnership", 0),
        },
        "study_recompute": {
            "observations_before": before_summary["study_observation_count"],
            "observations_after": after_summary["study_observation_count"],
            "observation_delta": after_summary["study_observation_count"] - before_summary["study_observation_count"],
            "detailed_rows_before": before_summary["snapshot"]["detailed_study_rows"],
            "detailed_rows_after": after_summary["snapshot"]["detailed_study_rows"],
            "detailed_row_delta": after_summary["snapshot"]["detailed_study_rows"] - before_summary["snapshot"]["detailed_study_rows"],
        },
        "signals": {
            "before": before_summary["snapshot"]["signal_count"],
            "after": after_summary["snapshot"]["signal_count"],
            "delta": after_summary["snapshot"]["signal_count"] - before_summary["snapshot"]["signal_count"],
            "confidence_before": before_signals,
            "confidence_after": after_signals,
        },
        "focused_slice_improvements": coverage_diff.get("focused_related_slices", {}),
        "macro_event_depth": coverage_diff.get("macro_event_depth", {}),
        "exact_slice_changes": low_confidence_diff.get("exact_slice_changes", [])[:12],
        "remaining_top_weak_slices": after_summary["low_confidence_diagnostics"].get("top_low_confidence_slices", [])[:10],
        "remaining_top_gap_candidates": after_summary["coverage_audit"].get("top_gap_candidates", [])[:10],
    }

    lines = [
        "# Precision Evidence Quality Pass Diff",
        "",
        "## Mapping Expansion",
        f"- Normalized financial-news rows unlocked: {payload['normalized_events_unlocked_by_mapping_expansion']}",
        f"- Stored `financial_news_local` rows unlocked: {payload['events_unlocked_by_mapping_expansion']}",
        "",
        "## Total Events",
        f"- Events: {payload['total_events']['before']} -> {payload['total_events']['after']} (delta {payload['total_events']['delta']:+d})",
        "",
        "## Category Counts",
    ]
    for item in payload["event_counts_by_category"]:
        lines.append(f"- {item['event_category']}: {item['before']} -> {item['after']} (delta {item['delta']:+d})")

    lines.extend(
        [
            "",
            "## Partnership Depth",
            f"- Partnership events: {payload['partnership_count']['before']} -> {payload['partnership_count']['after']} (delta {payload['partnership_count']['delta']:+d})",
            "",
            "## Event Studies",
            f"- Valid observations: {payload['study_recompute']['observations_before']} -> {payload['study_recompute']['observations_after']} (delta {payload['study_recompute']['observation_delta']:+d})",
            f"- Detailed study rows: {payload['study_recompute']['detailed_rows_before']} -> {payload['study_recompute']['detailed_rows_after']} (delta {payload['study_recompute']['detailed_row_delta']:+d})",
            "",
            "## Signals",
            f"- Signal count: {payload['signals']['before']} -> {payload['signals']['after']} (delta {payload['signals']['delta']:+d})",
            f"- Confidence bands before: {payload['signals']['confidence_before']}",
            f"- Confidence bands after: {payload['signals']['confidence_after']}",
            "",
            "## Exact Slice Improvements",
        ]
    )
    for key, item in payload["focused_slice_improvements"].items():
        lines.append(
            f"- {key}: min sample {item['before']['min_sample_size']} -> {item['after']['min_sample_size']} "
            f"(delta {item['delta_sample_size']:+d})"
        )

    lines.extend(["", "## Exact Slice Diagnostic Changes"])
    for item in payload["exact_slice_changes"][:10]:
        lines.append(
            f"- {item['slice_key']}: low {item['low_before']} -> {item['low_after']} (delta {item['low_delta']:+d}), "
            f"sample {item['sample_before']} -> {item['sample_after']}, "
            f"causes {item['dominant_causes_before']} -> {item['dominant_causes_after']}"
        )

    lines.extend(["", "## Remaining Top Weak Slices"])
    for item in payload["remaining_top_weak_slices"][:8]:
        lines.append(
            f"- {item['slice_key']}: low={item['low_count']}/{item['signal_count']}, causes={item['dominant_causes']}"
        )

    return payload, "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)

    repo_root = Path(__file__).resolve().parent.parent
    reference_now = datetime.now(UTC)
    news_input_dir = Path(args.news_input_dir)
    resolved_price_dataset = resolve_price_dataset_path(repo_root, args.price_file)
    LOGGER.info("Using price dataset %s", describe_resolution(resolved_price_dataset))

    wave_events, wave_summary = _normalize_wave_inputs(args.market_input, args.sec_input)
    focused_related_slices, focused_primary_slices, focus_slice_keys = _derive_focus_slice_keys(wave_events)

    before_baseline = build_targeted_expansion_baseline(
        repo_root=repo_root,
        price_file=resolved_price_dataset.path,
        excluded_identities=set(),
        now=reference_now,
        focused_related_slices=focused_related_slices,
        focused_primary_slices=focused_primary_slices,
    )
    before_plan = build_targeted_backfill_plan(before_baseline.report.to_dict(), limit=args.plan_limit)
    before_low_confidence = build_low_confidence_diagnostics_report(
        records_from_signal_scores(before_baseline.scored_signals),
        plan=before_plan.to_dict(),
        focus_slice_keys=focus_slice_keys,
    )

    before_mapping_baseline = _load_existing_json(repo_root / "reports" / "financial_news_alignment_after.json")
    before_financial_news_source_count = _count_events_by_source(before_baseline.report, "financial_news_local")
    before_mapping_report, _before_mapping_markdown = _build_mapping_expansion_report(
        repo_root,
        news_input_dir,
        before_mapping_baseline,
        _load_existing_json(repo_root / "reports" / "financial_news_dataset_inspection.json"),
        before_mapping_baseline.get("news_ingestion", {}),
        before_financial_news_source_count,
        before_financial_news_source_count,
    )

    inspection_report = inspect_financial_news_dataset(news_input_dir)
    _write_json_and_markdown(
        repo_root / "reports" / "financial_news_dataset_inspection.json",
        repo_root / "reports" / "financial_news_dataset_inspection.md",
        inspection_report,
        build_inspection_markdown(inspection_report),
    )

    before_summary_payload = _build_pass_summary(
        reference_time=reference_now,
        phase="before",
        news_mapping_report=before_mapping_report,
        wave_summary={"normalized_records": 0, "category_counts": {}, "source_names": {}},
        baseline=before_baseline,
        plan=before_plan.to_dict(),
        low_confidence=before_low_confidence,
        price_dataset_path=str(resolved_price_dataset.path),
    )
    _write_json(Path(args.before_summary_json), before_summary_payload)
    write_coverage_reports(before_baseline.report, Path(args.before_coverage_json), Path(args.before_coverage_markdown))
    write_low_confidence_reports(before_low_confidence, Path(args.before_low_confidence_json), Path(args.before_low_confidence_markdown))

    if args.dry_run:
        LOGGER.info("Dry run complete. No database writes performed.")
        return 0

    news_summary_after_mapping, normalized_financial_news_events = _build_financial_news_normalization_summary(news_input_dir)
    writer = SupabaseWriter(repo_root)
    news_write_summary = writer.upsert_events(normalized_financial_news_events)
    LOGGER.info(
        "Financial-news reingestion complete. normalized=%s skipped=%s events=%s related_companies=%s",
        news_summary_after_mapping["normalized_records"],
        news_summary_after_mapping["skipped_records"],
        news_write_summary.events_upserted,
        news_write_summary.related_companies_upserted,
    )

    backfill_report = run_massive_price_backfill(
        repo_root,
        start_date=None,
        end_date=None,
        ticker_overrides=["TTM"],
        dry_run=False,
    )
    _write_json_and_markdown(
        Path(args.massive_json),
        Path(args.massive_markdown),
        backfill_report.to_dict(),
        build_backfill_markdown(backfill_report),
    )

    wave_write_summary = writer.upsert_events(wave_events)
    LOGGER.info(
        "Precision quality wave upsert complete. events=%s related_companies=%s",
        wave_write_summary.events_upserted,
        wave_write_summary.related_companies_upserted,
    )

    effective_price_dataset = resolve_price_dataset_path(repo_root, args.price_file)
    study_write_summary = _recompute_event_studies(repo_root, effective_price_dataset.path)
    signal_write_summary = _rescore_signals(repo_root, now=reference_now)

    after_baseline = build_targeted_expansion_baseline(
        repo_root=repo_root,
        price_file=effective_price_dataset.path,
        excluded_identities=set(),
        now=reference_now,
        focused_related_slices=focused_related_slices,
        focused_primary_slices=focused_primary_slices,
    )
    after_plan = build_targeted_backfill_plan(after_baseline.report.to_dict(), limit=args.plan_limit)
    after_low_confidence = build_low_confidence_diagnostics_report(
        records_from_signal_scores(after_baseline.scored_signals),
        plan=after_plan.to_dict(),
        focus_slice_keys=focus_slice_keys,
    )

    after_financial_news_source_count = _count_events_by_source(after_baseline.report, "financial_news_local")
    mapping_report, mapping_markdown = _build_mapping_expansion_report(
        repo_root,
        news_input_dir,
        before_mapping_baseline,
        inspection_report,
        news_summary_after_mapping,
        before_financial_news_source_count,
        after_financial_news_source_count,
    )
    _write_json_and_markdown(Path(args.mapping_report_json), Path(args.mapping_report_markdown), mapping_report, mapping_markdown)

    after_summary_payload = _build_pass_summary(
        reference_time=reference_now,
        phase="after",
        news_mapping_report=mapping_report,
        wave_summary=wave_summary
        | {
            "write_summary": {
                "events_upserted": wave_write_summary.events_upserted,
                "related_companies_upserted": wave_write_summary.related_companies_upserted,
                "research_insights_upserted": wave_write_summary.research_insights_upserted,
            }
        },
        baseline=after_baseline,
        plan=after_plan.to_dict(),
        low_confidence=after_low_confidence,
        price_dataset_path=str(effective_price_dataset.path),
        backfill_report=backfill_report,
    )
    after_summary_payload["study_write_summary"] = study_write_summary
    after_summary_payload["signal_write_summary"] = signal_write_summary
    _write_json(Path(args.after_summary_json), after_summary_payload)

    write_coverage_reports(after_baseline.report, Path(args.after_coverage_json), Path(args.after_coverage_markdown))
    write_coverage_reports(after_baseline.report, repo_root / "reports" / "coverage_audit.json", repo_root / "reports" / "coverage_audit.md")
    write_targeted_backfill_plan(after_plan, Path(args.planner_json), Path(args.planner_markdown))
    write_targeted_backfill_plan(after_plan, repo_root / "reports" / "targeted_backfill_plan.json", repo_root / "reports" / "targeted_backfill_plan.md")
    write_low_confidence_reports(after_low_confidence, Path(args.after_low_confidence_json), Path(args.after_low_confidence_markdown))
    write_low_confidence_reports(after_low_confidence, repo_root / "reports" / "low_confidence_diagnostics.json", repo_root / "reports" / "low_confidence_diagnostics.md")

    coverage_diff = build_comparison_summary(
        before_baseline.report.to_dict(),
        after_baseline.report.to_dict(),
        before_baseline.snapshot,
        after_baseline.snapshot,
    )
    write_comparison_artifacts(coverage_diff, Path(args.coverage_diff_markdown), Path(args.coverage_diff_json))

    low_confidence_diff = build_low_confidence_diff(before_low_confidence, after_low_confidence)
    write_low_confidence_diff(
        low_confidence_diff,
        Path(args.low_confidence_diff_json),
        Path(args.low_confidence_diff_markdown),
    )

    summary_diff, summary_markdown = _build_pass_diff(
        before_summary=before_summary_payload,
        after_summary=after_summary_payload,
        coverage_diff=coverage_diff,
        low_confidence_diff=low_confidence_diff,
    )
    _write_json_and_markdown(Path(args.diff_summary_json), Path(args.diff_summary_markdown), summary_diff, summary_markdown)

    LOGGER.info(
        "Precision evidence-quality pass complete. Events %s -> %s. Signals %s -> %s.",
        before_baseline.snapshot["total_events"],
        after_baseline.snapshot["total_events"],
        before_baseline.snapshot["signal_count"],
        after_baseline.snapshot["signal_count"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
