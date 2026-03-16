from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
import json
import logging
from pathlib import Path
from typing import Any, Iterable, Iterator

import pyarrow.parquet as pq
import psycopg2
from psycopg2.extras import execute_values

from ingestion.write_to_supabase import build_postgres_dsn, load_ingestion_environment

from .price_dataset import collect_study_tickers, resolve_price_dataset_path
from .write_event_studies_to_supabase import EventStudySupabaseWriter


LOGGER = logging.getLogger("research.load_prices_to_supabase")
REPORT_PATH = Path("reports") / "daily_prices_load.json"
REQUIRED_COLUMNS = ("Date", "Ticker", "Close")
OPTIONAL_COLUMNS = ("Open", "High", "Low", "Volume", "Dividends", "Stock Splits")
BATCH_SIZE = 500
COMMIT_BATCHES = 20


@dataclass(frozen=True, slots=True)
class DailyPriceRecord:
    ticker: str
    trade_date: date
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    close: Decimal
    volume: int | None
    dividends: Decimal | None
    stock_splits: Decimal | None

    def to_insert_tuple(self) -> tuple[Any, ...]:
        return (
            self.ticker,
            self.trade_date,
            self.open,
            self.high,
            self.low,
            self.close,
            self.volume,
            self.dividends,
            self.stock_splits,
        )


@dataclass(frozen=True, slots=True)
class LoadSummary:
    price_file: str
    total_rows_read: int
    rows_skipped: int
    rows_upserted: int
    tickers_loaded: tuple[str, ...]
    load_completed_at: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["tickers_loaded"] = list(self.tickers_loaded)
        return payload


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format="%(levelname)s %(message)s")


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Load local daily price history into the Supabase daily_prices table.")
    parser.add_argument("--price-file", default=None, help="Optional explicit parquet/csv path. Defaults to shared resolver order.")
    parser.add_argument("--bootstrap-schema", action="store_true", help="Apply the daily_prices SQL schema before loading.")
    parser.add_argument(
        "--schema-file",
        default=str(repo_root / "supabase" / "sql" / "008_add_daily_prices.sql"),
        help="Path to the daily_prices SQL migration file.",
    )
    parser.add_argument("--ticker", action="append", default=[], help="Optional ticker filter. Can be provided multiple times.")
    parser.add_argument(
        "--study-universe",
        action="store_true",
        help="Load only the current event-study ticker universe from Supabase events and related companies.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Parse and validate rows without writing to Supabase.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")
    return parser.parse_args()


def _normalize_ticker_filter(tickers: Iterable[str]) -> set[str] | None:
    normalized = {ticker.strip().upper() for ticker in tickers if ticker and ticker.strip()}
    return normalized or None


def _resolve_ticker_filter(
    repo_root: Path,
    *,
    ticker_filters: Iterable[str],
    study_universe: bool,
) -> set[str] | None:
    normalized = _normalize_ticker_filter(ticker_filters) or set()
    if study_universe:
        writer = EventStudySupabaseWriter(repo_root)
        events = writer.load_study_events()
        normalized.update(collect_study_tickers(events))
    return normalized or None


def _resolve_path(repo_root: Path, candidate: str | None) -> Path:
    if candidate is None:
        raise ValueError("Expected a path candidate.")
    path = Path(candidate)
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()


def _normalize_trade_date(value: Any) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(str(value))


def _normalize_numeric(value: Any) -> Decimal | None:
    if value in {None, ""}:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid numeric value: {value!r}") from exc


def _normalize_volume(value: Any) -> int | None:
    if value in {None, ""}:
        return None
    return int(float(value))


def _record_from_values(trade_date_value: Any, ticker_value: Any, values: dict[str, Any]) -> DailyPriceRecord | None:
    ticker = str(ticker_value or "").strip().upper()
    if not ticker:
        raise ValueError("Missing ticker")

    close = _normalize_numeric(values["Close"])
    if close is None or close == 0:
        return None

    return DailyPriceRecord(
        ticker=ticker,
        trade_date=_normalize_trade_date(trade_date_value),
        open=_normalize_numeric(values.get("Open")),
        high=_normalize_numeric(values.get("High")),
        low=_normalize_numeric(values.get("Low")),
        close=close,
        volume=_normalize_volume(values.get("Volume")),
        dividends=_normalize_numeric(values.get("Dividends")),
        stock_splits=_normalize_numeric(values.get("Stock Splits")),
    )


