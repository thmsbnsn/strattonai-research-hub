from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
import json
import logging
from pathlib import Path
from time import sleep
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

import pyarrow as pa
import pyarrow.parquet as pq

from ingestion.load_price_series_file import inspect_price_series_file, load_price_series_file

from .massive_config import MassiveConfig, load_massive_config
from .price_dataset import collect_study_tickers, resolve_price_dataset_path
from .write_event_studies_to_supabase import EventStudySupabaseWriter


LOGGER = logging.getLogger("research.massive_price_backfill")
CSV_HEADER = ["Date", "Ticker", "Open", "High", "Low", "Close", "Volume", "Dividends", "Stock Splits"]
TICKER_ALIASES: dict[str, list[str]] = {
    "TTM": ["TTM", "NYSE:TTM"],
}


@dataclass(frozen=True, slots=True)
class HistoricalPriceRow:
    trade_date: str
    ticker: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    dividends: float = 0.0
    stock_splits: float = 0.0

    @property
    def key(self) -> tuple[str, str]:
        return self.trade_date, self.ticker

    def to_csv_row(self) -> dict[str, Any]:
        return {
            "Date": self.trade_date,
            "Ticker": self.ticker,
            "Open": self.open,
            "High": self.high,
            "Low": self.low,
            "Close": self.close,
            "Volume": self.volume,
            "Dividends": self.dividends,
            "Stock Splits": self.stock_splits,
        }


@dataclass(frozen=True, slots=True)
class MassiveBackfillReport:
    base_parquet_path: str
    base_csv_path: str
    extended_parquet_path: str
    extended_csv_path: str
    backfill_parquet_path: str
    backfill_csv_path: str
    previous_price_max_date: str
    new_price_max_date: str
    requested_tickers: tuple[str, ...]
    tickers_with_new_rows: tuple[str, ...]
    tickers_without_results: tuple[str, ...]
    fetched_row_count: int
    backfill_row_count: int
    covered_ticker_count: int
    uncovered_tickers_after_merge: tuple[str, ...]
    target_start_date: str
    target_end_date: str
    config_summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format="%(levelname)s %(message)s")


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Fetch deterministic historical price backfill data from Massive and build local extended datasets.")
    parser.add_argument(
        "--start-date",
        default=None,
        help="Optional explicit backfill start date (YYYY-MM-DD). Defaults to the day after the base dataset max date.",
    )
    parser.add_argument(
        "--end-date",
        default=None,
        help="Optional explicit backfill end date (YYYY-MM-DD). Defaults to max event date plus a 45-day forward-return buffer.",
    )
    parser.add_argument(
        "--ticker",
        action="append",
        default=[],
        help="Optional ticker override. Can be passed multiple times.",
    )
    parser.add_argument(
        "--json-output",
        default=str(repo_root / "reports" / "massive_price_backfill.json"),
        help="JSON output path for the backfill report.",
    )
    parser.add_argument(
        "--markdown-output",
        default=str(repo_root / "reports" / "massive_price_backfill.md"),
        help="Markdown output path for the backfill report.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Fetch and report without writing local files.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")
    return parser.parse_args()


def _resolve_base_paths(repo_root: Path) -> tuple[Path, Path]:
    base_parquet = resolve_price_dataset_path(repo_root, "data/prices/all_stock_data.parquet", allow_sample_fallback=False).path
    base_csv = resolve_price_dataset_path(repo_root, "data/prices/all_stock_data.csv", allow_sample_fallback=False).path
    return base_parquet, base_csv


def _determine_target_tickers(repo_root: Path, ticker_overrides: list[str]) -> list[str]:
    if ticker_overrides:
        return sorted({ticker.strip().upper() for ticker in ticker_overrides if ticker.strip()})

    writer = EventStudySupabaseWriter(repo_root)
    events = writer.load_study_events()
    return sorted(collect_study_tickers(events))


def _determine_end_date(repo_root: Path, explicit_end_date: str | None) -> date:
    if explicit_end_date:
        return date.fromisoformat(explicit_end_date)

    writer = EventStudySupabaseWriter(repo_root)
    events = writer.load_study_events()
    max_event_date = max(event.timestamp.date() for event in events)
    return max_event_date + timedelta(days=45)


