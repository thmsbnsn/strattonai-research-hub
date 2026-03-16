from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from psycopg.types.json import Jsonb

try:
    from ingestion.write_to_supabase import SupabaseWriter
except ImportError:  # pragma: no cover - script execution fallback
    from write_to_supabase import SupabaseWriter  # type: ignore

from .signal_models import SignalEvent, SignalRelatedCompany, SignalScore, SignalStudyStatistic


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(UTC)


def _to_decimal(value: Any) -> Decimal:
    return Decimal(str(value or 0))


class SignalSupabaseWriter(SupabaseWriter):
    def __init__(self, repo_root: Path):
        super().__init__(repo_root)

    def current_distribution(self) -> tuple[int, dict[str, int]]:
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("select count(*) from public.signal_scores")
                count = cursor.fetchone()[0]
                cursor.execute("select confidence_band, count(*) from public.signal_scores group by confidence_band")
                distribution = {band: total for band, total in cursor.fetchall()}
        return count, distribution

    def load_recent_signal_events(self, lookback_days: int = 30, limit_events: int = 100) -> list[SignalEvent]:
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select
                      id::text,
                      ticker,
                      category,
                      timestamp,
                      headline,
                      sentiment,
                      metadata
                    from public.events
                    where timestamp >= timezone('utc', now()) - (%s * interval '1 day')
                    order by timestamp desc
                    limit %s
                    """,
                    (lookback_days, limit_events),
                )
                event_rows = cursor.fetchall()

                event_ids = [row[0] for row in event_rows]
                related_rows: list[tuple[str, str, str, str, dict[str, Any] | None]] = []
                if event_ids:
                    cursor.execute(
                        """
                        select
                          event_id::text,
                          target_ticker,
                          coalesce(relationship_type, relationship) as relationship_type,
                          origin_type,
                          rationale
                        from public.related_companies
                        where event_id = any(%s::uuid[])
                        order by event_id asc, target_ticker asc
                        """,
                        (event_ids,),
                    )
                    related_rows = cursor.fetchall()

        related_by_event: dict[str, list[SignalRelatedCompany]] = defaultdict(list)
        for event_id, target_ticker, relationship_type, origin_type, rationale in related_rows:
            resolved_origin = origin_type or "explicit"
            if resolved_origin not in {"explicit", "inferred"}:
                resolved_origin = "explicit"

            related_by_event[event_id].append(
                SignalRelatedCompany(
                    target_ticker=target_ticker,
                    relationship_type=relationship_type or "Related",
                    origin_type=resolved_origin,
                    rationale=rationale or {},
                )
            )

        events: list[SignalEvent] = []
        for event_id, ticker, category, timestamp, headline, sentiment, metadata in event_rows:
            event_metadata = metadata or {}
            classification = event_metadata.get("classification", {}) if isinstance(event_metadata, dict) else {}
            classifier_confidence = classification.get("confidence", "Low")
            if classifier_confidence not in {"High", "Moderate", "Low"}:
                classifier_confidence = "Low"

            events.append(
                SignalEvent(
                    id=event_id,
                    ticker=ticker,
                    category=category,
                    timestamp=_parse_timestamp(timestamp),
                    headline=headline,
                    sentiment=sentiment,
                    classifier_confidence=classifier_confidence,
                    classifier_rationale=classification if isinstance(classification, dict) else {},
                    related_companies=tuple(related_by_event.get(event_id, [])),
                )
            )

        return events

    def load_signal_study_statistics(self) -> list[SignalStudyStatistic]:
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
                      sample_size,
                      avg_return,
                      median_return,
                      win_rate,
                      notes,
                      metadata
                    from public.event_study_statistics
                    order by event_category asc, horizon asc
                    """
                )
                rows = cursor.fetchall()

        return [
            SignalStudyStatistic(
                study_key=study_key,
                study_target_type=study_target_type,
                event_category=event_category,
                primary_ticker=primary_ticker,
                related_ticker=related_ticker,
                relationship_type=relationship_type,
                horizon=horizon,
                sample_size=sample_size,
                avg_return=_to_decimal(avg_return),
                median_return=_to_decimal(median_return),
                win_rate=_to_decimal(win_rate),
                notes=notes,
                metadata=metadata or {},
            )
            for (
                study_key,
                study_target_type,
                event_category,
                primary_ticker,
                related_ticker,
                relationship_type,
                horizon,
                sample_size,
                avg_return,
                median_return,
                win_rate,
                notes,
                metadata,
            ) in rows
        ]

    def upsert_signal_scores(self, signals: list[SignalScore]) -> int:
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("delete from public.signal_scores")
                for signal in signals:
                    cursor.execute(
                        """
                        insert into public.signal_scores (
                          id,
                          signal_key,
                          source_study_key,
                          event_id,
                          event_category,
                          primary_ticker,
                          target_ticker,
                          target_type,
                          relationship_type,
                          horizon,
                          score,
                          confidence_band,
                          evidence_summary,
                          rationale,
                          sample_size,
                          avg_return,
                          median_return,
                          win_rate,
                          origin_type
                        )
                        values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        on conflict (signal_key) do update
                        set
                          source_study_key = excluded.source_study_key,
                          event_id = excluded.event_id,
                          event_category = excluded.event_category,
                          primary_ticker = excluded.primary_ticker,
                          target_ticker = excluded.target_ticker,
                          target_type = excluded.target_type,
                          relationship_type = excluded.relationship_type,
                          horizon = excluded.horizon,
                          score = excluded.score,
                          confidence_band = excluded.confidence_band,
                          evidence_summary = excluded.evidence_summary,
                          rationale = excluded.rationale,
                          sample_size = excluded.sample_size,
                          avg_return = excluded.avg_return,
                          median_return = excluded.median_return,
                          win_rate = excluded.win_rate,
                          origin_type = excluded.origin_type,
                          updated_at = timezone('utc', now())
                        """,
                        (
                            signal.id,
                            signal.signal_key,
                            signal.source_study_key,
                            signal.event_id,
                            signal.event_category,
                            signal.primary_ticker,
                            signal.target_ticker,
                            signal.target_type,
                            signal.relationship_type,
                            signal.horizon,
                            signal.score,
                            signal.confidence_band,
                            signal.evidence_summary,
                            Jsonb(signal.rationale),
                            signal.sample_size,
                            signal.avg_return,
                            signal.median_return,
                            signal.win_rate,
                            signal.origin_type,
                        ),
                    )
            connection.commit()

        return len(signals)

    def count_matching_signals(self, signals: list[SignalScore]) -> int:
        if not signals:
            return 0

        with self.connect() as connection:
            with connection.cursor() as cursor:
                total = 0
                for signal in signals:
                    cursor.execute(
                        """
                        select count(*)
                        from public.signal_scores
                        where signal_key = %s
                        """,
                        (signal.signal_key,),
                    )
                    total += cursor.fetchone()[0]
        return total
