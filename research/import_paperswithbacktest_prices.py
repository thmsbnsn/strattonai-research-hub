from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
import json
import logging
from pathlib import Path
import shutil
import tempfile
from typing import Any, Iterable, Iterator

import pyarrow as pa
import pyarrow.dataset as pa_dataset
import pyarrow.parquet as pq

from ingestion.load_price_series_file import inspect_price_series_file, load_price_series_file

from .price_dataset import collect_study_tickers, resolve_price_dataset_path
from .write_event_studies_to_supabase import EventStudySupabaseWriter


LOGGER = logging.getLogger("research.import_paperswithbacktest_prices")
CSV_HEADER = ["Date", "Ticker", "Open", "High", "Low", "Close", "Volume", "Dividends", "Stock Splits"]


@dataclass(frozen=True, slots=True)
class ImportedPriceRow:
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
class PapersWithBacktestImportReport:
    source_directory: str
    base_price_path: str
    base_price_format: str
    enriched_parquet_path: str
    enriched_csv_path: str | None
    backfill_parquet_path: str
    backfill_csv_path: str
    target_tickers: tuple[str, ...]
    tickers_with_new_rows: tuple[str, ...]
    tickers_without_source_rows: tuple[str, ...]
    source_rows_matched: int
    new_rows_added: int
    cumulative_backfill_rows: int
    covered_ticker_count_after_merge: int
    previous_price_max_date: str
    new_price_max_date: str
    import_completed_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format="%(levelname)s %(message)s")


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description="Import Papers With Backtest daily stock prices into StrattonAI's enriched local price dataset."
    )
    parser.add_argument(
        "--source-dir",
        default=str(repo_root.parent / "data" / "DoWeLikeThis" / "StocksDailyPrice-PapersWithBacktest"),
        help="Directory containing the train-*.parquet shards from the Papers With Backtest stock dataset.",
    )
    parser.add_argument(
        "--price-file",
        default=None,
        help="Optional explicit base price dataset override. Defaults to the shared resolver order.",
    )
    parser.add_argument(
        "--ticker",
        action="append",
        default=[],
        help="Optional ticker override. Can be provided multiple times. Defaults to the current study universe.",
    )
    parser.add_argument(
        "--json-output",
        default=str(repo_root / "reports" / "paperswithbacktest_price_import.json"),
        help="JSON output path for the import report.",
    )
    parser.add_argument(
        "--markdown-output",
        default=str(repo_root / "reports" / "paperswithbacktest_price_import.md"),
        help="Markdown output path for the import report.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing local files.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")
    return parser.parse_args()


def _normalize_tickers(tickers: Iterable[str]) -> list[str]:
    return sorted({ticker.strip().upper() for ticker in tickers if ticker and ticker.strip()})


def _determine_target_tickers(repo_root: Path, ticker_overrides: list[str]) -> list[str]:
    normalized = _normalize_tickers(ticker_overrides)
    if normalized:
        return normalized

    writer = EventStudySupabaseWriter(repo_root)
    events = writer.load_study_events()
    return sorted(collect_study_tickers(events))


def _iter_pwb_rows(source_dir: Path, tickers: set[str]) -> Iterator[ImportedPriceRow]:
    shard_paths = sorted(source_dir.glob("train-*.parquet"))
    if not shard_paths:
        raise FileNotFoundError(f"No Papers With Backtest parquet shards were found in {source_dir}.")

    dataset = pa_dataset.dataset([str(path) for path in shard_paths], format="parquet")
    scanner = dataset.scanner(
        columns=["symbol", "date", "open", "high", "low", "close", "volume"],
        filter=pa_dataset.field("symbol").isin(sorted(tickers)),
        batch_size=65536,
    )
    for batch in scanner.to_batches():
        symbol_values = batch.column(0).to_pylist()
        date_values = batch.column(1).to_pylist()
        open_values = batch.column(2).to_pylist()
        high_values = batch.column(3).to_pylist()
        low_values = batch.column(4).to_pylist()
        close_values = batch.column(5).to_pylist()
        volume_values = batch.column(6).to_pylist()

        for symbol, trade_date, open_value, high_value, low_value, close_value, volume_value in zip(
            symbol_values,
            date_values,
            open_values,
            high_values,
            low_values,
            close_values,
            volume_values,
            strict=True,
        ):
            if close_value in {None, 0, 0.0}:
                continue
            yield ImportedPriceRow(
                trade_date=str(trade_date),
                ticker=str(symbol).strip().upper(),
                open=float(open_value or 0.0),
                high=float(high_value or 0.0),
                low=float(low_value or 0.0),
                close=float(close_value),
                volume=float(volume_value or 0.0),
            )


