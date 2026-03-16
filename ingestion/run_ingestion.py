from __future__ import annotations

import argparse
import logging
from collections import Counter
from pathlib import Path
from typing import Iterable

try:
    from .load_financial_news_file import load_financial_news_file
    from .load_sec_filings_file import load_sec_filings_file
    from .load_source_file import load_source_file
    from .map_financial_news_to_event import FinancialNewsMappingError, map_financial_news_to_event_payload
    from .models import IngestionFailure, IngestionSummary, NormalizedEvent
    from .map_sec_filing_to_event import map_sec_filing_to_event_payload
    from .normalize import ValidationError, normalize_event_record
    from .write_to_supabase import SupabaseWriter
except ImportError:  # pragma: no cover - script execution fallback
    from load_financial_news_file import load_financial_news_file  # type: ignore
    from load_sec_filings_file import load_sec_filings_file  # type: ignore
    from load_source_file import load_source_file  # type: ignore
    from map_financial_news_to_event import FinancialNewsMappingError, map_financial_news_to_event_payload  # type: ignore
    from models import IngestionFailure, IngestionSummary, NormalizedEvent  # type: ignore
    from map_sec_filing_to_event import map_sec_filing_to_event_payload  # type: ignore
    from normalize import ValidationError, normalize_event_record  # type: ignore
    from write_to_supabase import SupabaseWriter  # type: ignore

LOGGER = logging.getLogger("ingestion.run_ingestion")


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent.parent

    parser = argparse.ArgumentParser(description="Normalize and upsert local structured source data into Supabase.")
    parser.add_argument(
        "--source-type",
        choices=["market-events", "sec-filings", "financial-news"],
        default="market-events",
        help="Structured input mode to process.",
    )
    parser.add_argument(
        "--input",
        default=str(Path(__file__).resolve().with_name("sample_input_events.json")),
        help="Path to a JSON file containing structured source event records.",
    )
    parser.add_argument(
        "--bootstrap-schema",
        action="store_true",
        help="Apply supabase/sql/001_create_core_tables.sql before ingestion.",
    )
    parser.add_argument(
        "--schema-file",
        default=str(repo_root / "supabase" / "sql" / "001_create_core_tables.sql"),
        help="SQL file to apply when --bootstrap-schema is set.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Normalize and validate records without writing to Supabase.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )
    return parser.parse_args()


def get_default_input_path(source_type: str) -> str:
    current_dir = Path(__file__).resolve().parent
    if source_type == "sec-filings":
        return str(current_dir / "sample_input_sec_filings.json")
    if source_type == "financial-news":
        return str(current_dir.parent.parent / "data" / "events" / "financialNews" / "financial_news_events.csv")
    return str(current_dir / "sample_input_events.json")


def load_records(source_type: str, input_path: str) -> list[dict]:
    if source_type == "financial-news":
        return load_financial_news_file(input_path)
    if source_type == "sec-filings":
        return load_sec_filings_file(input_path)
    return load_source_file(input_path)


def prepare_record_for_normalization(source_type: str, raw_record: dict, record_index: int) -> dict:
    if source_type == "financial-news":
        return map_financial_news_to_event_payload(raw_record, record_index)
    if source_type == "sec-filings":
        return map_sec_filing_to_event_payload(raw_record)
    return raw_record


def normalize_records_with_diagnostics(
    source_type: str,
    raw_records: Iterable[dict],
    *,
    log_each_record: bool = True,
) -> tuple[list[NormalizedEvent], list[IngestionFailure], list[IngestionFailure]]:
    normalized_records: list[NormalizedEvent] = []
    failures: list[IngestionFailure] = []
    skipped: list[IngestionFailure] = []

    for index, raw_record in enumerate(raw_records, start=1):
        try:
            prepared_record = prepare_record_for_normalization(source_type, raw_record, index)
            normalized = normalize_event_record(prepared_record)
            normalized_records.append(normalized)
            if log_each_record:
                LOGGER.info("Normalized record %s -> %s [%s]", index, normalized.headline, normalized.id)
        except FinancialNewsMappingError as exc:
            skipped.append(IngestionFailure(record_index=index, reason=str(exc)))
            if log_each_record:
                LOGGER.warning("Skipped financial-news record %s: %s", index, exc)
        except ValidationError as exc:
            if source_type == "financial-news":
                skipped.append(IngestionFailure(record_index=index, reason=str(exc)))
                if log_each_record:
                    LOGGER.warning("Skipped financial-news record %s: %s", index, exc)
            else:
                failures.append(IngestionFailure(record_index=index, reason=str(exc)))
                if log_each_record:
                    LOGGER.error("Validation failed for record %s: %s", index, exc)

    return normalized_records, failures, skipped


def normalize_records(source_type: str, raw_records: Iterable[dict]) -> tuple[list[NormalizedEvent], list[IngestionFailure]]:
    normalized_records, failures, _skipped = normalize_records_with_diagnostics(
        source_type,
        raw_records,
        log_each_record=False,
    )
    return normalized_records, failures


def _log_failure_group(label: str, failures: list[IngestionFailure], *, verbose: bool) -> None:
    if not failures:
        return

    if verbose:
        for failure in failures:
            LOGGER.warning("%s record %s: %s", label, failure.record_index, failure.reason)
        return

    grouped_reasons = Counter(failure.reason for failure in failures)
    LOGGER.warning("%s %s record(s) across %s distinct reason(s).", label, len(failures), len(grouped_reasons))
    for reason, count in sorted(grouped_reasons.items(), key=lambda item: (-item[1], item[0])):
        LOGGER.warning("%s summary: %s x%s", label, reason, count)


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)

    repo_root = Path(__file__).resolve().parent.parent
    input_path = args.input
    if input_path == str(Path(__file__).resolve().with_name("sample_input_events.json")) and args.source_type == "sec-filings":
        input_path = get_default_input_path(args.source_type)
    if input_path == str(Path(__file__).resolve().with_name("sample_input_events.json")) and args.source_type == "financial-news":
        input_path = get_default_input_path(args.source_type)

    raw_records = load_records(args.source_type, input_path)
    normalized_records, failures, skipped = normalize_records_with_diagnostics(
        args.source_type,
        raw_records,
        log_each_record=args.verbose,
    )

    summary = IngestionSummary(
        input_records=len(raw_records),
        normalized_records=len(normalized_records),
        failed_records=len(failures),
        skipped_records=len(skipped),
    )

    writer = SupabaseWriter(repo_root)

    if args.bootstrap_schema:
        writer.apply_sql_file(Path(args.schema_file))

    if args.dry_run:
        LOGGER.info("Dry run complete. No database writes were performed.")
    else:
        summary.write_summary = writer.upsert_events(normalized_records)
        live_event_count = writer.count_matching_events(normalized_records)
        LOGGER.info("Verified %s matching live event row(s) in Supabase after upsert.", live_event_count)

    LOGGER.info(
        "Ingestion summary: input=%s normalized=%s skipped=%s failed=%s events_upserted=%s related_companies_upserted=%s research_insights_upserted=%s",
        summary.input_records,
        summary.normalized_records,
        summary.skipped_records,
        summary.failed_records,
        summary.write_summary.events_upserted,
        summary.write_summary.related_companies_upserted,
        summary.write_summary.research_insights_upserted,
    )

    _log_failure_group("Skipped", skipped, verbose=args.verbose)
    _log_failure_group("Failed normalization for", failures, verbose=args.verbose)

    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