def _iter_csv_rows(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(reader.fieldnames or ())
        missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        if missing:
            raise ValueError(f"CSV price file is missing required columns: {', '.join(missing)}")
        for row in reader:
            yield row


def _iter_parquet_rows(path: Path) -> Iterator[dict[str, Any]]:
    parquet_file = pq.ParquetFile(path)
    fieldnames = set(parquet_file.schema_arrow.names)
    missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
    if missing:
        raise ValueError(f"Parquet price file is missing required columns: {', '.join(missing)}")

    requested_columns = list(REQUIRED_COLUMNS) + [column for column in OPTIONAL_COLUMNS if column in fieldnames]
    for batch in parquet_file.iter_batches(batch_size=65536, columns=requested_columns):
        column_map = {name: batch.column(index).to_pylist() for index, name in enumerate(requested_columns)}
        row_count = batch.num_rows
        for row_index in range(row_count):
            yield {name: column_map[name][row_index] for name in requested_columns}


def _iter_source_rows(path: Path) -> Iterator[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        yield from _iter_parquet_rows(path)
        return
    if suffix == ".csv":
        yield from _iter_csv_rows(path)
        return
    raise ValueError(f"Unsupported price file format for {path}. Expected .parquet or .csv.")


def iter_normalized_price_records(path: Path, *, tickers: set[str] | None = None) -> Iterator[DailyPriceRecord | None]:
    for row in _iter_source_rows(path):
        ticker = str(row.get("Ticker") or "").strip().upper()
        if tickers is not None and ticker not in tickers:
            continue
        yield _record_from_values(row.get("Date"), row.get("Ticker"), row)


def _apply_schema(connection: psycopg2.extensions.connection, schema_path: Path) -> None:
    LOGGER.info("Applying daily_prices schema file: %s", schema_path)
    sql_text = schema_path.read_text(encoding="utf-8")
    with connection.cursor() as cursor:
        cursor.execute(sql_text)
    connection.commit()


def _connect(repo_root: Path) -> psycopg2.extensions.connection:
    load_ingestion_environment(repo_root)
    dsn = build_postgres_dsn()
    return psycopg2.connect(dsn)


def _upsert_batch(cursor: psycopg2.extensions.cursor, rows: list[tuple[Any, ...]]) -> None:
    execute_values(
        cursor,
        """
        insert into public.daily_prices (
            ticker,
            trade_date,
            open,
            high,
            low,
            close,
            volume,
            dividends,
            stock_splits
        )
        values %s
        on conflict (ticker, trade_date) do update
        set
            close = excluded.close,
            open = excluded.open,
            high = excluded.high,
            low = excluded.low,
            volume = excluded.volume,
            dividends = excluded.dividends,
            stock_splits = excluded.stock_splits
        """,
        rows,
        page_size=len(rows),
    )


def _write_report(repo_root: Path, summary: LoadSummary) -> None:
    report_path = (repo_root / REPORT_PATH).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summary.to_dict(), indent=2), encoding="utf-8")


def run_load(
    repo_root: Path,
    *,
    price_file: str | None,
    bootstrap_schema: bool,
    schema_file: str,
    ticker_filters: Iterable[str],
    study_universe: bool,
    dry_run: bool,
) -> LoadSummary:
    resolved = resolve_price_dataset_path(repo_root, price_file, allow_sample_fallback=False)
    resolved_path = resolved.path.resolve()
    tickers = _resolve_ticker_filter(repo_root, ticker_filters=ticker_filters, study_universe=study_universe)

    LOGGER.info("Resolved price file: %s", resolved_path)
    if tickers:
        LOGGER.info("Ticker scope contains %s ticker(s)", len(tickers))
    total_rows_read = 0
    rows_skipped = 0
    rows_upserted = 0
    tickers_loaded: set[str] = set()

    connection = None
    cursor = None
    pending_batch: list[tuple[Any, ...]] = []
    batches_since_commit = 0

    try:
        if not dry_run:
            connection = _connect(repo_root)
            cursor = connection.cursor()
            if bootstrap_schema:
                _apply_schema(connection, _resolve_path(repo_root, schema_file))

        for record in iter_normalized_price_records(resolved_path, tickers=tickers):
            total_rows_read += 1
            if record is None:
                rows_skipped += 1
                continue

            tickers_loaded.add(record.ticker)
            if dry_run:
                rows_upserted += 1
                continue

            pending_batch.append(record.to_insert_tuple())
            if len(pending_batch) < BATCH_SIZE:
                continue

            _upsert_batch(cursor, pending_batch)
            rows_upserted += len(pending_batch)
            batches_since_commit += 1
            LOGGER.debug("Upserted batch of %s price row(s)", len(pending_batch))
            pending_batch = []

            if batches_since_commit >= COMMIT_BATCHES:
                connection.commit()
                batches_since_commit = 0

        if not dry_run and pending_batch:
            _upsert_batch(cursor, pending_batch)
            rows_upserted += len(pending_batch)
            LOGGER.debug("Upserted batch of %s price row(s)", len(pending_batch))

        if not dry_run and connection is not None:
            connection.commit()
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

    completed_at = datetime.now(UTC).isoformat()
    summary = LoadSummary(
        price_file=str(resolved_path),
        total_rows_read=total_rows_read,
        rows_skipped=rows_skipped,
        rows_upserted=rows_upserted,
        tickers_loaded=tuple(sorted(tickers_loaded)),
        load_completed_at=completed_at,
    )
    _write_report(repo_root, summary)
    LOGGER.info(
        "Loaded %s price row(s) for %s ticker(s) into daily_prices",
        rows_upserted,
        len(tickers_loaded),
    )
    return summary


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)

    repo_root = Path(__file__).resolve().parent.parent
    summary = run_load(
        repo_root,
        price_file=args.price_file,
        bootstrap_schema=args.bootstrap_schema,
        schema_file=args.schema_file,
        ticker_filters=args.ticker,
        study_universe=args.study_universe,
        dry_run=args.dry_run,
    )
    LOGGER.info(
        "Summary: price_file=%s total_rows_read=%s rows_skipped=%s rows_upserted=%s tickers=%s",
        summary.price_file,
        summary.total_rows_read,
        summary.rows_skipped,
        summary.rows_upserted,
        len(summary.tickers_loaded),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
