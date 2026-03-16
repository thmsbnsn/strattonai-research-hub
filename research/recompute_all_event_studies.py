from __future__ import annotations

import argparse
import logging
from collections import Counter
from pathlib import Path

from .event_study_engine import aggregate_observations, build_price_map, compute_event_study_observations
from .price_dataset import collect_study_tickers, describe_resolution, load_resolved_price_series
from .write_event_studies_to_supabase import EventStudySupabaseWriter


LOGGER = logging.getLogger("research.recompute_all_event_studies")


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format="%(levelname)s %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recompute all event studies using the extended local price history.")
    parser.add_argument(
        "--price-file",
        default=None,
        help="Optional explicit price dataset path (.parquet, .csv, or .json). Defaults resolve to Parquet first.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Compute studies without writing to Supabase.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")
    return parser.parse_args()


def _count_existing(writer: EventStudySupabaseWriter) -> tuple[int, int]:
    with writer.connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("select count(*) from public.event_study_statistics")
            detail_count = cursor.fetchone()[0]
            cursor.execute("select count(*) from public.event_study_results")
            summary_count = cursor.fetchone()[0]
    return detail_count, summary_count


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)

    repo_root = Path(__file__).resolve().parent.parent
    writer = EventStudySupabaseWriter(repo_root)
    before_detail_count, before_summary_count = _count_existing(writer)

    events = writer.load_study_events()
    tickers = collect_study_tickers(events)
    price_series, resolved_price_dataset = load_resolved_price_series(repo_root, args.price_file, tickers=tickers)
    LOGGER.info("Using price dataset %s", describe_resolution(resolved_price_dataset))
    price_map = build_price_map(price_series)
    observations, stats = compute_event_study_observations(events, price_map)
    aggregates = aggregate_observations(observations)

    coverage = Counter(aggregate.event_category for aggregate in aggregates if aggregate.study_target_type == "category_summary")
    LOGGER.info(
        "Computed %s observation(s) and %s aggregate study row(s). Missing primary=%s missing related=%s missing horizon=%s. Category summaries=%s",
        len(observations),
        len(aggregates),
        stats["missing_primary_series"],
        stats["missing_related_series"],
        stats["missing_horizon"],
        dict(sorted(coverage.items())),
    )

    if args.dry_run:
        LOGGER.info("Dry run complete. No database writes were performed.")
        return 0

    detail_count = writer.upsert_event_study_aggregates(aggregates)
    summary_count = writer.upsert_ui_summary_rows(aggregates)
    after_detail_count, after_summary_count = _count_existing(writer)

    LOGGER.info(
        "Event studies updated. Detailed before=%s after=%s delta=%s. Summary before=%s after=%s delta=%s. Upserted detailed=%s summary=%s.",
        before_detail_count,
        after_detail_count,
        after_detail_count - before_detail_count,
        before_summary_count,
        after_summary_count,
        after_summary_count - before_summary_count,
        detail_count,
        summary_count,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
