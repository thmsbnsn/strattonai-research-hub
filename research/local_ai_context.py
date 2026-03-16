from __future__ import annotations

from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from ingestion.write_to_supabase import build_postgres_dsn, load_ingestion_environment

from .local_ai_models import ContextCitation, LocalAIContext


def format_win_rate(value: object) -> str:
    numeric = float(value)
    percentage = numeric * 100 if abs(numeric) <= 1 else numeric
    return f"{percentage:.0f}%"


class LocalAIContextRepository:
    def __init__(self, repo_root: Path):
        load_ingestion_environment(repo_root)
        self.repo_root = repo_root
        self._dsn = build_postgres_dsn()

    def _optional_query(self, sql: str, params: tuple[object, ...] = ()) -> list[dict]:
        try:
            with psycopg.connect(self._dsn, autocommit=True, row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(sql, params)
                    return list(cursor.fetchall())
        except psycopg.errors.UndefinedTable:
            return []

    def fetch_context(self, ticker: str | None) -> LocalAIContext:
        normalized_ticker = ticker.strip().upper() if ticker else None

        profile = self._fetch_profile(normalized_ticker)
        latest_price = self._fetch_latest_price(normalized_ticker)
        signals = self._fetch_signals(normalized_ticker)
        events = self._fetch_events(normalized_ticker)
        relationships = self._fetch_relationships(normalized_ticker)
        studies = self._fetch_studies(normalized_ticker)
        insights = self._fetch_insights()

        notes: list[str] = []
        if normalized_ticker and not profile:
            notes.append(f"No company profile found for {normalized_ticker}.")
        if normalized_ticker and not latest_price:
            notes.append(f"No daily price rows are currently available for {normalized_ticker}.")
        if normalized_ticker and not signals:
            notes.append(f"No scored signals are currently available for {normalized_ticker}.")
        if normalized_ticker and not relationships:
            notes.append(f"No company-graph relationships are currently available for {normalized_ticker}.")
        if not events:
            notes.append("No recent event rows are currently available.")

        return LocalAIContext(
            ticker=normalized_ticker,
            company_name=(profile or {}).get("name"),
            profile=profile or {},
            latest_price=latest_price,
            signals=signals,
            events=events,
            relationships=relationships,
            studies=studies,
            insights=insights,
            notes=notes,
        )

    def _fetch_profile(self, ticker: str | None) -> dict | None:
        if not ticker:
            return None

        rows = self._optional_query(
            """
            select ticker, name, sector, industry, market_cap, pe, revenue, employees
            from public.company_profiles
            where ticker = %s
            limit 1
            """,
            (ticker,),
        )
        return rows[0] if rows else None

    def _fetch_latest_price(self, ticker: str | None) -> dict | None:
        if not ticker:
            return None

        rows = self._optional_query(
            """
            select ticker, trade_date, close, volume
            from public.daily_prices
            where ticker = %s
            order by trade_date desc
            limit 1
            """,
            (ticker,),
        )
        return rows[0] if rows else None

    def _fetch_signals(self, ticker: str | None) -> list[dict]:
        if ticker:
            return self._optional_query(
                """
                select
                  event_category,
                  primary_ticker,
                  target_ticker,
                  target_type,
                  relationship_type,
                  horizon,
                  score,
                  confidence_band,
                  evidence_summary,
                  sample_size,
                  avg_return,
                  median_return,
                  win_rate
                from public.signal_scores
                where primary_ticker = %s or target_ticker = %s
                order by score desc
                limit 6
                """,
                (ticker, ticker),
            )

        return self._optional_query(
            """
            select
              event_category,
              primary_ticker,
              target_ticker,
              target_type,
              relationship_type,
              horizon,
              score,
              confidence_band,
              evidence_summary,
              sample_size,
              avg_return,
              median_return,
              win_rate
            from public.signal_scores
            order by score desc
            limit 6
            """
        )

    def _fetch_events(self, ticker: str | None) -> list[dict]:
        if ticker:
            return self._optional_query(
                """
                select distinct
                  e.id::text,
                  e.ticker,
                  e.category,
                  e.sentiment,
                  e.timestamp,
                  e.headline
                from public.events e
                left join public.related_companies rc on rc.event_id = e.id
                where e.ticker = %s or rc.target_ticker = %s
                order by e.timestamp desc
                limit 6
                """,
                (ticker, ticker),
            )

        return self._optional_query(
            """
            select id::text, ticker, category, sentiment, timestamp, headline
            from public.events
            order by timestamp desc
            limit 6
            """
        )

    def _fetch_relationships(self, ticker: str | None) -> list[dict]:
        if not ticker:
            return []

        return self._optional_query(
            """
            select
              source_ticker,
              source_name,
              target_ticker,
              target_name,
              relationship_type,
              strength
            from public.company_relationship_graph
            where source_ticker = %s or target_ticker = %s
            order by strength desc
            limit 6
            """,
            (ticker, ticker),
        )

    def _fetch_studies(self, ticker: str | None) -> list[dict]:
        if ticker:
            return self._optional_query(
                """
                select
                  event_category,
                  study_target_type,
                  primary_ticker,
                  related_ticker,
                  relationship_type,
                  horizon,
                  sample_size,
                  avg_return,
                  median_return,
                  win_rate
                from public.event_study_statistics
                where primary_ticker = %s or related_ticker = %s
                order by sample_size desc, abs(avg_return) desc
                limit 6
                """,
                (ticker, ticker),
            )

        return self._optional_query(
            """
            select
              event_category,
              study_target_type,
              primary_ticker,
              related_ticker,
              relationship_type,
              horizon,
              sample_size,
              avg_return,
              median_return,
              win_rate
            from public.event_study_statistics
            where study_target_type = 'category_summary'
            order by sample_size desc, abs(avg_return) desc
            limit 6
            """
        )

    def _fetch_insights(self) -> list[dict]:
        return self._optional_query(
            """
            select title, summary, confidence, event_count
            from public.research_insights
            order by event_count desc
            limit 4
            """
        )


def build_context_citations(context: LocalAIContext) -> list[ContextCitation]:
    citations: list[ContextCitation] = []

    for signal in context.signals[:3]:
        citations.append(
            ContextCitation(
                kind="signal",
                title=f"{signal['event_category']} · {signal['horizon']}",
                detail=(
                    f"score {float(signal['score']):.1f}, {signal['confidence_band']} confidence, "
                    f"sample n={int(signal['sample_size'])}"
                ),
                ticker=signal.get("target_ticker") or signal.get("primary_ticker"),
            )
        )

    for event in context.events[:2]:
        citations.append(
            ContextCitation(
                kind="event",
                title=f"{event['ticker']} · {event['category']}",
                detail=str(event["headline"]),
                ticker=event.get("ticker"),
            )
        )

    for study in context.studies[:2]:
        citations.append(
            ContextCitation(
                kind="study",
                title=f"{study['event_category']} · {study['horizon']}",
                detail=(
                    f"{study['study_target_type']} study, avg {float(study['avg_return']):.2f}%, "
                    f"win rate {format_win_rate(study['win_rate'])}, n={int(study['sample_size'])}"
                ),
                ticker=study.get("primary_ticker") or study.get("related_ticker"),
            )
        )

    return citations


def build_grounding_notes(context: LocalAIContext) -> list[str]:
    notes = list(context.notes)
    if context.ticker:
        notes.append(f"Focus ticker: {context.ticker}")
    if context.latest_price:
        notes.append(
            f"Latest stored close: {context.latest_price['ticker']} {float(context.latest_price['close']):.2f} on {context.latest_price['trade_date']}"
        )
    return notes


def build_context_prompt(context: LocalAIContext) -> str:
    sections: list[str] = []

    if context.ticker:
        sections.append(f"Focus ticker: {context.ticker}")
    if context.company_name:
        sections.append(f"Company name: {context.company_name}")
    if context.profile:
        sections.append(
            "Profile: "
            + ", ".join(
                str(part)
                for part in (
                    context.profile.get("sector"),
                    context.profile.get("industry"),
                    context.profile.get("market_cap"),
                )
                if part
            )
        )
    if context.latest_price:
        sections.append(
            f"Latest price: close {float(context.latest_price['close']):.2f} on {context.latest_price['trade_date']}"
        )
    if context.signals:
        sections.append(
            "Signals:\n"
            + "\n".join(
                f"- {signal['event_category']} {signal['horizon']} | "
                f"score {float(signal['score']):.1f} | {signal['confidence_band']} | "
                f"sample n={int(signal['sample_size'])}"
                for signal in context.signals[:4]
            )
        )
    if context.events:
        sections.append(
            "Recent events:\n"
            + "\n".join(
                f"- {event['ticker']} {event['category']} | {event['headline']}"
                for event in context.events[:4]
            )
        )
    if context.relationships:
        sections.append(
            "Relationships:\n"
            + "\n".join(
                f"- {relationship['source_ticker']} -> {relationship['target_ticker']} | "
                f"{relationship['relationship_type']} | strength {float(relationship['strength']):.2f}"
                for relationship in context.relationships[:4]
            )
        )
    if context.studies:
        sections.append(
            "Study evidence:\n"
            + "\n".join(
                f"- {study['event_category']} {study['horizon']} | {study['study_target_type']} | "
                f"avg {float(study['avg_return']):.2f}% | median {float(study['median_return']):.2f}% | "
                f"win rate {format_win_rate(study['win_rate'])} | n={int(study['sample_size'])}"
                for study in context.studies[:4]
            )
        )
    if context.insights:
        sections.append(
            "Research insights:\n"
            + "\n".join(
                f"- {insight['title']} | {insight['confidence']} | n={int(insight['event_count'])}"
                for insight in context.insights[:3]
            )
        )
    if context.notes:
        sections.append("Notes:\n" + "\n".join(f"- {note}" for note in context.notes))

    return "\n\n".join(section for section in sections if section.strip())


def build_deterministic_fallback_answer(message: str, context: LocalAIContext, trading_mode: str) -> str:
    if context.ticker and context.signals:
        best_signal = context.signals[0]
        event_phrase = f"{best_signal['event_category']} on a {best_signal['horizon']} horizon"
        return (
            f"{context.ticker} currently has structured research coverage. The strongest stored signal is "
            f"{event_phrase} with score {float(best_signal['score']):.1f}, "
            f"{best_signal['confidence_band']} confidence, and sample size n={int(best_signal['sample_size'])}. "
            f"Use this as a research lead, not an execution instruction. Current trading mode is {trading_mode}."
        )

    if context.ticker and context.events:
        latest_event = context.events[0]
        return (
            f"I have event context for {context.ticker}, but scored signal evidence is limited right now. "
            f"The latest stored event is {latest_event['category']}: {latest_event['headline']}. "
            "More study depth is needed before treating it as a high-confidence setup."
        )

    return (
        "The local AI gateway is running, but structured research context for this request is limited. "
        "Select a supported ticker or ask about a company that already has events, signals, and study evidence in StrattonAI."
    )
