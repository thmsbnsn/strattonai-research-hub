from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

try:
    from ingestion.write_to_supabase import SupabaseWriter
except ImportError:  # pragma: no cover - script execution fallback
    from write_to_supabase import SupabaseWriter  # type: ignore

from .coverage_audit import build_coverage_audit_report
from .coverage_audit_diff import build_snapshot_from_studies_and_signals
from .coverage_models import (
    CoverageAuditReport,
    CoverageEvent,
    CoverageRelationshipEdge,
    CoverageRelatedCompany,
    CoverageSignal,
    CoverageStudyStatistic,
)
from .event_study_engine import aggregate_observations, build_price_map, compute_event_study_observations
from .event_study_models import StudyEvent, StudyRelatedCompany
from .price_dataset import collect_study_tickers, describe_resolution, load_resolved_price_series
from .signal_models import SignalEvent, SignalRelatedCompany, SignalStudyStatistic
from .signal_scoring import index_studies, score_event_signals


@dataclass(frozen=True, slots=True)
class TargetedExpansionBaselineArtifacts:
    report: CoverageAuditReport
    snapshot: dict[str, Any]
    coverage_studies: tuple[CoverageStudyStatistic, ...]
    coverage_signals: tuple[CoverageSignal, ...]
    scored_signals: tuple[Any, ...]
    observation_count: int
    observation_stats: dict[str, int]
    study_event_count: int
    signal_event_count: int
    price_dataset_path: str


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(UTC)


def _resolve_classifier_confidence(metadata: dict[str, Any] | None) -> str:
    classification = metadata.get("classification", {}) if isinstance(metadata, dict) else {}
    confidence = classification.get("confidence", "Low")
    return confidence if confidence in {"High", "Moderate", "Low"} else "Low"


def _to_coverage_studies(aggregates: list) -> list[CoverageStudyStatistic]:
    return [
        CoverageStudyStatistic(
            study_key=aggregate.study_key,
            study_target_type=aggregate.study_target_type,
            event_category=aggregate.event_category,
            primary_ticker=aggregate.primary_ticker,
            related_ticker=aggregate.related_ticker,
            relationship_type=aggregate.relationship_type,
            horizon=aggregate.horizon,
            sample_size=aggregate.sample_size,
        )
        for aggregate in aggregates
    ]


def _to_signal_studies(aggregates: list) -> list[SignalStudyStatistic]:
    return [
        SignalStudyStatistic(
            study_key=aggregate.study_key,
            study_target_type=aggregate.study_target_type,
            event_category=aggregate.event_category,
            primary_ticker=aggregate.primary_ticker,
            related_ticker=aggregate.related_ticker,
            relationship_type=aggregate.relationship_type,
            horizon=aggregate.horizon,
            sample_size=aggregate.sample_size,
            avg_return=aggregate.avg_return,
            median_return=aggregate.median_return,
            win_rate=aggregate.win_rate,
            notes=aggregate.notes,
            metadata=aggregate.metadata,
        )
        for aggregate in aggregates
    ]


def _to_coverage_signals(signals: list) -> list[CoverageSignal]:
    coverage_signals: list[CoverageSignal] = []
    for signal in signals:
        rationale = signal.rationale if isinstance(signal.rationale, dict) else {}
        study = rationale.get("study", {}) if isinstance(rationale, dict) else {}
        study_target_type = study.get("study_target_type") if isinstance(study, dict) else None
        coverage_signals.append(
            CoverageSignal(
                event_category=signal.event_category,
                primary_ticker=signal.primary_ticker,
                target_ticker=signal.target_ticker,
                target_type=signal.target_type,
                relationship_type=signal.relationship_type,
                horizon=signal.horizon,
                confidence_band=signal.confidence_band,
                source_study_target_type=str(study_target_type) if study_target_type else None,
            )
        )
    return coverage_signals


