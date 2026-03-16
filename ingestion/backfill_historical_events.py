from __future__ import annotations

import argparse
import logging
from collections import Counter
from pathlib import Path

try:
    from .run_ingestion import configure_logging, load_records, normalize_records
    from .write_to_supabase import SupabaseWriter
except ImportError:  # pragma: no cover - script execution fallback
    from run_ingestion import configure_logging, load_records, normalize_records  # type: ignore
    from write_to_supabase import SupabaseWriter  # type: ignore


LOGGER = logging.getLogger("ingestion.backfill_historical_events")


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Backfill structured historical market events and SEC filings.")
    parser.add_argument(
        "--market-input",
        default=str(repo_root / "ingestion" / "sample_historical_events.json"),
        help="Historical market event JSON file.",
    )
    parser.add_argument(
        "--sec-input",
        default=str(repo_root / "ingestion" / "sample_historical_sec_filings.json"),
        help="Historical SEC filing JSON file.",
    )
    parser.add_argument("--skip-sec", action="store_true", help="Skip SEC filing ingestion.")
    parser.add_argument("--dry-run", action="store_true", help="Normalize records without writing to Supabase.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")
    return parser.parse_args()


def _count_events(writer: SupabaseWriter) -> int:
    with writer.connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("select count(*) from public.events")
            return cursor.fetchone()[0]


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)

    repo_root = Path(__file__).resolve().parent.parent
    writer = SupabaseWriter(repo_root)

    market_records = load_records("market-events", args.market_input)
    market_events, market_failures = normalize_records("market-events", market_records)

    sec_events = []
    sec_failures = []
    if not args.skip_sec:
        sec_records = load_records("sec-filings", args.sec_input)
        sec_events, sec_failures = normalize_records("sec-filings", sec_records)

    all_events = [*market_events, *sec_events]
    category_counts = Counter(event.category for event in all_events)
    source_counts = Counter(event.source_name for event in all_events)

    LOGGER.info(
        "Prepared %s normalized historical events across %s categories. Source mix=%s category coverage=%s",
        len(all_events),
        len(category_counts),
        dict(source_counts),
        dict(sorted(category_counts.items())),
    )

    if args.dry_run:
        LOGGER.info(
            "Dry run complete. Failures: market=%s sec=%s. No database writes were performed.",
            len(market_failures),
            len(sec_failures),
        )
        return 0 if not market_failures and not sec_failures else 1

    before_count = _count_events(writer)
    summary = writer.upsert_events(all_events)
    after_count = _count_events(writer)
    verified_count = writer.count_matching_events(all_events)

    LOGGER.info(
        "Historical backfill wrote events=%s related_companies=%s research_insights=%s. Event rows before=%s after=%s delta=%s verified=%s",
        summary.events_upserted,
        summary.related_companies_upserted,
        summary.research_insights_upserted,
        before_count,
        after_count,
        after_count - before_count,
        verified_count,
    )
    return 0 if not market_failures and not sec_failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
