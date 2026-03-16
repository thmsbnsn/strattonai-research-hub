from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
from typing import Any

try:
    from ingestion.write_to_supabase import SupabaseWriter
except ImportError:  # pragma: no cover - script execution fallback
    from write_to_supabase import SupabaseWriter  # type: ignore

from .coverage_models import CoverageSignal, CoverageStudyStatistic


FOCUSED_RELATED_SLICES = (
    ("Capital Expenditure", "ORCL", "Sector Peer"),
    ("Capital Expenditure", "AMZN", "Competitor"),
    ("Legal/Regulatory", "GOOGL", "Sector Peer"),
    ("Legal/Regulatory", "META", "Sector Peer"),
    ("Partnership", "TSM", "Supplier"),
)

FOCUSED_PRIMARY_SLICES = (
    ("Macro Event", "MSFT"),
    ("Macro Event", "NVDA"),
)


def parse_focus_slices_from_gap_keys(
    gap_keys: list[str] | tuple[str, ...],
) -> tuple[tuple[tuple[str, str, str], ...], tuple[tuple[str, str], ...]]:
    related_slices: list[tuple[str, str, str]] = []
    primary_slices: list[tuple[str, str]] = []

    for gap_key in gap_keys:
        parts = gap_key.split("::")
        if len(parts) == 4 and parts[0] == "related":
            related_slice = (parts[1], parts[2], parts[3])
            if related_slice not in related_slices:
                related_slices.append(related_slice)
        elif len(parts) == 3 and parts[0] == "primary":
            primary_slice = (parts[1], parts[2])
            if primary_slice not in primary_slices:
                primary_slices.append(primary_slice)

    return tuple(related_slices), tuple(primary_slices)


def _build_related_slice_snapshot_from_horizon_totals(
    event_category: str,
    related_ticker: str,
    relationship_type: str,
    horizon_totals: dict[str, int],
) -> dict[str, Any]:
    return {
        "event_category": event_category,
        "related_ticker": related_ticker,
        "relationship_type": relationship_type,
        "horizon_count": len(horizon_totals),
        "min_sample_size": min(horizon_totals.values()) if horizon_totals else 0,
    }


def _build_primary_slice_snapshot_from_horizon_totals(
    event_category: str,
    primary_ticker: str,
    horizon_totals: dict[str, int],
) -> dict[str, Any]:
    return {
        "event_category": event_category,
        "primary_ticker": primary_ticker,
        "horizon_count": len(horizon_totals),
        "min_sample_size": min(horizon_totals.values()) if horizon_totals else 0,
    }


def build_snapshot_from_studies_and_signals(
    report: dict[str, Any],
    studies: list[CoverageStudyStatistic],
    signals: list[CoverageSignal],
    focused_related_slices: tuple[tuple[str, str, str], ...] = FOCUSED_RELATED_SLICES,
    focused_primary_slices: tuple[tuple[str, str], ...] = FOCUSED_PRIMARY_SLICES,
) -> dict[str, Any]:
    confidence_bands = {"High": 0, "Moderate": 0, "Low": 0}
    for signal in signals:
        if signal.confidence_band in confidence_bands:
            confidence_bands[signal.confidence_band] += 1

    focused_related_summary: dict[str, dict[str, Any]] = {}
    for event_category, related_ticker, relationship_type in focused_related_slices:
        horizon_totals: dict[str, int] = defaultdict(int)
        for study in studies:
            if (
                study.study_target_type == "related"
                and study.event_category == event_category
                and study.related_ticker == related_ticker
                and study.relationship_type == relationship_type
            ):
                horizon_totals[study.horizon] += study.sample_size

        focused_related_summary[f"{event_category}::{related_ticker}::{relationship_type}"] = _build_related_slice_snapshot_from_horizon_totals(
            event_category,
            related_ticker,
            relationship_type,
            horizon_totals,
        )

    focused_primary_summary: dict[str, dict[str, Any]] = {}
    for event_category, primary_ticker in focused_primary_slices:
        horizon_totals: dict[str, int] = defaultdict(int)
        for study in studies:
            if (
                study.study_target_type == "primary"
                and study.event_category == event_category
                and study.primary_ticker == primary_ticker
            ):
                horizon_totals[study.horizon] += study.sample_size

        focused_primary_summary[f"{event_category}::{primary_ticker}"] = _build_primary_slice_snapshot_from_horizon_totals(
            event_category,
            primary_ticker,
            horizon_totals,
        )

    return {
        "total_events": sum(int(value) for value in report.get("event_counts_by_category", {}).values()),
        "detailed_study_rows": len(studies),
        "ui_summary_rows": sum(1 for study in studies if study.study_target_type == "category_summary"),
        "signal_count": len(signals),
        "confidence_bands": confidence_bands,
        "focused_related_slices": focused_related_summary,
        "focused_primary_slices": focused_primary_summary,
    }