class TargetedExpansionBaselineRepository(SupabaseWriter):
    def load_baseline_inputs(
        self,
        excluded_identities: set[tuple[str, str]],
        now: datetime,
        signal_lookback_days: int = 180,
        signal_limit: int = 1000,
    ) -> tuple[
        list[CoverageEvent],
        list[CoverageRelatedCompany],
        list[CoverageRelationshipEdge],
        list[StudyEvent],
        list[SignalEvent],
    ]:
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select
                      id::text,
                      source_name,
                      source_record_id,
                      ticker,
                      category,
                      timestamp,
                      headline,
                      sentiment,
                      metadata
                    from public.events
                    order by timestamp asc, id asc
                    """
                )
                event_rows = cursor.fetchall()

                filtered_rows = [
                    row
                    for row in event_rows
                    if (str(row[1] or ""), str(row[2] or "")) not in excluded_identities
                ]
                event_ids = [row[0] for row in filtered_rows]

                related_rows: list[tuple[str, str, str, str, str, str, dict[str, Any] | None]] = []
                if event_ids:
                    cursor.execute(
                        """
                        select
                          event_id::text,
                          source_ticker,
                          target_ticker,
                          coalesce(relationship_type, relationship) as relationship_type,
                          origin_type,
                          coalesce(name, target_ticker) as related_name,
                          rationale
                        from public.related_companies
                        where event_id = any(%s::uuid[])
                        order by event_id asc, target_ticker asc, relationship_type asc
                        """,
                        (event_ids,),
                    )
                    related_rows = cursor.fetchall()

                cursor.execute(
                    """
                    select source_ticker, target_ticker, relationship_type, strength
                    from public.company_relationship_graph
                    order by source_ticker asc, target_ticker asc, relationship_type asc
                    """
                )
                graph_rows = cursor.fetchall()

        related_for_studies: dict[str, list[StudyRelatedCompany]] = defaultdict(list)
        related_for_signals: dict[str, list[SignalRelatedCompany]] = defaultdict(list)
        coverage_related: list[CoverageRelatedCompany] = []

        for event_id, source_ticker, target_ticker, relationship_type, origin_type, _related_name, rationale in related_rows:
            resolved_relationship = relationship_type or "Related"
            resolved_origin = origin_type or "explicit"
            if resolved_origin not in {"explicit", "inferred"}:
                resolved_origin = "explicit"

            related_for_studies[event_id].append(
                StudyRelatedCompany(
                    target_ticker=target_ticker,
                    relationship_type=resolved_relationship,
                    origin_type=resolved_origin,
                )
            )
            related_for_signals[event_id].append(
                SignalRelatedCompany(
                    target_ticker=target_ticker,
                    relationship_type=resolved_relationship,
                    origin_type=resolved_origin,  # type: ignore[arg-type]
                    rationale=rationale or {},
                )
            )
            coverage_related.append(
                CoverageRelatedCompany(
                    event_id=event_id,
                    source_ticker=source_ticker,
                    target_ticker=target_ticker,
                    relationship_type=resolved_relationship,
                    origin_type=resolved_origin,
                )
            )

        coverage_events: list[CoverageEvent] = []
        study_events: list[StudyEvent] = []
        signal_candidates: list[tuple[datetime, str, str, str, str, str, dict[str, Any] | None]] = []
        signal_cutoff = now - timedelta(days=signal_lookback_days)

        for event_id, source_name, _source_record_id, ticker, category, timestamp, headline, sentiment, metadata in filtered_rows:
            parsed_timestamp = _parse_timestamp(timestamp)
            coverage_events.append(
                CoverageEvent(
                    id=event_id,
                    source_name=str(source_name or "unknown"),
                    ticker=ticker,
                    category=category,
                )
            )
            study_events.append(
                StudyEvent(
                    id=event_id,
                    ticker=ticker,
                    category=category,
                    timestamp=parsed_timestamp,
                    related_companies=tuple(related_for_studies.get(event_id, [])),
                )
            )
            if parsed_timestamp >= signal_cutoff:
                signal_candidates.append(
                    (
                        parsed_timestamp,
                        event_id,
                        ticker,
                        category,
                        headline,
                        sentiment,
                        metadata or {},
                    )
                )

        signal_events: list[SignalEvent] = []
        for parsed_timestamp, event_id, ticker, category, headline, sentiment, metadata in sorted(
            signal_candidates,
            key=lambda row: (row[0], row[1]),
            reverse=True,
        )[:signal_limit]:
            classifier_rationale = metadata.get("classification", {}) if isinstance(metadata, dict) else {}
            signal_events.append(
                SignalEvent(
                    id=event_id,
                    ticker=ticker,
                    category=category,
                    timestamp=parsed_timestamp,
                    headline=headline,
                    sentiment=sentiment,
                    classifier_confidence=_resolve_classifier_confidence(metadata),  # type: ignore[arg-type]
                    classifier_rationale=classifier_rationale if isinstance(classifier_rationale, dict) else {},
                    related_companies=tuple(related_for_signals.get(event_id, [])),
                )
            )

        relationship_graph = [
            CoverageRelationshipEdge(
                source_ticker=source_ticker,
                target_ticker=target_ticker,
                relationship_type=relationship_type,
                strength=float(strength or 0),
            )
            for source_ticker, target_ticker, relationship_type, strength in graph_rows
        ]

        return coverage_events, coverage_related, relationship_graph, study_events, signal_events


def build_targeted_expansion_baseline(
    repo_root: Path,
    price_file: str | Path | None,
    excluded_identities: set[tuple[str, str]],
    now: datetime,
    focused_related_slices: tuple[tuple[str, str, str], ...] = (),
    focused_primary_slices: tuple[tuple[str, str], ...] = (),
) -> TargetedExpansionBaselineArtifacts:
    repository = TargetedExpansionBaselineRepository(repo_root)
    (
        coverage_events,
        coverage_related,
        relationship_graph,
        study_events,
        signal_events,
    ) = repository.load_baseline_inputs(excluded_identities=excluded_identities, now=now)

    price_series, resolved_price_dataset = load_resolved_price_series(
        repo_root,
        price_file,
        tickers=collect_study_tickers(study_events),
    )
    price_map = build_price_map(price_series)
    price_days_by_ticker = {series.ticker: len(series.prices) for series in price_series}

    observations, observation_stats = compute_event_study_observations(study_events, price_map)
    aggregates = aggregate_observations(observations)

    coverage_studies = _to_coverage_studies(aggregates)
    signal_studies = _to_signal_studies(aggregates)
    indexed_studies = index_studies(signal_studies)
    scored_signals = []
    for event in signal_events:
        scored_signals.extend(score_event_signals(event, indexed_studies, now=now))
    coverage_signals = _to_coverage_signals(scored_signals)

    report = build_coverage_audit_report(
        events=coverage_events,
        related_companies=coverage_related,
        relationship_graph=relationship_graph,
        studies=coverage_studies,
        signals=coverage_signals,
        price_days_by_ticker=price_days_by_ticker,
        price_file=resolved_price_dataset.path,
    )
    report.notes["baseline_reconstructed"] = True
    report.notes["price_resolution_reason"] = resolved_price_dataset.resolution_reason
    report.notes["price_format"] = resolved_price_dataset.format
    report.notes["price_used_sample_fallback"] = resolved_price_dataset.used_sample_fallback
    report.notes["price_resolution"] = describe_resolution(resolved_price_dataset)
    report.notes["excluded_event_identities"] = [
        {"source_name": source_name, "source_record_id": source_record_id}
        for source_name, source_record_id in sorted(excluded_identities)
    ]

    snapshot = build_snapshot_from_studies_and_signals(
        report.to_dict(),
        coverage_studies,
        coverage_signals,
        focused_related_slices=focused_related_slices,
        focused_primary_slices=focused_primary_slices,
    )
    return TargetedExpansionBaselineArtifacts(
        report=report,
        snapshot=snapshot,
        coverage_studies=tuple(coverage_studies),
        coverage_signals=tuple(coverage_signals),
        scored_signals=tuple(scored_signals),
        observation_count=len(observations),
        observation_stats=observation_stats,
        study_event_count=len(study_events),
        signal_event_count=len(signal_events),
        price_dataset_path=str(resolved_price_dataset.path),
    )
