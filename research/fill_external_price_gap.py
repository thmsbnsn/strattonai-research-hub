from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
import gzip
import io
import json
import logging
from pathlib import Path
import shutil
import tempfile
from typing import Any, Callable, Iterable, Iterator
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pyarrow as pa
import pyarrow.parquet as pq

from ingestion.load_price_series_file import inspect_price_series_file, load_price_series_file

from .load_prices_to_supabase import run_load
from .massive_config import MassiveConfig, load_massive_config
from .massive_price_backfill import HistoricalPriceRow, _fetch_massive_rows
from .price_dataset import collect_study_tickers, resolve_price_dataset_path
from .write_event_studies_to_supabase import EventStudySupabaseWriter

try:
    import boto3
    from botocore.config import Config as BotoConfig
    from botocore.exceptions import ClientError
except ImportError:  # pragma: no cover - optional dependency path
    boto3 = None
    BotoConfig = None
    ClientError = Exception


LOGGER = logging.getLogger("research.fill_external_price_gap")
CSV_HEADER = ["Date", "Ticker", "Open", "High", "Low", "Close", "Volume", "Dividends", "Stock Splits"]
FORWARD_RETURN_BUFFER_DAYS = 45


@dataclass(frozen=True, slots=True)
class ProviderAttempt:
    provider: str
    status: str
    row_count: int
    message: str
    first_date: str | None = None
    last_date: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class TickerGapFillResult:
    ticker: str
    start_date: str
    end_date: str
    selected_provider: str | None
    rows_found: int
    rows_added: int
    attempts: tuple[ProviderAttempt, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticker": self.ticker,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "selected_provider": self.selected_provider,
            "rows_found": self.rows_found,
            "rows_added": self.rows_added,
            "attempts": [attempt.to_dict() for attempt in self.attempts],
        }


@dataclass(frozen=True, slots=True)
class ExternalPriceGapFillReport:
    base_price_path: str
    base_price_format: str
    enriched_parquet_path: str | None
    enriched_csv_path: str | None
    backfill_parquet_path: str
    backfill_csv_path: str
    target_tickers: tuple[str, ...]
    tickers_filled: tuple[str, ...]
    tickers_unresolved: tuple[str, ...]
    total_rows_added: int
    cumulative_backfill_rows: int
    previous_price_max_date: str
    new_price_max_date: str
    supabase_rows_upserted: int
    results: tuple[TickerGapFillResult, ...]
    completed_at: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["results"] = [result.to_dict() for result in self.results]
        return payload


ProviderFetcher = Callable[[Path, str, date, date], tuple[list[HistoricalPriceRow], ProviderAttempt]]


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format="%(levelname)s %(message)s")
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description="Fill uncovered study-universe price gaps from configured external providers and merge them into StrattonAI's enriched local dataset."
    )
    parser.add_argument("--price-file", default=None, help="Optional explicit base price dataset override.")
    parser.add_argument("--ticker", action="append", default=[], help="Optional ticker override. Defaults to uncovered study tickers.")
    parser.add_argument("--load-supabase", action="store_true", help="Load the merged enriched dataset into daily_prices after a successful fill.")
    parser.add_argument(
        "--bootstrap-daily-prices-schema",
        action="store_true",
        help="Apply the daily_prices schema before loading Supabase when --load-supabase is set.",
    )
    parser.add_argument(
        "--json-output",
        default=str(repo_root / "reports" / "external_price_gap_fill.json"),
        help="JSON output path for the fill report.",
    )
    parser.add_argument(
        "--markdown-output",
        default=str(repo_root / "reports" / "external_price_gap_fill.md"),
        help="Markdown output path for the fill report.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report provider coverage without writing local files.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")
    return parser.parse_args()


def _load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("//") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _normalize_tickers(tickers: Iterable[str]) -> list[str]:
    return sorted({ticker.strip().upper() for ticker in tickers if ticker and ticker.strip()})


def _load_study_events(repo_root: Path):
    writer = EventStudySupabaseWriter(repo_root)
    return writer.load_study_events()