class CoverageSnapshotRepository(SupabaseWriter):
    def capture_snapshot(
        self,
        focused_related_slices: tuple[tuple[str, str, str], ...] = FOCUSED_RELATED_SLICES,
        focused_primary_slices: tuple[tuple[str, str], ...] = FOCUSED_PRIMARY_SLICES,
    ) -> dict[str, Any]:
        snapshot: dict[str, Any] = {
            "total_events": 0,
            "detailed_study_rows": 0,
            "ui_summary_rows": 0,
            "signal_count": 0,
            "confidence_bands": {"High": 0, "Moderate": 0, "Low": 0},
            "focused_related_slices": {},
            "focused_primary_slices": {},
        }

        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("select count(*) from public.events")
                snapshot["total_events"] = cursor.fetchone()[0]

                cursor.execute("select count(*) from public.event_study_statistics")
                snapshot["detailed_study_rows"] = cursor.fetchone()[0]

                cursor.execute("select count(*) from public.event_study_results")
                snapshot["ui_summary_rows"] = cursor.fetchone()[0]

                cursor.execute("select count(*) from public.signal_scores")
                snapshot["signal_count"] = cursor.fetchone()[0]

                cursor.execute("select confidence_band, count(*) from public.signal_scores group by confidence_band")
                for band, count in cursor.fetchall():
                    snapshot["confidence_bands"][band] = count

                for event_category, related_ticker, relationship_type in focused_related_slices:
                    cursor.execute(
                        """
                        select horizon, sum(sample_size) as total_sample_size
                        from public.event_study_statistics
                        where study_target_type = 'related'
                          and event_category = %s
                          and related_ticker = %s
                          and relationship_type = %s
                        group by horizon
                        order by horizon asc
                        """,
                        (event_category, related_ticker, relationship_type),
                    )
                    rows = cursor.fetchall()
                    snapshot["focused_related_slices"][f"{event_category}::{related_ticker}::{relationship_type}"] = _build_related_slice_snapshot_from_horizon_totals(
                        event_category,
                        related_ticker,
                        relationship_type,
                        {horizon: int(total_sample_size or 0) for horizon, total_sample_size in rows},
                    )

                for event_category, primary_ticker in focused_primary_slices:
                    cursor.execute(
                        """
                        select horizon, sum(sample_size) as total_sample_size
                        from public.event_study_statistics
                        where study_target_type = 'primary'
                          and event_category = %s
                          and primary_ticker = %s
                        group by horizon
                        order by horizon asc
                        """,
                        (event_category, primary_ticker),
                    )
                    rows = cursor.fetchall()
                    snapshot["focused_primary_slices"][f"{event_category}::{primary_ticker}"] = _build_primary_slice_snapshot_from_horizon_totals(
                        event_category,
                        primary_ticker,
                        {horizon: int(total_sample_size or 0) for horizon, total_sample_size in rows},
                    )

        return snapshot


def _sum_confidence_bands(report: dict[str, Any]) -> dict[str, int]:
    total = {"High": 0, "Moderate": 0, "Low": 0}
    for distribution in report.get("confidence_band_distribution_by_category", {}).values():
        total["High"] += int(distribution.get("high", 0))
        total["Moderate"] += int(distribution.get("moderate", 0))
        total["Low"] += int(distribution.get("low", 0))
    return total


def _sorted_category_deltas(before: dict[str, int], after: dict[str, int]) -> list[tuple[str, int, int, int]]:
    categories = sorted(set(before) | set(after))
    return [
        (category, before.get(category, 0), after.get(category, 0), after.get(category, 0) - before.get(category, 0))
        for category in categories
    ]


