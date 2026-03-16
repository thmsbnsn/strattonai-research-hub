from __future__ import annotations

import argparse
import logging
from datetime import UTC, datetime
from pathlib import Path

from .signal_scoring import index_studies, score_event_signals
from .write_signals_to_supabase import SignalSupabaseWriter


LOGGER = logging.getLogger("research.score_current_events")


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format="%(levelname)s %(message)s")


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Score recent events using deterministic event-study evidence.")
    parser.add_argument("--lookback-days", type=int, default=30, help="Recent event window to score.")
    parser.add_argument("--limit-events", type=int, default=50, help="Maximum number of recent events to score.")
    parser.add_argument("--dry-run", action="store_true", help="Compute signals without writing to Supabase.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")
    parser.add_argument(
        "--bootstrap-schema",
        action="store_true",
        help="Apply the signal table migration before scoring.",
    )
    parser.add_argument(
        "--schema-file",
        default=str(repo_root / "supabase" / "sql" / "007_add_signal_scores.sql"),
        help="SQL file to apply when --bootstrap-schema is set.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)

    repo_root = Path(__file__).resolve().parent.parent
    writer = SignalSupabaseWriter(repo_root)

    if args.bootstrap_schema:
        writer.apply_sql_file(Path(args.schema_file))

    events = writer.load_recent_signal_events(lookback_days=args.lookback_days, limit_events=args.limit_events)
    studies = writer.load_signal_study_statistics()
    indexed_studies = index_studies(studies)

    now = datetime.now(UTC)
    signals = []
    for event in events:
        signals.extend(score_event_signals(event, indexed_studies, now=now))

    LOGGER.info(
        "Scored %s signal(s) from %s recent event(s) using %s study statistic row(s).",
        len(signals),
        len(events),
        len(studies),
    )

    if args.dry_run:
        LOGGER.info("Dry run complete. No database writes were performed.")
        return 0

    upserted = writer.upsert_signal_scores(signals)
    verified = writer.count_matching_signals(signals)
    LOGGER.info("Upserted %s signal row(s) and verified %s matching row(s).", upserted, verified)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