def _determine_target_tickers(repo_root: Path, base_price_path: Path, ticker_overrides: list[str]) -> list[str]:
    normalized = _normalize_tickers(ticker_overrides)
    if normalized:
        return normalized

    events = _load_study_events(repo_root)
    study_tickers = collect_study_tickers(events)
    covered_tickers = {series.ticker for series in load_price_series_file(base_price_path, tickers=study_tickers)}
    return sorted(study_tickers - covered_tickers)


def _determine_event_ranges(repo_root: Path, tickers: Iterable[str]) -> dict[str, tuple[date, date]]:
    tickers_set = set(tickers)
    if not tickers_set:
        return {}

    events = _load_study_events(repo_root)
    ranges: dict[str, tuple[date, date]] = {}
    for event in events:
        if event.ticker not in tickers_set:
            continue
        event_date = event.timestamp.date()
        current = ranges.get(event.ticker)
        if current is None:
            ranges[event.ticker] = (event_date, event_date + timedelta(days=FORWARD_RETURN_BUFFER_DAYS))
            continue
        ranges[event.ticker] = (
            min(current[0], event_date),
            max(current[1], event_date + timedelta(days=FORWARD_RETURN_BUFFER_DAYS)),
        )
    return ranges


def _existing_price_keys(path: Path, tickers: set[str]) -> tuple[set[tuple[str, str]], str]:
    series = load_price_series_file(path, tickers=tickers)
    keys = {
        (point.date.isoformat(), series_item.ticker)
        for series_item in series
        for point in series_item.prices
    }
    max_date = max((point.date.isoformat() for series_item in series for point in series_item.prices), default="")
    return keys, max_date


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


def _merge_backfill_rows(existing_rows: list[HistoricalPriceRow], new_rows: list[HistoricalPriceRow]) -> list[HistoricalPriceRow]:
    merged = {row.key: row for row in existing_rows}
    for row in new_rows:
        merged[row.key] = row
    return sorted(merged.values(), key=lambda row: (row.trade_date, row.ticker))


def _write_rows_csv(rows: list[HistoricalPriceRow], path: Path) -> None:
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