def _load_existing_backfill_rows(path: Path) -> list[HistoricalPriceRow]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [
            HistoricalPriceRow(
                trade_date=row["Date"],
                ticker=row["Ticker"],
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row["Volume"]),
                dividends=float(row["Dividends"]),
                stock_splits=float(row["Stock Splits"]),
            )
            for row in reader
        ]


def _merge_backfill_rows(existing_rows: list[HistoricalPriceRow], fetched_rows: list[HistoricalPriceRow]) -> list[HistoricalPriceRow]:
    merged = {row.key: row for row in existing_rows}
    for row in fetched_rows:
        merged[row.key] = row
    return sorted(merged.values(), key=lambda row: (row.trade_date, row.ticker))


def _fetch_massive_rows(
    config: MassiveConfig,
    ticker: str,
    start_date: date,
    end_date: date,
    *,
    max_retries: int = 8,
    retry_sleep_seconds: float = 5.0,
) -> list[HistoricalPriceRow]:
    alias_candidates = TICKER_ALIASES.get(ticker, [ticker])
    symbols = tuple(dict.fromkeys([ticker, *alias_candidates]))

    for symbol in symbols:
        rows = _fetch_massive_rows_for_symbol(
            config,
            requested_ticker=ticker,
            lookup_symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            max_retries=max_retries,
            retry_sleep_seconds=retry_sleep_seconds,
        )
        if rows:
            if symbol != ticker:
                LOGGER.info("Massive alias fallback succeeded for %s using %s", ticker, symbol)
            return rows
    return []


def _fetch_massive_rows_for_symbol(
    config: MassiveConfig,
    *,
    requested_ticker: str,
    lookup_symbol: str,
    start_date: date,
    end_date: date,
    max_retries: int,
    retry_sleep_seconds: float,
) -> list[HistoricalPriceRow]:
    params = urlencode(
        {
            "adjusted": "true",
            "sort": "asc",
            "limit": "50000",
            "apiKey": config.api_key,
        }
    )
    encoded_symbol = quote(lookup_symbol, safe="")
    url = f"{config.base_url}/v2/aggs/ticker/{encoded_symbol}/range/1/day/{start_date.isoformat()}/{end_date.isoformat()}?{params}"
    request = Request(url, headers={"User-Agent": "StrattonAI/1.0"})

    for attempt in range(1, max_retries + 1):
        try:
            with urlopen(request, timeout=60) as response:
                payload = json.loads(response.read().decode("utf-8"))
            results = payload.get("results", [])
            rows = [
                HistoricalPriceRow(
                    trade_date=datetime.fromtimestamp(result["t"] / 1000, tz=UTC).date().isoformat(),
                    ticker=requested_ticker,
                    open=float(result.get("o", 0.0)),
                    high=float(result.get("h", 0.0)),
                    low=float(result.get("l", 0.0)),
                    close=float(result.get("c", 0.0)),
                    volume=float(result.get("v", 0.0)),
                )
                for result in results
            ]
            LOGGER.info("Fetched %s day aggregate row(s) for %s via %s", len(rows), requested_ticker, lookup_symbol)
            return rows
        except HTTPError as exc:
            if exc.code == 429 and attempt < max_retries:
                retry_after_header = exc.headers.get("Retry-After") if exc.headers else None
                retry_after_seconds = 0.0
                if retry_after_header:
                    try:
                        retry_after_seconds = float(retry_after_header)
                    except ValueError:
                        retry_after_seconds = 0.0
                wait_seconds = max(retry_sleep_seconds * attempt, retry_after_seconds)
                LOGGER.warning(
                    "Massive rate limit for %s on attempt %s/%s. Retrying in %.1f seconds.",
                    lookup_symbol,
                    attempt,
                    max_retries,
                    wait_seconds,
                )
                sleep(wait_seconds)
                continue
            if exc.code == 429:
                LOGGER.error(
                    "Massive rate limit persisted for %s after %s attempts. Marking ticker as uncovered.",
                    lookup_symbol,
                    max_retries,
                )
                return []
            if exc.code == 404:
                LOGGER.warning("Massive returned 404 for %s. Treating as uncovered.", lookup_symbol)
                return []
            raise
        except URLError as exc:
            if attempt < max_retries:
                LOGGER.warning("Massive network error for %s on attempt %s/%s: %s", lookup_symbol, attempt, max_retries, exc)
                sleep(retry_sleep_seconds * attempt)
                continue
            LOGGER.error(
                "Massive network error persisted for %s after %s attempts. Marking ticker as uncovered.",
                lookup_symbol,
                max_retries,
            )
            return []
    return []


