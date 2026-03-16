from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from uuid import NAMESPACE_URL, uuid5

from psycopg.types.json import Jsonb

try:
    from ingestion.write_to_supabase import SupabaseWriter
except ImportError:  # pragma: no cover - script execution fallback
    from write_to_supabase import SupabaseWriter  # type: ignore

from .event_study_models import EventStudyAggregate, StudyEvent, StudyRelatedCompany


SUMMARY_NAMESPACE = uuid5(NAMESPACE_URL, "strattonai/event-study-summary")


class EventStudySupabaseWriter(SupabaseWriter):
    def current_counts(self) -> tuple[int, int]:
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("select count(*) from public.event_study_statistics")
                detailed = cursor.fetchone()[0]
                cursor.execute("select count(*) from public.event_study_results")
                summary = cursor.fetchone()[0]
        return detailed, summary

    def load_study_events(self) -> list[StudyEvent]:
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select id::text, ticker, category, timestamp
                    from public.events
                    order by timestamp asc
                    """
                )
                event_rows = cursor.fetchall()

                cursor.execute(
                    """
                    select
                      event_id::text,
                      target_ticker,
                      coalesce(relationship_type, relationship) as relationship_type,
                      origin_type
                    from public.related_companies
                    where event_id is not null
                    order by event_id asc, target_ticker asc
                    """
                )
                related_rows = cursor.fetchall()

        related_by_event: dict[str, list[StudyRelatedCompany]] = defaultdict(list)
        for event_id, target_ticker, relationship_type, origin_type in related_rows:
            related_by_event[event_id].append(
                StudyRelatedCompany(
                    target_ticker=target_ticker,
                    relationship_type=relationship_type,
                    origin_type=origin_type or "explicit",
                )
            )

        events: list[StudyEvent] = []
        for event_id, ticker, category, timestamp in event_rows:
            events.append(
                StudyEvent(
                    id=event_id,
                    ticker=ticker,
                    category=category,
                    timestamp=timestamp if isinstance(timestamp, datetime) else datetime.fromisoformat(str(timestamp)),
                    related_companies=tuple(related_by_event.get(event_id, [])),
                )
            )

        return events

    def upsert_event_study_aggregates(self, aggregates: list[EventStudyAggregate]) -> int:
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("delete from public.event_study_statistics")
                for aggregate in aggregates:
                    cursor.execute(
                        """
                        insert into public.event_study_statistics (
                          id,
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
                        )
                        values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        on conflict (study_key) do update
                        set
                          study_target_type = excluded.study_target_type,
                          event_category = excluded.event_category,
                          primary_ticker = excluded.primary_ticker,
                          related_ticker = excluded.related_ticker,
                          relationship_type = excluded.relationship_type,
                          horizon = excluded.horizon,
                          sample_size = excluded.sample_size,
                          avg_return = excluded.avg_return,
                          median_return = excluded.median_return,
                          win_rate = excluded.win_rate,
                          notes = excluded.notes,
                          metadata = excluded.metadata,
                          updated_at = timezone('utc', now())
                        """,
                        (
                            aggregate.id,
                            aggregate.study_key,
                            aggregate.study_target_type,
                            aggregate.event_category,
                            aggregate.primary_ticker,
                            aggregate.related_ticker,
                            aggregate.relationship_type,
                            aggregate.horizon,
                            aggregate.sample_size,
                            aggregate.avg_return,
                            aggregate.median_return,
                            aggregate.win_rate,
                            aggregate.notes,
                            Jsonb(aggregate.metadata),
                        ),
                    )

            connection.commit()

        return len(aggregates)

    def upsert_ui_summary_rows(self, aggregates: list[EventStudyAggregate]) -> int:
        category_summaries = [aggregate for aggregate in aggregates if aggregate.study_target_type == "category_summary"]

        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("delete from public.event_study_results")
                for aggregate in category_summaries:
                    summary_id = str(uuid5(SUMMARY_NAMESPACE, aggregate.study_key))
                    cursor.execute(
                        """
                        insert into public.event_study_results (
                          id,
                          event_type,
                          horizon,
                          avg_return,
                          win_rate,
                          sample_size
                        )
                        values (%s, %s, %s, %s, %s, %s)
                        on conflict (event_type, horizon) do update
                        set
                          avg_return = excluded.avg_return,
                          win_rate = excluded.win_rate,
                          sample_size = excluded.sample_size,
                          updated_at = timezone('utc', now())
                        """,
                        (
                            summary_id,
                            aggregate.event_category,
                            aggregate.horizon,
                            aggregate.avg_return,
                            aggregate.win_rate,
                            aggregate.sample_size,
                        ),
                    )

            connection.commit()

        return len(category_summaries)

    def count_matching_studies(self, aggregates: list[EventStudyAggregate]) -> int:
        if not aggregates:
            return 0

        with self.connect() as connection:
            with connection.cursor() as cursor:
                total = 0
                for aggregate in aggregates:
                    cursor.execute(
                        """
                        select count(*)
                        from public.event_study_statistics
                        where study_key = %s
                        """,
                        (aggregate.study_key,),
                    )
                    total += cursor.fetchone()[0]
        return total
