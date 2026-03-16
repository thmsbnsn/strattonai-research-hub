from __future__ import annotations

import logging
import os
from dataclasses import replace
from pathlib import Path
from urllib.parse import urlparse

import psycopg
from psycopg.types.json import Jsonb

try:
    from .models import NormalizedEvent, NormalizedRelatedCompany, NormalizedResearchInsight, WriteSummary
    from .normalize import rebind_event_id
except ImportError:  # pragma: no cover - script execution fallback
    from models import NormalizedEvent, NormalizedRelatedCompany, NormalizedResearchInsight, WriteSummary  # type: ignore
    from normalize import rebind_event_id  # type: ignore

LOGGER = logging.getLogger("ingestion.write_to_supabase")


def load_env_from_file(path: Path) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        key, raw_value = stripped.split("=", 1)
        value = raw_value.strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), value)


def load_ingestion_environment(repo_root: Path) -> None:
    load_env_from_file(repo_root / ".env")
    load_env_from_file(repo_root.parent / ".env")


def build_postgres_dsn() -> str:
    project_url = os.environ.get("SUPABASE_PROJECT_URL")
    db_password = os.environ.get("SUPABASE_DATABASE_PASSWORD")

    if not project_url:
        raise RuntimeError("SUPABASE_PROJECT_URL is required.")

    if not db_password:
        raise RuntimeError("SUPABASE_DATABASE_PASSWORD is required.")

    parsed = urlparse(project_url)
    project_ref = parsed.netloc.split(".")[0]

    if not project_ref:
        raise RuntimeError(f"Could not derive Supabase project reference from {project_url}")

    return (
        f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"
        "?sslmode=require"
    )