def _write_backfill_csv(rows: list[HistoricalPriceRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_HEADER)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.to_csv_row())


def _rows_to_arrow_table(rows: list[HistoricalPriceRow]) -> pa.Table:
    return pa.table(
        {
            "Date": [date.fromisoformat(row.trade_date) for row in rows],
            "Ticker": [row.ticker for row in rows],
            "Open": [row.open for row in rows],
            "High": [row.high for row in rows],
            "Low": [row.low for row in rows],
            "Close": [row.close for row in rows],
            "Volume": [row.volume for row in rows],
            "Dividends": [row.dividends for row in rows],
            "Stock Splits": [row.stock_splits for row in rows],
        }
    )


def _write_backfill_parquet(rows: list[HistoricalPriceRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    table = _rows_to_arrow_table(rows)
    pq.write_table(table, path, compression="snappy")


def _rebuild_extended_csv(base_csv_path: Path, backfill_rows: list[HistoricalPriceRow], extended_csv_path: Path) -> None:
    extended_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with base_csv_path.open("rb") as source_handle, extended_csv_path.open("wb") as target_handle:
        while True:
            chunk = source_handle.read(1024 * 1024)
            if not chunk:
                break
            target_handle.write(chunk)

    if not backfill_rows:
        return

    with extended_csv_path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_HEADER)
        for row in backfill_rows:
            writer.writerow(row.to_csv_row())


def _rebuild_extended_parquet(base_parquet_path: Path, backfill_rows: list[HistoricalPriceRow], extended_parquet_path: Path) -> None:
    parquet_file = pq.ParquetFile(base_parquet_path)
    schema = parquet_file.schema_arrow
    extended_parquet_path.parent.mkdir(parents=True, exist_ok=True)

    with pq.ParquetWriter(extended_parquet_path, schema, compression="snappy") as writer:
        for batch in parquet_file.iter_batches(batch_size=65536):
            writer.write_table(pa.Table.from_batches([batch], schema=schema))
        if backfill_rows:
            writer.write_table(_rows_to_arrow_table(backfill_rows).cast(schema))


def build_markdown_report(report: MassiveBackfillReport) -> str:
    lines = [
        "# Massive Price Backfill",
        "",
        f"- Previous price max date: {report.previous_price_max_date}",
        f"- New price max date: {report.new_price_max_date}",
        f"- Requested tickers: {', '.join(report.requested_tickers)}",
        f"- Tickers with new rows: {', '.join(report.tickers_with_new_rows) or 'None'}",
        f"- Tickers without results: {', '.join(report.tickers_without_results) or 'None'}",
        f"- Fetched rows: {report.fetched_row_count}",
        f"- Backfill rows after merge: {report.backfill_row_count}",
        f"- Covered tickers after merge: {report.covered_ticker_count}",
        f"- Uncovered tickers after merge: {', '.join(report.uncovered_tickers_after_merge) or 'None'}",
        "",
        "## Local Outputs",
        f"- Backfill CSV: `{report.backfill_csv_path}`",
        f"- Backfill Parquet: `{report.backfill_parquet_path}`",
        f"- Extended CSV: `{report.extended_csv_path}`",
        f"- Extended Parquet: `{report.extended_parquet_path}`",
    ]
    return "\n".join(lines) + "\n"


def run_massive_price_backfill(
    repo_root: Path,
    *,
    start_date: str | None,
    end_date: str | None,
    ticker_overrides: list[str],
    dry_run: bool,
) -> MassiveBackfillReport:
    config = load_massive_config(repo_root)
    base_parquet_path, base_csv_path = _resolve_base_paths(repo_root)
    base_inspection = inspect_price_series_file(base_parquet_path)
    previous_max_date = date.fromisoformat(base_inspection.max_date or "1900-01-01")

    resolved_start_date = date.fromisoformat(start_date) if start_date else previous_max_date + timedelta(days=1)
    if resolved_start_date <= previous_max_date:
        raise ValueError(
            f"Backfill start date {resolved_start_date.isoformat()} must be after current base max date {previous_max_date.isoformat()}."
        )

    resolved_end_date = _determine_end_date(repo_root, end_date)
    requested_tickers = _determine_target_tickers(repo_root, ticker_overrides)

    fetched_rows: list[HistoricalPriceRow] = []
    tickers_with_new_rows: list[str] = []
    tickers_without_results: list[str] = []
    for ticker in requested_tickers:
        rows = _fetch_massive_rows(config, ticker, resolved_start_date, resolved_end_date)
        if rows:
            fetched_rows.extend(rows)
            tickers_with_new_rows.append(ticker)
        else:
            tickers_without_results.append(ticker)
        sleep(1.5)

    backfill_dir = base_parquet_path.parent / "backfills"
    backfill_csv_path = backfill_dir / "massive_daily_backfill.csv"
    backfill_parquet_path = backfill_dir / "massive_daily_backfill.parquet"
    existing_backfill_rows = _load_existing_backfill_rows(backfill_csv_path)
    merged_backfill_rows = _merge_backfill_rows(existing_backfill_rows, fetched_rows)

    extended_parquet_path = base_parquet_path.with_name("all_stock_data_extended.parquet")
    extended_csv_path = base_csv_path.with_name("all_stock_data_extended.csv")

    if not dry_run:
        _write_backfill_csv(merged_backfill_rows, backfill_csv_path)
        _write_backfill_parquet(merged_backfill_rows, backfill_parquet_path)
        _rebuild_extended_csv(base_csv_path, merged_backfill_rows, extended_csv_path)
        _rebuild_extended_parquet(base_parquet_path, merged_backfill_rows, extended_parquet_path)

    coverage_path = extended_parquet_path if not dry_run else base_parquet_path
    covered_series = load_price_series_file(coverage_path, tickers=requested_tickers)
    covered_tickers = {series.ticker for series in covered_series}
    new_max_date = (
        max((series.prices[-1].date.isoformat() for series in covered_series if series.prices), default=previous_max_date.isoformat())
        if covered_series
        else previous_max_date.isoformat()
    )

    return MassiveBackfillReport(
        base_parquet_path=str(base_parquet_path),
        base_csv_path=str(base_csv_path),
        extended_parquet_path=str(extended_parquet_path),
        extended_csv_path=str(extended_csv_path),
        backfill_parquet_path=str(backfill_parquet_path),
        backfill_csv_path=str(backfill_csv_path),
        previous_price_max_date=previous_max_date.isoformat(),
        new_price_max_date=new_max_date,
        requested_tickers=tuple(requested_tickers),
        tickers_with_new_rows=tuple(sorted(tickers_with_new_rows)),
        tickers_without_results=tuple(sorted(tickers_without_results)),
        fetched_row_count=len(fetched_rows),
        backfill_row_count=len(merged_backfill_rows),
        covered_ticker_count=len(covered_tickers),
        uncovered_tickers_after_merge=tuple(sorted(set(requested_tickers) - covered_tickers)),
        target_start_date=resolved_start_date.isoformat(),
        target_end_date=resolved_end_date.isoformat(),
        config_summary=config.safe_summary(),
    )


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)

    repo_root = Path(__file__).resolve().parent.parent
    report = run_massive_price_backfill(
        repo_root,
        start_date=args.start_date,
        end_date=args.end_date,
        ticker_overrides=args.ticker,
        dry_run=args.dry_run,
    )

    json_output = Path(args.json_output)
    markdown_output = Path(args.markdown_output)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    markdown_output.write_text(build_markdown_report(report), encoding="utf-8")
    LOGGER.info(
        "Massive backfill complete. previous_max=%s new_max=%s fetched_rows=%s covered_tickers=%s uncovered=%s",
        report.previous_price_max_date,
        report.new_price_max_date,
        report.fetched_row_count,
        report.covered_ticker_count,
        list(report.uncovered_tickers_after_merge),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