def build_comparison_summary(
    before_report: dict[str, Any],
    after_report: dict[str, Any],
    before_snapshot: dict[str, Any],
    after_snapshot: dict[str, Any],
) -> dict[str, Any]:
    before_event_total = sum(before_report.get("event_counts_by_category", {}).values())
    after_event_total = sum(after_report.get("event_counts_by_category", {}).values())

    return {
        "total_events": {
            "before": before_event_total,
            "after": after_event_total,
            "delta": after_event_total - before_event_total,
        },
        "event_counts_by_category": [
            {
                "event_category": category,
                "before": before_count,
                "after": after_count,
                "delta": delta,
            }
            for category, before_count, after_count, delta in _sorted_category_deltas(
                before_report.get("event_counts_by_category", {}),
                after_report.get("event_counts_by_category", {}),
            )
        ],
        "macro_event_depth": {
            "event_count_before": before_report.get("event_counts_by_category", {}).get("Macro Event", 0),
            "event_count_after": after_report.get("event_counts_by_category", {}).get("Macro Event", 0),
            "primary_slices": {
                key: {
                    "before": before_snapshot["focused_primary_slices"][key],
                    "after": after_snapshot["focused_primary_slices"][key],
                }
                for key in after_snapshot["focused_primary_slices"]
            },
        },
        "study_rows": {
            "detailed_before": before_snapshot["detailed_study_rows"],
            "detailed_after": after_snapshot["detailed_study_rows"],
            "detailed_delta": after_snapshot["detailed_study_rows"] - before_snapshot["detailed_study_rows"],
            "summary_before": before_snapshot["ui_summary_rows"],
            "summary_after": after_snapshot["ui_summary_rows"],
            "summary_delta": after_snapshot["ui_summary_rows"] - before_snapshot["ui_summary_rows"],
        },
        "signals": {
            "count_before": before_snapshot["signal_count"],
            "count_after": after_snapshot["signal_count"],
            "count_delta": after_snapshot["signal_count"] - before_snapshot["signal_count"],
            "confidence_bands_before": before_snapshot["confidence_bands"],
            "confidence_bands_after": after_snapshot["confidence_bands"],
            "audit_confidence_bands_before": _sum_confidence_bands(before_report),
            "audit_confidence_bands_after": _sum_confidence_bands(after_report),
        },
        "focused_related_slices": {
            key: {
                "before": before_snapshot["focused_related_slices"][key],
                "after": after_snapshot["focused_related_slices"][key],
                "delta_sample_size": after_snapshot["focused_related_slices"][key]["min_sample_size"]
                - before_snapshot["focused_related_slices"][key]["min_sample_size"],
            }
            for key in after_snapshot["focused_related_slices"]
        },
        "remaining_top_gap_candidates": after_report.get("top_gap_candidates", [])[:8],
    }


def build_comparison_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Coverage Audit Diff",
        "",
        "## Total Events",
        (
            f"- Events: {summary['total_events']['before']} -> {summary['total_events']['after']} "
            f"(delta {summary['total_events']['delta']:+d})"
        ),
        "",
        "## Event Counts By Category",
    ]

    for item in summary["event_counts_by_category"]:
        lines.append(
            f"- {item['event_category']}: {item['before']} -> {item['after']} (delta {item['delta']:+d})"
        )

    lines.extend(
        [
            "",
            "## Macro Event Depth",
            (
                f"- Macro Event count: {summary['macro_event_depth']['event_count_before']} -> "
                f"{summary['macro_event_depth']['event_count_after']}"
            ),
        ]
    )
    for key, values in summary["macro_event_depth"]["primary_slices"].items():
        lines.append(
            f"- {key}: min sample {values['before']['min_sample_size']} -> {values['after']['min_sample_size']}, "
            f"horizons {values['before']['horizon_count']} -> {values['after']['horizon_count']}"
        )

    lines.extend(
        [
            "",
            "## Focused Related Slice Improvements",
        ]
    )
    for key, values in summary["focused_related_slices"].items():
        lines.append(
            f"- {key}: min sample {values['before']['min_sample_size']} -> {values['after']['min_sample_size']} "
            f"(delta {values['delta_sample_size']:+d}), horizons {values['before']['horizon_count']} -> {values['after']['horizon_count']}"
        )

    lines.extend(
        [
            "",
            "## Event Study Rows",
            (
                f"- Detailed rows: {summary['study_rows']['detailed_before']} -> {summary['study_rows']['detailed_after']} "
                f"(delta {summary['study_rows']['detailed_delta']:+d})"
            ),
            (
                f"- UI summary rows: {summary['study_rows']['summary_before']} -> {summary['study_rows']['summary_after']} "
                f"(delta {summary['study_rows']['summary_delta']:+d})"
            ),
            "",
            "## Signals",
            (
                f"- Signal count: {summary['signals']['count_before']} -> {summary['signals']['count_after']} "
                f"(delta {summary['signals']['count_delta']:+d})"
            ),
            (
                f"- Confidence bands: High {summary['signals']['confidence_bands_before']['High']} -> {summary['signals']['confidence_bands_after']['High']}, "
                f"Moderate {summary['signals']['confidence_bands_before']['Moderate']} -> {summary['signals']['confidence_bands_after']['Moderate']}, "
                f"Low {summary['signals']['confidence_bands_before']['Low']} -> {summary['signals']['confidence_bands_after']['Low']}"
            ),
            "",
            "## Remaining Weak Slices",
        ]
    )

    for candidate in summary["remaining_top_gap_candidates"]:
        lines.append(
            f"- {candidate['candidate_key']}: needs {candidate['required_additional_examples']} more example(s). {candidate['rationale']}"
        )

    return "\n".join(lines) + "\n"


def write_comparison_artifacts(summary: dict[str, Any], markdown_output: Path, json_output: Path | None = None) -> None:
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(build_comparison_markdown(summary), encoding="utf-8")

    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