class SupabaseWriter:
    def __init__(self, repo_root: Path):
        load_ingestion_environment(repo_root)
        self.repo_root = repo_root
        self._dsn = build_postgres_dsn()

    def connect(self) -> psycopg.Connection:
        return psycopg.connect(self._dsn, autocommit=False)

    def apply_sql_file(self, sql_path: Path) -> None:
        LOGGER.info("Applying SQL file: %s", sql_path)
        sql_text = sql_path.read_text(encoding="utf-8")

        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql_text)
            connection.commit()

    def resolve_existing_event_id(self, cursor: psycopg.Cursor, event: NormalizedEvent) -> str | None:
        cursor.execute(
            """
            select id::text
            from public.events
            where source_name = %s
              and source_record_id = %s
            limit 1
            """,
            (event.source_name, event.source_record_id),
        )
        row = cursor.fetchone()
        if row:
            return row[0]

        cursor.execute(
            """
            select id::text
            from public.events
            where ticker = %s
              and headline = %s
              and timestamp = %s
            limit 1
            """,
            (event.ticker, event.headline, event.timestamp),
        )
        row = cursor.fetchone()
        return row[0] if row else None

    def resolve_existing_related_company_id(
        self,
        cursor: psycopg.Cursor,
        related_company: NormalizedRelatedCompany,
    ) -> str | None:
        cursor.execute(
            """
            select id::text
            from public.related_companies
            where event_id = %s
              and source_ticker = %s
              and target_ticker = %s
              and coalesce(relationship_type, relationship) = %s
            limit 1
            """,
            (
                related_company.event_id,
                related_company.source_ticker,
                related_company.target_ticker,
                related_company.relationship,
            ),
        )
        row = cursor.fetchone()
        return row[0] if row else None

    def resolve_existing_insight_id(
        self,
        cursor: psycopg.Cursor,
        insight: NormalizedResearchInsight,
    ) -> str | None:
        cursor.execute(
            """
            select id::text
            from public.research_insights
            where lower(title) = lower(%s)
            limit 1
            """,
            (insight.title,),
        )
        row = cursor.fetchone()
        return row[0] if row else None

    def upsert_events(self, events: list[NormalizedEvent]) -> WriteSummary:
        summary = WriteSummary()

        with self.connect() as connection:
            with connection.cursor() as cursor:
                for event in events:
                    existing_event_id = self.resolve_existing_event_id(cursor, event)
                    resolved_event = rebind_event_id(event, existing_event_id or event.id)

                    cursor.execute(
                        """
                        insert into public.events (
                            id,
                            source_name,
                            source_record_id,
                            headline,
                            ticker,
                            category,
                            sentiment,
                            timestamp,
                            historical_analog,
                            sample_size,
                            avg_return,
                            details,
                            metadata
                        )
                        values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        on conflict (id) do update
                        set
                            source_name = excluded.source_name,
                            source_record_id = excluded.source_record_id,
                            headline = excluded.headline,
                            ticker = excluded.ticker,
                            category = excluded.category,
                            sentiment = excluded.sentiment,
                            timestamp = excluded.timestamp,
                            historical_analog = excluded.historical_analog,
                            sample_size = excluded.sample_size,
                            avg_return = excluded.avg_return,
                            details = excluded.details,
                            metadata = excluded.metadata,
                            updated_at = timezone('utc', now())
                        """,
                        (
                            resolved_event.id,
                            resolved_event.source_name,
                            resolved_event.source_record_id,
                            resolved_event.headline,
                            resolved_event.ticker,
                            resolved_event.category,
                            resolved_event.sentiment,
                            resolved_event.timestamp,
                            resolved_event.historical_analog,
                            resolved_event.sample_size,
                            resolved_event.avg_return,
                            resolved_event.details,
                            Jsonb(resolved_event.metadata),
                        ),
                    )
                    summary.events_upserted += 1
                    LOGGER.debug("Upserted event %s [%s]", resolved_event.headline, resolved_event.id)

                    for related_company in resolved_event.related_companies:
                        existing_related_id = self.resolve_existing_related_company_id(cursor, related_company)
                        resolved_related_company = replace(
                            related_company,
                            id=existing_related_id or related_company.id,
                        )
                        cursor.execute(
                            """
                            insert into public.related_companies (
                                id,
                                event_id,
                                graph_relationship_id,
                                source_ticker,
                                target_ticker,
                                name,
                                relationship,
                                relationship_type,
                                strength,
                                origin_type,
                                notes,
                                rationale
                            )
                            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            on conflict (id) do update
                            set
                                event_id = excluded.event_id,
                                graph_relationship_id = excluded.graph_relationship_id,
                                source_ticker = excluded.source_ticker,
                                target_ticker = excluded.target_ticker,
                                name = excluded.name,
                                relationship = excluded.relationship,
                                relationship_type = excluded.relationship_type,
                                strength = excluded.strength,
                                origin_type = excluded.origin_type,
                                notes = excluded.notes,
                                rationale = excluded.rationale,
                                updated_at = timezone('utc', now())
                            """,
                            (
                                resolved_related_company.id,
                                resolved_related_company.event_id,
                                resolved_related_company.graph_relationship_id,
                                resolved_related_company.source_ticker,
                                resolved_related_company.target_ticker,
                                resolved_related_company.name,
                                resolved_related_company.relationship,
                                resolved_related_company.relationship,
                                resolved_related_company.strength,
                                resolved_related_company.origin_type,
                                resolved_related_company.notes,
                                Jsonb(resolved_related_company.rationale),
                            ),
                        )
                        summary.related_companies_upserted += 1
                        LOGGER.debug(
                            "Upserted related company %s -> %s for event %s",
                            resolved_related_company.source_ticker,
                            resolved_related_company.target_ticker,
                            resolved_event.id,
                        )

                    if resolved_event.research_insight is not None:
                        existing_insight_id = self.resolve_existing_insight_id(cursor, resolved_event.research_insight)
                        resolved_insight = replace(
                            resolved_event.research_insight,
                            id=existing_insight_id or resolved_event.research_insight.id,
                        )
                        cursor.execute(
                            """
                            insert into public.research_insights (
                                id,
                                title,
                                summary,
                                confidence,
                                event_count
                            )
                            values (%s, %s, %s, %s, %s)
                            on conflict (id) do update
                            set
                                title = excluded.title,
                                summary = excluded.summary,
                                confidence = excluded.confidence,
                                event_count = excluded.event_count,
                                updated_at = timezone('utc', now())
                            """,
                            (
                                resolved_insight.id,
                                resolved_insight.title,
                                resolved_insight.summary,
                                resolved_insight.confidence,
                                resolved_insight.event_count,
                            ),
                        )
                        summary.research_insights_upserted += 1
                        LOGGER.debug("Upserted research insight %s [%s]", resolved_insight.title, resolved_insight.id)

            connection.commit()

        return summary

    def count_matching_events(self, events: list[NormalizedEvent]) -> int:
        if not events:
            return 0

        with self.connect() as connection:
            with connection.cursor() as cursor:
                total = 0
                for event in events:
                    cursor.execute(
                        """
                        select count(*)
                        from public.events
                        where ticker = %s
                          and headline = %s
                          and timestamp = %s
                        """,
                        (event.ticker, event.headline, event.timestamp),
                    )
                    total += cursor.fetchone()[0]
                return total
