from __future__ import annotations

import argparse
import logging
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from .signal_scoring import index_studies, score_event_signals
from .write_signals_to_supabase import SignalSupabaseWriter


LOGGER = logging.getLogger("research.rescore_all_recent_events")


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format="%(levelname)s %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rescore recent events after backfill and study recomputation.")
    parser.add_argument("--lookback-days", type=int, default=120, help="Recent event window to rescore.")
    parser.add_argument("--limit-events", type=int, default=500, help="Maximum number of recent events to rescore.")
    parser.add_argument("--dry-run", action="store_true", help="Compute signals without writing to Supabase.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")
    return parser.parse_args()


def _current_distribution(writer: SignalSupabaseWriter) -> tuple[int, dict[str, int]]:
    with writer.connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("select count(*) from public.signal_scores")
            count = cursor.fetchone()[0]
            cursor.execute("select confidence_band, count(*) from public.signal_scores group by confidence_band")
            distribution = {band: total for band, total in cursor.fetchall()}
    return count, distribution


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)

    repo_root = Path(__file__).resolve().parent.parent
    writer = SignalSupabaseWriter(repo_root)
    before_count, before_distribution = _current_distribution(writer)

    events = writer.load_recent_signal_events(lookback_days=args.lookback_days, limit_events=args.limit_events)
    studies = writer.load_signal_study_statistics()
    indexed_studies = index_studies(studies)
    now = datetime.now(UTC)

    signals = []
    for event in events:
        signals.extend(score_event_signals(event, indexed_studies, now=now))

    computed_distribution = Counter(signal.confidence_band for signal in signals)
    LOGGER.info(
        "Computed %s signal(s) from %s event(s). Confidence distribution=%s",
        len(signals),
        len(events),
        dict(sorted(computed_distribution.items())),
    )

    if args.dry_run:
        LOGGER.info("Dry run complete. No database writes were performed.")
        return 0

    upserted = writer.upsert_signal_scores(signals)
    after_count, after_distribution = _current_distribution(writer)
    LOGGER.info(
        "Signals updated. Before count=%s distribution=%s. After count=%s distribution=%s. Upserted=%s.",
        before_count,
        dict(sorted(before_distribution.items())),
        after_count,
        dict(sorted(after_distribution.items())),
        upserted,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