def _existing_price_keys(path: Path, tickers: set[str]) -> tuple[set[tuple[str, str]], str]:
    series = load_price_series_file(path, tickers=tickers)
    keys = {
        (point.date.isoformat(), series_item.ticker)
        for series_item in series
        for point in series_item.prices
    }
    max_date = max((point.date.isoformat() for series_item in series for point in series_item.prices), default="")
    return keys, max_date


def _load_existing_backfill_rows(path: Path) -> list[ImportedPriceRow]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [
            ImportedPriceRow(
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


def _merge_backfill_rows(existing_rows: list[ImportedPriceRow], new_rows: list[ImportedPriceRow]) -> list[ImportedPriceRow]:
    merged = {row.key: row for row in existing_rows}
    for row in new_rows:
        merged[row.key] = row
    return sorted(merged.values(), key=lambda row: (row.trade_date, row.ticker))


def _write_rows_csv(rows: list[ImportedPriceRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_HEADER)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.to_csv_row())


def _rows_to_arrow_table(rows: list[ImportedPriceRow]) -> pa.Table:
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


def _write_rows_parquet(rows: list[ImportedPriceRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(_rows_to_arrow_table(rows), path, compression="snappy")


def _copy_with_new_rows_csv(base_csv_path: Path, output_csv_path: Path, new_rows: list[ImportedPriceRow]) -> None:
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    if base_csv_path.resolve() == output_csv_path.resolve():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_handle:
            temp_path = Path(temp_handle.name)
        shutil.copyfile(base_csv_path, temp_path)
        if new_rows:
            with temp_path.open("a", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=CSV_HEADER)
                for row in new_rows:
                    writer.writerow(row.to_csv_row())
        shutil.move(temp_path, output_csv_path)
        return

    shutil.copyfile(base_csv_path, output_csv_path)
    if new_rows:
        with output_csv_path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_HEADER)
            for row in new_rows:
                writer.writerow(row.to_csv_row())


def _copy_with_new_rows_parquet(base_parquet_path: Path, output_parquet_path: Path, new_rows: list[ImportedPriceRow]) -> None:
    parquet_file = pq.ParquetFile(base_parquet_path)
    schema = parquet_file.schema_arrow
    output_parquet_path.parent.mkdir(parents=True, exist_ok=True)

    if base_parquet_path.resolve() == output_parquet_path.resolve():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".parquet") as temp_handle:
            temp_path = Path(temp_handle.name)
        target_path = temp_path
    else:
        target_path = output_parquet_path

    with pq.ParquetWriter(target_path, schema, compression="snappy") as writer:
        for batch in parquet_file.iter_batches(batch_size=65536):
            writer.write_table(pa.Table.from_batches([batch], schema=schema))
        if new_rows:
            writer.write_table(_rows_to_arrow_table(new_rows).cast(schema))

    if target_path != output_parquet_path:
        shutil.move(target_path, output_parquet_path)


def build_markdown_report(report: PapersWithBacktestImportReport) -> str:
    lines = [
        "# Papers With Backtest Price Import",
        "",
        f"- Source directory: `{report.source_directory}`",
        f"- Base price dataset: `{report.base_price_path}` ({report.base_price_format})",
        f"- Previous price max date: {report.previous_price_max_date}",
        f"- New price max date: {report.new_price_max_date}",
        f"- Target tickers: {', '.join(report.target_tickers)}",
        f"- Tickers with new rows: {', '.join(report.tickers_with_new_rows) or 'None'}",
        f"- Tickers without source rows: {', '.join(report.tickers_without_source_rows) or 'None'}",
        f"- Source rows matched: {report.source_rows_matched}",
        f"- New rows added: {report.new_rows_added}",
        f"- Cumulative imported backfill rows: {report.cumulative_backfill_rows}",
        f"- Covered tickers after merge: {report.covered_ticker_count_after_merge}",
        "",
        "## Local Outputs",
        f"- Backfill CSV: `{report.backfill_csv_path}`",
        f"- Backfill Parquet: `{report.backfill_parquet_path}`",
        f"- Enriched Parquet: `{report.enriched_parquet_path}`",
    ]
    if report.enriched_csv_path:
        lines.append(f"- Enriched CSV: `{report.enriched_csv_path}`")
    return "\n".join(lines) + "\n"


def run_import(
    repo_root: Path,
    *,
    source_dir: str,
    price_file: str | None,
    ticker_overrides: list[str],
    dry_run: bool,
) -> PapersWithBacktestImportReport:
    source_directory = Path(source_dir).resolve()
    resolved_base = resolve_price_dataset_path(repo_root, price_file, allow_sample_fallback=False)
    base_price_path = resolved_base.path.resolve()
    target_tickers = _determine_target_tickers(repo_root, ticker_overrides)
    target_ticker_set = set(target_tickers)

    existing_keys, previous_max_date = _existing_price_keys(base_price_path, target_ticker_set)
    matched_rows: list[ImportedPriceRow] = []
    tickers_seen_in_source: set[str] = set()
    new_rows: list[ImportedPriceRow] = []

    for row in _iter_pwb_rows(source_directory, target_ticker_set):
        matched_rows.append(row)
        tickers_seen_in_source.add(row.ticker)
        if row.key in existing_keys:
            continue
        existing_keys.add(row.key)
        new_rows.append(row)

    tickers_without_source_rows = sorted(target_ticker_set - tickers_seen_in_source)
    tickers_with_new_rows = sorted({row.ticker for row in new_rows})

    prices_dir = base_price_path.parent
    backfill_dir = prices_dir / "backfills"
    backfill_csv_path = backfill_dir / "paperswithbacktest_daily_backfill.csv"
    backfill_parquet_path = backfill_dir / "paperswithbacktest_daily_backfill.parquet"
    enriched_parquet_path = prices_dir / "all_stock_data_extended_enriched.parquet"
    base_csv_candidate = base_price_path.with_suffix(".csv")
    enriched_csv_path = prices_dir / "all_stock_data_extended_enriched.csv" if base_csv_candidate.exists() else None

    cumulative_backfill_rows = _merge_backfill_rows(_load_existing_backfill_rows(backfill_csv_path), new_rows)

    if not dry_run:
        _write_rows_csv(cumulative_backfill_rows, backfill_csv_path)
        _write_rows_parquet(cumulative_backfill_rows, backfill_parquet_path)
        _copy_with_new_rows_parquet(base_price_path, enriched_parquet_path, new_rows)
        if enriched_csv_path is not None:
            _copy_with_new_rows_csv(base_csv_candidate, enriched_csv_path, new_rows)

    coverage_path = enriched_parquet_path if not dry_run else base_price_path
    coverage_inspection = inspect_price_series_file(coverage_path, tickers=target_tickers)

    return PapersWithBacktestImportReport(
        source_directory=str(source_directory),
        base_price_path=str(base_price_path),
        base_price_format=resolved_base.format,
        enriched_parquet_path=str(enriched_parquet_path),
        enriched_csv_path=str(enriched_csv_path) if enriched_csv_path else None,
        backfill_parquet_path=str(backfill_parquet_path),
        backfill_csv_path=str(backfill_csv_path),
        target_tickers=tuple(target_tickers),
        tickers_with_new_rows=tuple(tickers_with_new_rows),
        tickers_without_source_rows=tuple(tickers_without_source_rows),
        source_rows_matched=len(matched_rows),
        new_rows_added=len(new_rows),
        cumulative_backfill_rows=len(cumulative_backfill_rows),
        covered_ticker_count_after_merge=coverage_inspection.distinct_ticker_count,
        previous_price_max_date=previous_max_date,
        new_price_max_date=coverage_inspection.max_date or previous_max_date,
        import_completed_at=datetime.now(UTC).isoformat(),
    )


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)

    repo_root = Path(__file__).resolve().parent.parent
    report = run_import(
        repo_root,
        source_dir=args.source_dir,
        price_file=args.price_file,
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
        "Papers With Backtest import complete. base=%s matched=%s added=%s covered=%s missing=%s",
        report.base_price_path,
        report.source_rows_matched,
        report.new_rows_added,
        report.covered_ticker_count_after_merge,
        list(report.tickers_without_source_rows),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
