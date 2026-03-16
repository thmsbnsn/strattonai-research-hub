from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from decimal import Decimal
import json
from pathlib import Path
from statistics import mean
from typing import Any

try:
    from ingestion.write_to_supabase import SupabaseWriter
except ImportError:  # pragma: no cover - script execution fallback
    from write_to_supabase import SupabaseWriter  # type: ignore


LOW_CONFIDENCE = "Low"
MODERATE_CONFIDENCE_SAMPLE_SIZE = 5


@dataclass(frozen=True, slots=True)
class LowConfidenceSignalRecord:
    event_category: str
    primary_ticker: str
    target_ticker: str
    target_type: str
    relationship_type: str | None
    horizon: str
    confidence_band: str
    sample_size: int
    avg_return: float
    median_return: float
    win_rate: float
    score: float
    source_study_target_type: str | None
    consistency_rate: float
    recency_multiplier: float

    @property
    def is_fallback(self) -> bool:
        return self.source_study_target_type in {"category_summary", "relationship"}

    @property
    def slice_key(self) -> str:
        if self.target_type == "primary":
            return f"primary::{self.event_category}::{self.primary_ticker}"
        return f"related::{self.event_category}::{self.target_ticker}::{self.relationship_type or 'Related'}"


class LowConfidenceDiagnosticsRepository(SupabaseWriter):
    def load_signal_records(self) -> list[LowConfidenceSignalRecord]:
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
                      sample_size,
                      avg_return,
                      median_return,
                      win_rate,
                      score,
                      rationale
                    from public.signal_scores
                    order by event_category asc, target_type asc, target_ticker asc, horizon asc
                    """
                )
                rows = cursor.fetchall()

        return [self._row_to_record(row) for row in rows]

    @staticmethod
    def _row_to_record(row: tuple[Any, ...]) -> LowConfidenceSignalRecord:
        (
            event_category,
            primary_ticker,
            target_ticker,
            target_type,
            relationship_type,
            horizon,
            confidence_band,
            sample_size,
            avg_return,
            median_return,
            win_rate,
            score,
            rationale,
        ) = row
        return build_signal_record(
            event_category=event_category,
            primary_ticker=primary_ticker,
            target_ticker=target_ticker,
            target_type=target_type,
            relationship_type=relationship_type,
            horizon=horizon,
            confidence_band=confidence_band,
            sample_size=sample_size,
            avg_return=avg_return,
            median_return=median_return,
            win_rate=win_rate,
            score=score,
            rationale=rationale or {},
        )


def _to_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, Decimal):
        return float(value)
    return float(str(value))


def build_signal_record(
    *,
    event_category: str,
    primary_ticker: str,
    target_ticker: str,
    target_type: str,
    relationship_type: str | None,
    horizon: str,
    confidence_band: str,
    sample_size: int,
    avg_return: Any,
    median_return: Any,
    win_rate: Any,
    score: Any,
    rationale: dict[str, Any],
) -> LowConfidenceSignalRecord:
    study = rationale.get("study", {}) if isinstance(rationale, dict) else {}
    scoring = rationale.get("scoring", {}) if isinstance(rationale, dict) else {}
    components = scoring.get("components", {}) if isinstance(scoring, dict) else {}
    return LowConfidenceSignalRecord(
        event_category=event_category,
        primary_ticker=primary_ticker,
        target_ticker=target_ticker,
        target_type=target_type,
        relationship_type=relationship_type,
        horizon=horizon,
        confidence_band=confidence_band,
        sample_size=int(sample_size or 0),
        avg_return=_to_float(avg_return),
        median_return=_to_float(median_return),
        win_rate=_to_float(win_rate),
        score=_to_float(score),
        source_study_target_type=str(study.get("study_target_type")) if study.get("study_target_type") else None,
        consistency_rate=_to_float(components.get("consistency_rate"), default=_to_float(win_rate)),
        recency_multiplier=_to_float(components.get("recency_multiplier"), default=1.0),
    )


def records_from_signal_scores(signals: list[Any] | tuple[Any, ...]) -> list[LowConfidenceSignalRecord]:
    return [
        build_signal_record(
            event_category=signal.event_category,
            primary_ticker=signal.primary_ticker,
            target_ticker=signal.target_ticker,
            target_type=signal.target_type,
            relationship_type=signal.relationship_type,
            horizon=signal.horizon,
            confidence_band=signal.confidence_band,
            sample_size=signal.sample_size,
            avg_return=signal.avg_return,
            median_return=signal.median_return,
            win_rate=signal.win_rate,
            score=signal.score,
            rationale=signal.rationale if isinstance(signal.rationale, dict) else {},
        )
        for signal in signals
    ]


def _dominant_causes(records: list[LowConfidenceSignalRecord]) -> list[str]:
    causes: list[str] = []
    if not records:
        return ["no_low_signals"]

    fallback_ratio = mean(1.0 if record.is_fallback else 0.0 for record in records)
    average_sample_size = mean(record.sample_size for record in records)
    average_abs_avg_return = mean(abs(record.avg_return) for record in records)
    average_abs_median_return = mean(abs(record.median_return) for record in records)
    average_consistency_rate = mean(record.consistency_rate for record in records)
    average_recency_multiplier = mean(record.recency_multiplier for record in records)

    if fallback_ratio >= 0.5:
        causes.append("sparse_exact_coverage")
    if average_sample_size < MODERATE_CONFIDENCE_SAMPLE_SIZE:
        causes.append("small_sample_size")
    elif average_sample_size < 8:
        causes.append("thin_sample_depth")
    if average_abs_avg_return < 1.0 and average_abs_median_return < 0.75:
        causes.append("weak_edge")
    else:
        if average_abs_avg_return < 1.0:
            causes.append("weak_avg_return")
        if average_abs_median_return < 0.75:
            causes.append("weak_median_return")
    if average_consistency_rate < 55.0:
        causes.append("weak_win_rate")
    if average_recency_multiplier < 0.93:
        causes.append("older_recency_mix")

    return causes or ["mixed"]


def _build_slice_summary(
    slice_key: str,
    records: list[LowConfidenceSignalRecord],
    plan_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    confidence_counter = Counter(record.confidence_band for record in records)
    low_records = [record for record in records if record.confidence_band == LOW_CONFIDENCE]
    fallback_ratio = mean(1.0 if record.is_fallback else 0.0 for record in low_records) if low_records else 0.0
    average_sample_size = mean(record.sample_size for record in low_records) if low_records else 0.0
    minimum_sample_size = min((record.sample_size for record in low_records), default=0)
    average_abs_avg_return = mean(abs(record.avg_return) for record in low_records) if low_records else 0.0
    average_abs_median_return = mean(abs(record.median_return) for record in low_records) if low_records else 0.0
    average_win_rate = mean(record.win_rate for record in low_records) if low_records else 0.0
    average_consistency_rate = mean(record.consistency_rate for record in low_records) if low_records else 0.0
    average_recency_multiplier = mean(record.recency_multiplier for record in low_records) if low_records else 0.0
    dominant_causes = _dominant_causes(low_records)
    exemplar = records[0]
    linked_plan_item = plan_map.get(slice_key)
    linked_gap_size = int(linked_plan_item.get("gap_size", 0)) if linked_plan_item else None
    if exemplar.target_type == "related" and fallback_ratio >= 0.5 and "relationship_sparsity" not in dominant_causes:
        insert_at = 1 if "sparse_exact_coverage" in dominant_causes else 0
        dominant_causes.insert(insert_at, "relationship_sparsity")
    can_improve_with_depth = (
        bool(low_records)
        and (
            (linked_gap_size is not None and linked_gap_size <= 1)
            or max(MODERATE_CONFIDENCE_SAMPLE_SIZE - minimum_sample_size, 0) <= 1
        )
        and average_consistency_rate >= 55.0
        and average_abs_avg_return >= 1.0
    )

    if can_improve_with_depth and fallback_ratio >= 0.5:
        improvement_note = "One more exact example would likely reduce fallback reliance on this slice."
    elif can_improve_with_depth:
        improvement_note = "One more well-matched example would likely clear the moderate-confidence sample threshold."
    elif "weak_edge" in dominant_causes or "weak_avg_return" in dominant_causes or "weak_median_return" in dominant_causes:
        improvement_note = "Depth alone is unlikely to help without stronger historical edge quality."
    elif "weak_win_rate" in dominant_causes:
        improvement_note = "Depth alone is unlikely to help until win-rate consistency improves."
    else:
        improvement_note = "This slice remains low-confidence for mixed reasons."

    return {
        "slice_key": slice_key,
        "event_category": exemplar.event_category,
        "target_type": exemplar.target_type,
        "primary_ticker": exemplar.primary_ticker if exemplar.target_type == "primary" else None,
        "target_ticker": exemplar.target_ticker if exemplar.target_type == "related" else exemplar.primary_ticker,
        "relationship_type": exemplar.relationship_type,
        "signal_count": len(records),
        "low_count": confidence_counter.get("Low", 0),
        "moderate_count": confidence_counter.get("Moderate", 0),
        "high_count": confidence_counter.get("High", 0),
        "low_ratio": round(confidence_counter.get("Low", 0) / len(records), 4),
        "average_sample_size": round(average_sample_size, 2),
        "minimum_sample_size": minimum_sample_size,
        "average_abs_avg_return": round(average_abs_avg_return, 4),
        "average_abs_median_return": round(average_abs_median_return, 4),
        "average_win_rate": round(average_win_rate, 2),
        "average_consistency_rate": round(average_consistency_rate, 2),
        "fallback_ratio": round(fallback_ratio, 4),
        "average_recency_multiplier": round(average_recency_multiplier, 4),
        "dominant_causes": dominant_causes,
        "linked_gap_size": linked_gap_size,
        "can_improve_with_depth": can_improve_with_depth,
        "improvement_note": improvement_note,
    }


def build_low_confidence_diagnostics_report(
    signal_records: list[LowConfidenceSignalRecord],
    plan: dict[str, Any] | None = None,
    focus_slice_keys: tuple[str, ...] = (),
) -> dict[str, Any]:
    plan_map = {
        str(item.get("source_gap_key")): item
        for item in (plan or {}).get("plan_items", [])
        if item.get("source_gap_key")
    }

    grouped_by_slice: dict[str, list[LowConfidenceSignalRecord]] = defaultdict(list)
    grouped_by_category: dict[str, list[LowConfidenceSignalRecord]] = defaultdict(list)
    for record in signal_records:
        grouped_by_slice[record.slice_key].append(record)
        grouped_by_category[record.event_category].append(record)

    slice_summaries = [
        _build_slice_summary(slice_key, records, plan_map)
        for slice_key, records in grouped_by_slice.items()
    ]
    slice_summaries.sort(
        key=lambda item: (
            -item["low_count"],
            -item["low_ratio"],
            item["slice_key"],
        )
    )

    category_summaries: list[dict[str, Any]] = []
    for event_category, records in sorted(grouped_by_category.items()):
        distribution = Counter(record.confidence_band for record in records)
        category_slice_summaries = [item for item in slice_summaries if item["event_category"] == event_category]
        low_slice_causes = Counter(
            cause
            for item in category_slice_summaries
            for cause in item["dominant_causes"]
            for _ in range(item["low_count"])
        )
        category_summaries.append(
            {
                "event_category": event_category,
                "signal_count": len(records),
                "low_count": distribution.get("Low", 0),
                "moderate_count": distribution.get("Moderate", 0),
                "high_count": distribution.get("High", 0),
                "low_ratio": round(distribution.get("Low", 0) / len(records), 4),
                "dominant_causes": [cause for cause, _count in low_slice_causes.most_common(3)],
                "top_low_slices": [item["slice_key"] for item in category_slice_summaries[:5]],
            }
        )

    efficient_upgrade_candidates = [
        item
        for item in slice_summaries
        if item["low_count"] > 0 and item["can_improve_with_depth"]
    ]
    efficient_upgrade_candidates.sort(
        key=lambda item: (
            item["linked_gap_size"] if item["linked_gap_size"] is not None else 99,
            -item["low_count"],
            -item["fallback_ratio"],
            item["slice_key"],
        )
    )

    focus_slices = {
        slice_key: next((item for item in slice_summaries if item["slice_key"] == slice_key), None)
        for slice_key in focus_slice_keys
    }

    return {
        "category_summaries": category_summaries,
        "top_low_confidence_slices": slice_summaries[:20],
        "efficient_upgrade_candidates": efficient_upgrade_candidates[:12],
        "focus_slices": focus_slices,
        "notes": {
            "moderate_confidence_sample_threshold": MODERATE_CONFIDENCE_SAMPLE_SIZE,
            "signal_count": len(signal_records),
            "focus_slice_keys": list(focus_slice_keys),
        },
    }


def build_low_confidence_markdown(report: dict[str, Any]) -> str:
    lines = ["# Low-Confidence Diagnostics", "", "## Category Summary"]
    for category in report.get("category_summaries", []):
        lines.append(
            f"- {category['event_category']}: low={category['low_count']}, moderate={category['moderate_count']}, "
            f"high={category['high_count']}, low_ratio={category['low_ratio']:.2%}, causes={category['dominant_causes']}"
        )

    lines.extend(["", "## Top Low-Confidence Slices"])
    for item in report.get("top_low_confidence_slices", [])[:12]:
        lines.append(
            f"- {item['slice_key']}: low={item['low_count']}/{item['signal_count']}, "
            f"sample={item['average_sample_size']}, fallback_ratio={item['fallback_ratio']:.2%}, causes={item['dominant_causes']}"
        )

    lines.extend(["", "## Efficient Upgrade Candidates"])
    for item in report.get("efficient_upgrade_candidates", []):
        lines.append(
            f"- {item['slice_key']}: linked_gap_size={item['linked_gap_size']}, low={item['low_count']}, "
            f"sample={item['average_sample_size']}, note={item['improvement_note']}"
        )

    lines.extend(["", "## Focus Slices"])
    for slice_key, item in report.get("focus_slices", {}).items():
        if item is None:
            lines.append(f"- {slice_key}: not present in current signal set.")
            continue
        lines.append(
            f"- {slice_key}: low={item['low_count']}/{item['signal_count']}, "
            f"sample={item['average_sample_size']}, causes={item['dominant_causes']}, note={item['improvement_note']}"
        )

    return "\n".join(lines) + "\n"


def write_low_confidence_reports(report: dict[str, Any], json_output: Path, markdown_output: Path) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    markdown_output.write_text(build_low_confidence_markdown(report), encoding="utf-8")


def build_low_confidence_diff(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    before_categories = {item["event_category"]: item for item in before.get("category_summaries", [])}
    after_categories = {item["event_category"]: item for item in after.get("category_summaries", [])}
    category_changes = []
    for event_category in sorted(set(before_categories) | set(after_categories)):
        before_item = before_categories.get(event_category, {})
        after_item = after_categories.get(event_category, {})
        category_changes.append(
            {
                "event_category": event_category,
                "low_before": before_item.get("low_count", 0),
                "low_after": after_item.get("low_count", 0),
                "low_delta": after_item.get("low_count", 0) - before_item.get("low_count", 0),
                "low_ratio_before": before_item.get("low_ratio", 0),
                "low_ratio_after": after_item.get("low_ratio", 0),
                "dominant_causes_after": after_item.get("dominant_causes", []),
            }
        )

    before_focus = before.get("focus_slices", {})
    after_focus = after.get("focus_slices", {})
    focus_slice_changes: dict[str, Any] = {}
    for slice_key in sorted(set(before_focus) | set(after_focus)):
        focus_slice_changes[slice_key] = {
            "before": before_focus.get(slice_key),
            "after": after_focus.get(slice_key),
        }

    before_top_slices = {item["slice_key"]: item for item in before.get("top_low_confidence_slices", [])}
    after_top_slices = {item["slice_key"]: item for item in after.get("top_low_confidence_slices", [])}
    exact_slice_changes: list[dict[str, Any]] = []
    for slice_key in sorted(set(before_top_slices) | set(after_top_slices) | set(before_focus) | set(after_focus)):
        before_item = before_focus.get(slice_key) or before_top_slices.get(slice_key)
        after_item = after_focus.get(slice_key) or after_top_slices.get(slice_key)
        exact_slice_changes.append(
            {
                "slice_key": slice_key,
                "low_before": before_item.get("low_count", 0) if before_item else 0,
                "low_after": after_item.get("low_count", 0) if after_item else 0,
                "low_delta": (after_item.get("low_count", 0) if after_item else 0) - (before_item.get("low_count", 0) if before_item else 0),
                "low_ratio_before": before_item.get("low_ratio", 0) if before_item else 0,
                "low_ratio_after": after_item.get("low_ratio", 0) if after_item else 0,
                "sample_before": before_item.get("average_sample_size", 0) if before_item else 0,
                "sample_after": after_item.get("average_sample_size", 0) if after_item else 0,
                "signal_count_before": before_item.get("signal_count", 0) if before_item else 0,
                "signal_count_after": after_item.get("signal_count", 0) if after_item else 0,
                "linked_gap_size_after": after_item.get("linked_gap_size") if after_item else None,
                "dominant_causes_before": before_item.get("dominant_causes", []) if before_item else [],
                "dominant_causes_after": after_item.get("dominant_causes", []) if after_item else [],
                "improvement_note_after": after_item.get("improvement_note") if after_item else None,
            }
        )

    exact_slice_changes.sort(
        key=lambda item: (
            -(item["signal_count_after"] or item["signal_count_before"]),
            -(item["low_after"] or item["low_before"]),
            item["slice_key"],
        )
    )

    return {
        "category_changes": category_changes,
        "focus_slice_changes": focus_slice_changes,
        "exact_slice_changes": exact_slice_changes[:20],
        "efficient_upgrade_candidates_after": after.get("efficient_upgrade_candidates", [])[:10],
    }


def build_low_confidence_diff_markdown(diff: dict[str, Any]) -> str:
    lines = ["# Low-Confidence Diagnostics Diff", "", "## Category Changes"]
    for item in diff.get("category_changes", []):
        lines.append(
            f"- {item['event_category']}: low {item['low_before']} -> {item['low_after']} "
            f"(delta {item['low_delta']:+d}), low_ratio {item['low_ratio_before']:.2%} -> {item['low_ratio_after']:.2%}, "
            f"after_causes={item['dominant_causes_after']}"
        )

    lines.extend(["", "## Focus Slice Changes"])
    for slice_key, item in diff.get("focus_slice_changes", {}).items():
        before = item.get("before")
        after = item.get("after")
        if before is None and after is None:
            lines.append(f"- {slice_key}: no signals before or after.")
            continue
        lines.append(
            f"- {slice_key}: low {before.get('low_count', 0) if before else 0} -> {after.get('low_count', 0) if after else 0}, "
            f"sample {before.get('average_sample_size', 0) if before else 0} -> {after.get('average_sample_size', 0) if after else 0}, "
            f"causes {before.get('dominant_causes', []) if before else []} -> {after.get('dominant_causes', []) if after else []}"
        )

    lines.extend(["", "## Exact Slice Changes"])
    for item in diff.get("exact_slice_changes", [])[:12]:
        lines.append(
            f"- {item['slice_key']}: low {item['low_before']} -> {item['low_after']} "
            f"(delta {item['low_delta']:+d}), sample {item['sample_before']} -> {item['sample_after']}, "
            f"causes {item['dominant_causes_before']} -> {item['dominant_causes_after']}, "
            f"after_note={item['improvement_note_after']}"
        )

    lines.extend(["", "## Efficient Upgrade Candidates After"])
    for item in diff.get("efficient_upgrade_candidates_after", []):
        lines.append(
            f"- {item['slice_key']}: linked_gap_size={item['linked_gap_size']}, low={item['low_count']}, note={item['improvement_note']}"
        )

    return "\n".join(lines) + "\n"


def write_low_confidence_diff(diff: dict[str, Any], json_output: Path, markdown_output: Path) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(diff, indent=2), encoding="utf-8")
    markdown_output.write_text(build_low_confidence_diff_markdown(diff), encoding="utf-8")