def _write_rows_parquet(rows: list[HistoricalPriceRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(_rows_to_arrow_table(rows), path, compression="snappy")


def _copy_with_new_rows_csv(base_csv_path: Path, output_csv_path: Path, new_rows: list[HistoricalPriceRow]) -> None:
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


def _copy_with_new_rows_parquet(base_parquet_path: Path, output_parquet_path: Path, new_rows: list[HistoricalPriceRow]) -> None:
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


def _select_column(fieldnames: Iterable[str], *candidates: str) -> str | None:
    normalized = {field.lower(): field for field in fieldnames}
    for candidate in candidates:
        field = normalized.get(candidate.lower())
        if field is not None:
            return field
    return None


def _attempt_summary(provider: str, status: str, message: str, rows: list[HistoricalPriceRow]) -> ProviderAttempt:
    return ProviderAttempt(
        provider=provider,
        status=status,
        row_count=len(rows),
        message=message,
        first_date=rows[0].trade_date if rows else None,
        last_date=rows[-1].trade_date if rows else None,
    )


def _fetch_from_massive_rest(repo_root: Path, ticker: str, start_date: date, end_date: date) -> tuple[list[HistoricalPriceRow], ProviderAttempt]:
    try:
        config = load_massive_config(repo_root)
        rows = _fetch_massive_rows(config, ticker, start_date, end_date)
    except Exception as exc:  # pragma: no cover - network error path
        return [], ProviderAttempt("massive_rest", "error", 0, str(exc))

    if rows:
        return rows, _attempt_summary("massive_rest", "success", "Massive REST returned daily aggregate rows.", rows)
    return [], ProviderAttempt("massive_rest", "no_rows", 0, "Massive REST returned zero daily aggregate rows for the requested range.")


def _build_massive_s3_client(config: MassiveConfig):
    if boto3 is None or BotoConfig is None:
        raise RuntimeError("boto3 is required for Massive flat-file access.")
    if not config.access_key_id or not config.secret_access_key or not config.s3_endpoint or not config.bucket:
        raise RuntimeError("Massive flat-file credentials are incomplete.")
    return boto3.client(
        "s3",
        endpoint_url=config.s3_endpoint,
        aws_access_key_id=config.access_key_id,
        aws_secret_access_key=config.secret_access_key,
        region_name="us-east-1",
        config=BotoConfig(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def _iter_month_prefixes(start_date: date, end_date: date) -> Iterator[str]:
    current = date(start_date.year, start_date.month, 1)
    while current <= end_date:
        yield f"us_stocks_sip/day_aggs_v1/{current:%Y/%m}/"
        current = date(current.year + (current.month // 12), (current.month % 12) + 1, 1)


def _object_trade_date(key: str) -> date:
    return date.fromisoformat(Path(key).name.split(".")[0])


def _parse_massive_flatfile_rows(body: bytes, *, ticker: str, trade_date: date) -> list[HistoricalPriceRow]:
    with gzip.GzipFile(fileobj=io.BytesIO(body)) as compressed_handle:
        text_handle = io.TextIOWrapper(compressed_handle, encoding="utf-8")
        reader = csv.DictReader(text_handle)
        fieldnames = reader.fieldnames or []
        ticker_field = _select_column(fieldnames, "ticker", "symbol")
        open_field = _select_column(fieldnames, "open", "o")
        high_field = _select_column(fieldnames, "high", "h")
        low_field = _select_column(fieldnames, "low", "l")
        close_field = _select_column(fieldnames, "close", "c")
        volume_field = _select_column(fieldnames, "volume", "v")
        if not all([ticker_field, open_field, high_field, low_field, close_field, volume_field]):
            raise ValueError("Massive flat-file schema is missing one or more OHLCV columns.")

        rows: list[HistoricalPriceRow] = []
        for row in reader:
            if str(row.get(ticker_field, "")).strip().upper() != ticker:
                continue
            close_value = float(row.get(close_field, 0.0) or 0.0)
            if close_value == 0:
                continue
            rows.append(
                HistoricalPriceRow(
                    trade_date=trade_date.isoformat(),
                    ticker=ticker,
                    open=float(row.get(open_field, 0.0) or 0.0),
                    high=float(row.get(high_field, 0.0) or 0.0),
                    low=float(row.get(low_field, 0.0) or 0.0),
                    close=close_value,
                    volume=float(row.get(volume_field, 0.0) or 0.0),
                )
            )
        return rows


def _fetch_from_massive_flatfiles(repo_root: Path, ticker: str, start_date: date, end_date: date) -> tuple[list[HistoricalPriceRow], ProviderAttempt]:
    try:
        config = load_massive_config(repo_root)
        client = _build_massive_s3_client(config)
    except Exception as exc:
        return [], ProviderAttempt("massive_flatfiles", "unavailable", 0, str(exc))

    object_keys: list[str] = []
    try:
        for prefix in _iter_month_prefixes(start_date, end_date):
            paginator = client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=config.bucket, Prefix=prefix):
                for item in page.get("Contents", []):
                    key = item["Key"]
                    trade_date = _object_trade_date(key)
                    if start_date <= trade_date <= end_date:
                        object_keys.append(key)
    except ClientError as exc:  # pragma: no cover - live access path
        message = exc.response.get("Error", {}).get("Message", str(exc))
        return [], ProviderAttempt("massive_flatfiles", "error", 0, message)

    if not object_keys:
        return [], ProviderAttempt("massive_flatfiles", "no_rows", 0, "No Massive flat-file day aggregates were listed for the requested range.")

    rows: list[HistoricalPriceRow] = []
    for key in sorted(object_keys):
        try:
            response = client.get_object(Bucket=config.bucket, Key=key)
        except ClientError as exc:
            status_code = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            message = exc.response.get("Error", {}).get("Message", str(exc))
            if status_code == 403:
                return [], ProviderAttempt(
                    "massive_flatfiles",
                    "restricted",
                    0,
                    "Massive flat-file credentials can list day_aggs_v1 keys but cannot download objects (403 Forbidden).",
                )
            return [], ProviderAttempt("massive_flatfiles", "error", 0, message)

        rows.extend(_parse_massive_flatfile_rows(response["Body"].read(), ticker=ticker, trade_date=_object_trade_date(key)))

    if rows:
        rows.sort(key=lambda row: row.trade_date)
        return rows, _attempt_summary("massive_flatfiles", "success", "Massive flat-file day aggregates returned ticker rows.", rows)
    return [], ProviderAttempt("massive_flatfiles", "no_rows", 0, "Massive flat-file day aggregates contained no rows for the requested ticker.")


def _alpaca_env(repo_root: Path) -> dict[str, str]:
    return _load_env_file(repo_root / ".env")


def _alpaca_request(repo_root: Path, url: str) -> dict[str, Any]:
    env = _alpaca_env(repo_root)
    key = env.get("ALPACA_API_KEY")
    secret = env.get("ALPACA_SECRET_KEY")
    if not key or not secret:
        raise RuntimeError("Alpaca API credentials are missing.")

    request = Request(
        url,
        headers={
            "APCA-API-KEY-ID": key,
            "APCA-API-SECRET-KEY": secret,
            "User-Agent": "StrattonAI/1.0",
        },
    )
    with urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def _fetch_from_alpaca(repo_root: Path, ticker: str, start_date: date, end_date: date) -> tuple[list[HistoricalPriceRow], ProviderAttempt]:
    params = urlencode(
        {
            "timeframe": "1Day",
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "limit": "10000",
        }
    )
    bars_url = f"https://data.alpaca.markets/v2/stocks/{ticker}/bars?{params}"
    try:
        payload = _alpaca_request(repo_root, bars_url)
    except HTTPError as exc:  # pragma: no cover - network path
        body = exc.read().decode("utf-8", errors="replace")
        return [], ProviderAttempt("alpaca", "error", 0, body[:400])
    except URLError as exc:  # pragma: no cover - network path
        return [], ProviderAttempt("alpaca", "error", 0, str(exc))
    except Exception as exc:
        return [], ProviderAttempt("alpaca", "unavailable", 0, str(exc))

    bars = payload.get("bars") or []
    rows = [
        HistoricalPriceRow(
            trade_date=str(bar["t"]).split("T")[0],
            ticker=ticker,
            open=float(bar.get("o", 0.0)),
            high=float(bar.get("h", 0.0)),
            low=float(bar.get("l", 0.0)),
            close=float(bar.get("c", 0.0)),
            volume=float(bar.get("v", 0.0)),
        )
        for bar in bars
        if float(bar.get("c", 0.0) or 0.0) != 0.0
    ]
    if rows:
        return rows, _attempt_summary("alpaca", "success", "Alpaca returned historical stock bars.", rows)

    asset_message = "Alpaca returned no historical bars for the requested ticker."
    try:
        asset = _alpaca_request(repo_root, f"https://paper-api.alpaca.markets/v2/assets/{ticker}")
        asset_message = f"Alpaca returned no bars. Asset status={asset.get('status')} tradable={asset.get('tradable')} exchange={asset.get('exchange')}."
    except Exception:
        pass
    return [], ProviderAttempt("alpaca", "no_rows", 0, asset_message)


def _fmp_request(url: str) -> tuple[int, str]:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 StrattonAI/1.0"})
    try:
        with urlopen(request, timeout=60) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


def _fetch_from_fmp(repo_root: Path, ticker: str, start_date: date, end_date: date) -> tuple[list[HistoricalPriceRow], ProviderAttempt]:
    env = _load_env_file(repo_root / ".env")
    api_key = env.get("FMP_API_KEY")
    if not api_key:
        return [], ProviderAttempt("fmp", "unavailable", 0, "FMP_API_KEY is missing.")

    url = "https://financialmodelingprep.com/stable/historical-price-eod/light?" + urlencode(
        {"symbol": ticker, "from": start_date.isoformat(), "to": end_date.isoformat(), "apikey": api_key}
    )
    try:
        status, body = _fmp_request(url)
    except Exception as exc:
        return [], ProviderAttempt("fmp", "unavailable", 0, str(exc))

    if status in {402, 403}:
        normalized_body = body[:300].strip().replace("\n", " ")
        attempt_status = "unavailable" if "invalid api key" in normalized_body.lower() else "restricted"
        return [], ProviderAttempt("fmp", attempt_status, 0, normalized_body)
    if status != 200:
        return [], ProviderAttempt("fmp", "error", 0, body[:300].strip().replace("\n", " "))

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return [], ProviderAttempt("fmp", "error", 0, "FMP returned a non-JSON historical response.")

    records = payload if isinstance(payload, list) else payload.get("historical", [])
    rows: list[HistoricalPriceRow] = []
    for row in records or []:
        close_value = float(row.get("close", 0.0) or 0.0)
        if close_value == 0.0:
            continue
        rows.append(
            HistoricalPriceRow(
                trade_date=str(row.get("date")),
                ticker=ticker,
                open=float(row.get("open", close_value)),
                high=float(row.get("high", close_value)),
                low=float(row.get("low", close_value)),
                close=close_value,
                volume=float(row.get("volume", 0.0) or 0.0),
            )
        )
    if rows:
        rows.sort(key=lambda row: row.trade_date)
        return rows, _attempt_summary("fmp", "success", "FMP returned historical EOD rows.", rows)
    return [], ProviderAttempt("fmp", "no_rows", 0, "FMP returned no historical rows for the requested ticker.")


def _fetch_from_alpha_vantage(repo_root: Path, ticker: str, start_date: date, end_date: date) -> tuple[list[HistoricalPriceRow], ProviderAttempt]:
    env = _load_env_file(repo_root / ".env")
    api_key = env.get("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        return [], ProviderAttempt("alpha_vantage", "unavailable", 0, "ALPHA_VANTAGE_API_KEY is missing.")

    url = "https://www.alphavantage.co/query?" + urlencode(
        {"function": "TIME_SERIES_DAILY", "symbol": ticker, "outputsize": "full", "apikey": api_key}
    )
    request = Request(url, headers={"User-Agent": "StrattonAI/1.0"})
    try:
        with urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:  # pragma: no cover - network path
        body = exc.read().decode("utf-8", errors="replace")
        return [], ProviderAttempt("alpha_vantage", "error", 0, body[:300])
    except URLError as exc:  # pragma: no cover - network path
        return [], ProviderAttempt("alpha_vantage", "error", 0, str(exc))

    info_message = payload.get("Information") or payload.get("Note") or payload.get("Error Message")
    if info_message:
        status = "restricted" if "premium" in info_message.lower() or "rate limit" in info_message.lower() else "no_rows"
        return [], ProviderAttempt("alpha_vantage", status, 0, info_message[:300])

    series = payload.get("Time Series (Daily)", {})
    rows: list[HistoricalPriceRow] = []
    for trade_date, row in sorted(series.items()):
        trade_date_value = date.fromisoformat(trade_date)
        if not (start_date <= trade_date_value <= end_date):
            continue
        close_value = float(row.get("4. close", 0.0) or 0.0)
        if close_value == 0.0:
            continue
        rows.append(
            HistoricalPriceRow(
                trade_date=trade_date,
                ticker=ticker,
                open=float(row.get("1. open", close_value)),
                high=float(row.get("2. high", close_value)),
                low=float(row.get("3. low", close_value)),
                close=close_value,
                volume=float(row.get("5. volume", 0.0) or 0.0),
            )
        )
    if rows:
        return rows, _attempt_summary("alpha_vantage", "success", "Alpha Vantage returned historical daily rows.", rows)
    return [], ProviderAttempt("alpha_vantage", "no_rows", 0, "Alpha Vantage returned no rows for the requested ticker.")


def _iter_provider_fetchers() -> tuple[ProviderFetcher, ...]:
    return (
        _fetch_from_massive_rest,
        _fetch_from_massive_flatfiles,
        _fetch_from_alpaca,
        _fetch_from_fmp,
        _fetch_from_alpha_vantage,
    )


def _resolve_base_inputs(base_price_path: Path) -> tuple[Path | None, Path | None]:
    base_parquet_input = base_price_path if base_price_path.suffix.lower() == ".parquet" else None
    base_csv_input = base_price_path if base_price_path.suffix.lower() == ".csv" else None

    if base_parquet_input is None:
        parquet_candidate = base_price_path.with_suffix(".parquet")
        if parquet_candidate.exists():
            base_parquet_input = parquet_candidate
    if base_csv_input is None:
        csv_candidate = base_price_path.with_suffix(".csv")
        if csv_candidate.exists():
            base_csv_input = csv_candidate
    return base_parquet_input, base_csv_input


def build_markdown_report(report: ExternalPriceGapFillReport) -> str:
    lines = [
        "# External Price Gap Fill",
        "",
        f"- Base price dataset: `{report.base_price_path}` ({report.base_price_format})",
        f"- Previous price max date: {report.previous_price_max_date}",
        f"- New price max date: {report.new_price_max_date}",
        f"- Target tickers: {', '.join(report.target_tickers) or 'None'}",
        f"- Tickers filled: {', '.join(report.tickers_filled) or 'None'}",
        f"- Tickers unresolved: {', '.join(report.tickers_unresolved) or 'None'}",
        f"- Total rows added: {report.total_rows_added}",
        f"- Cumulative external backfill rows: {report.cumulative_backfill_rows}",
        f"- Supabase rows upserted: {report.supabase_rows_upserted}",
        "",
        "## Ticker Results",
    ]
    for result in report.results:
        lines.append(
            f"- {result.ticker}: provider={result.selected_provider or 'None'} rows_found={result.rows_found} rows_added={result.rows_added} range={result.start_date} -> {result.end_date}"
        )
        for attempt in result.attempts:
            lines.append(
                f"  - {attempt.provider}: status={attempt.status}, rows={attempt.row_count}, message={attempt.message}"
            )
    return "\n".join(lines) + "\n"


def run_fill(
    repo_root: Path,
    *,
    price_file: str | None,
    ticker_overrides: list[str],
    load_supabase: bool,
    bootstrap_daily_prices_schema: bool,
    dry_run: bool,
) -> ExternalPriceGapFillReport:
    resolved_base = resolve_price_dataset_path(repo_root, price_file, allow_sample_fallback=False)
    base_price_path = resolved_base.path.resolve()
    target_tickers = _determine_target_tickers(repo_root, base_price_path, ticker_overrides)
    target_ticker_set = set(target_tickers)
    existing_keys, previous_max_date = _existing_price_keys(base_price_path, target_ticker_set)
    if not previous_max_date:
        previous_max_date = inspect_price_series_file(base_price_path).max_date or ""
    event_ranges = _determine_event_ranges(repo_root, target_tickers)

    backfill_dir = base_price_path.parent / "backfills"
    backfill_csv_path = backfill_dir / "external_price_gap_backfill.csv"
    backfill_parquet_path = backfill_dir / "external_price_gap_backfill.parquet"
    enriched_parquet_path = base_price_path.parent / "all_stock_data_extended_enriched.parquet"
    enriched_csv_path = base_price_path.parent / "all_stock_data_extended_enriched.csv"

    fetched_rows: list[HistoricalPriceRow] = []
    results: list[TickerGapFillResult] = []

    for ticker in target_tickers:
        date_range = event_ranges.get(ticker)
        if date_range is None:
            results.append(
                TickerGapFillResult(
                    ticker=ticker,
                    start_date="",
                    end_date="",
                    selected_provider=None,
                    rows_found=0,
                    rows_added=0,
                    attempts=(
                        ProviderAttempt(
                            provider="event_range",
                            status="unavailable",
                            row_count=0,
                            message="No study events were found for the requested ticker, so no backfill range could be derived.",
                        ),
                    ),
                )
            )
            continue

        start_date, end_date = date_range
        attempts: list[ProviderAttempt] = []
        selected_provider: str | None = None
        selected_rows: list[HistoricalPriceRow] = []
        for fetcher in _iter_provider_fetchers():
            rows, attempt = fetcher(repo_root, ticker, start_date, end_date)
            attempts.append(attempt)
            if rows:
                selected_provider = attempt.provider
                selected_rows = rows
                break

        unique_new_rows: list[HistoricalPriceRow] = []
        for row in selected_rows:
            if row.key in existing_keys:
                continue
            existing_keys.add(row.key)
            unique_new_rows.append(row)
        fetched_rows.extend(unique_new_rows)
        results.append(
            TickerGapFillResult(
                ticker=ticker,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                selected_provider=selected_provider,
                rows_found=len(selected_rows),
                rows_added=len(unique_new_rows),
                attempts=tuple(attempts),
            )
        )

    cumulative_backfill_rows = _merge_backfill_rows(_load_existing_backfill_rows(backfill_csv_path), fetched_rows)

    base_parquet_input, base_csv_input = _resolve_base_inputs(base_price_path)
    if not dry_run and fetched_rows:
        _write_rows_csv(cumulative_backfill_rows, backfill_csv_path)
        _write_rows_parquet(cumulative_backfill_rows, backfill_parquet_path)
        if base_parquet_input is not None:
            _copy_with_new_rows_parquet(base_parquet_input, enriched_parquet_path, fetched_rows)
        if base_csv_input is not None:
            _copy_with_new_rows_csv(base_csv_input, enriched_csv_path, fetched_rows)

    if not dry_run and fetched_rows and enriched_parquet_path.exists():
        coverage_path = enriched_parquet_path
    elif not dry_run and fetched_rows and enriched_csv_path.exists():
        coverage_path = enriched_csv_path
    else:
        coverage_path = base_parquet_input or base_csv_input or base_price_path
    coverage_inspection = inspect_price_series_file(coverage_path, tickers=target_tickers)

    supabase_rows_upserted = 0
    if not dry_run and fetched_rows and load_supabase and coverage_path.exists():
        summary = run_load(
            repo_root,
            price_file=str(coverage_path),
            bootstrap_schema=bootstrap_daily_prices_schema,
            schema_file=str(repo_root / "supabase" / "sql" / "008_add_daily_prices.sql"),
            ticker_filters=target_tickers,
            study_universe=False,
            dry_run=False,
        )
        supabase_rows_upserted = summary.rows_upserted

    return ExternalPriceGapFillReport(
        base_price_path=str(base_price_path),
        base_price_format=resolved_base.format,
        enriched_parquet_path=str(enriched_parquet_path) if base_parquet_input is not None else None,
        enriched_csv_path=str(enriched_csv_path) if base_csv_input is not None else None,
        backfill_parquet_path=str(backfill_parquet_path),
        backfill_csv_path=str(backfill_csv_path),
        target_tickers=tuple(target_tickers),
        tickers_filled=tuple(sorted(result.ticker for result in results if result.rows_added > 0)),
        tickers_unresolved=tuple(sorted(result.ticker for result in results if result.rows_added == 0)),
        total_rows_added=len(fetched_rows),
        cumulative_backfill_rows=len(cumulative_backfill_rows),
        previous_price_max_date=previous_max_date,
        new_price_max_date=coverage_inspection.max_date or previous_max_date,
        supabase_rows_upserted=supabase_rows_upserted,
        results=tuple(results),
        completed_at=datetime.now(UTC).isoformat(),
    )


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)

    repo_root = Path(__file__).resolve().parent.parent
    report = run_fill(
        repo_root,
        price_file=args.price_file,
        ticker_overrides=args.ticker,
        load_supabase=args.load_supabase,
        bootstrap_daily_prices_schema=args.bootstrap_daily_prices_schema,
        dry_run=args.dry_run,
    )

    json_output = Path(args.json_output)
    markdown_output = Path(args.markdown_output)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    markdown_output.write_text(build_markdown_report(report), encoding="utf-8")
    LOGGER.info(
        "External price gap fill complete. target_tickers=%s filled=%s unresolved=%s rows_added=%s",
        list(report.target_tickers),
        list(report.tickers_filled),
        list(report.tickers_unresolved),
        report.total_rows_added,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
