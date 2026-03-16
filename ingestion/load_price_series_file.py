from __future__ import annotations

from collections import Counter, defaultdict
import csv
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
from typing import Any, Iterable

try:
    import pyarrow.dataset as pa_dataset
except ImportError:  # pragma: no cover - optional dependency
    pa_dataset = None

try:
    from research.event_study_models import PricePoint, PriceSeries
except ImportError:  # pragma: no cover - script execution fallback
    from event_study_models import PricePoint, PriceSeries  # type: ignore


TABULAR_REQUIRED_COLUMNS = ("Date", "Ticker", "Close")
JSON_REQUIRED_FIELDS = ("series",)


class PriceSeriesValidationError(ValueError):
    """Raised when structured price input cannot be parsed safely."""


@dataclass(frozen=True, slots=True)
class PriceDatasetInspection:
    path: str
    format: str
    row_count: int
    distinct_ticker_count: int
    min_date: str | None
    max_date: str | None
    required_columns: tuple[str, ...]
    missing_columns: tuple[str, ...]
    rejected_rows: int
    rejection_reasons: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "format": self.format,
            "row_count": self.row_count,
            "distinct_ticker_count": self.distinct_ticker_count,
            "min_date": self.min_date,
            "max_date": self.max_date,
            "required_columns": list(self.required_columns),
            "missing_columns": list(self.missing_columns),
            "rejected_rows": self.rejected_rows,
            "rejection_reasons": self.rejection_reasons,
        }


def _load_json(path: str | Path) -> Any:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Price series file not found: {file_path}")

    return json.loads(file_path.read_text(encoding="utf-8"))


def _normalize_tickers(tickers: Iterable[str] | None) -> set[str] | None:
    if tickers is None:
        return None
    normalized = {str(ticker).strip().upper() for ticker in tickers if str(ticker).strip()}
    return normalized or None


def _detect_format(path: str | Path) -> str:
    suffix = Path(path).suffix.lower()
    if suffix == ".json":
        return "json"
    if suffix == ".csv":
        return "csv"
    if suffix == ".parquet":
        return "parquet"
    raise PriceSeriesValidationError(
        f"Unsupported price file format for '{path}'. Expected .json, .csv, or .parquet."
    )


def _generate_business_dates(range_payload: dict[str, Any]) -> list[str]:
    start_raw = range_payload.get("start")
    end_raw = range_payload.get("end")

    if not isinstance(start_raw, str) or not isinstance(end_raw, str):
        raise PriceSeriesValidationError("date_range requires string start and end values.")

    start_date = date.fromisoformat(start_raw)
    end_date = date.fromisoformat(end_raw)
    if end_date < start_date:
        raise PriceSeriesValidationError("date_range.end must be on or after date_range.start.")

    dates: list[str] = []
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:
            dates.append(current.isoformat())
        current += timedelta(days=1)

    if not dates:
        raise PriceSeriesValidationError("date_range produced no business dates.")

    return dates


def _resolve_dates(payload: dict[str, Any]) -> list[str]:
    dates = payload.get("dates")
    if isinstance(dates, list) and all(isinstance(item, str) for item in dates):
        return dates

    date_range = payload.get("date_range")
    if isinstance(date_range, dict):
        return _generate_business_dates(date_range)

    raise PriceSeriesValidationError("Price series file requires either a string-array 'dates' field or a 'date_range' object.")


def _expand_segment_series(entry: dict[str, Any], date_count: int) -> list[float]:
    ticker = str(entry.get("ticker", "")).strip().upper()
    start_close = entry.get("start_close")
    segments = entry.get("segments")

    if start_close is None:
        raise PriceSeriesValidationError(f"{ticker} requires either 'closes' or 'start_close'.")

    if not isinstance(segments, list) or not segments:
        raise PriceSeriesValidationError(f"{ticker} requires a non-empty 'segments' array when using start_close.")

    try:
        current_close = float(start_close)
    except (TypeError, ValueError) as exc:
        raise PriceSeriesValidationError(f"{ticker} start_close must be numeric.") from exc

    closes = [round(current_close, 4)]
    expanded_moves: list[float] = []
    for segment in segments:
        if not isinstance(segment, dict):
            raise PriceSeriesValidationError(f"{ticker} segment entries must be objects.")

        days = segment.get("days")
        daily_move = segment.get("daily_move")
        if not isinstance(days, int) or days <= 0:
            raise PriceSeriesValidationError(f"{ticker} segment days must be a positive integer.")
        if not isinstance(daily_move, (int, float)):
            raise PriceSeriesValidationError(f"{ticker} segment daily_move must be numeric.")

        expanded_moves.extend([float(daily_move)] * days)

    expected_moves = date_count - 1
    if len(expanded_moves) != expected_moves:
        raise PriceSeriesValidationError(
            f"{ticker} segment days ({len(expanded_moves)}) must equal date count minus one ({expected_moves})."
        )

    for move in expanded_moves:
        current_close = max(current_close + move, 0.01)
        closes.append(round(current_close, 4))

    return closes


def _normalize_trade_date(value: Any) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if value in {None, ""}:
        raise PriceSeriesValidationError("missing_date")
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:  # pragma: no cover - guarded by tests
        raise PriceSeriesValidationError("invalid_date") from exc


def _normalize_close(value: Any) -> Decimal:
    if value in {None, ""}:
        raise PriceSeriesValidationError("missing_close")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:  # pragma: no cover - guarded by tests
        raise PriceSeriesValidationError("invalid_close") from exc


def _normalize_row(trade_date_value: Any, ticker_value: Any, close_value: Any) -> tuple[str, PricePoint]:
    ticker = str(ticker_value or "").strip().upper()
    if not ticker:
        raise PriceSeriesValidationError("missing_ticker")
    trade_date = _normalize_trade_date(trade_date_value)
    close = _normalize_close(close_value)
    return ticker, PricePoint(date=trade_date, close=close)


def _consume_rows(
    rows: Iterable[tuple[Any, Any, Any]],
    *,
    tickers: set[str] | None,
    collect_points: bool,
) -> tuple[defaultdict[str, list[PricePoint]], PriceDatasetInspection]:
    grouped_points: defaultdict[str, list[PricePoint]] = defaultdict(list)
    accepted_rows = 0
    tickers_seen: set[str] = set()
    rejection_reasons: Counter[str] = Counter()
    min_trade_date: date | None = None
    max_trade_date: date | None = None

    for trade_date_value, ticker_value, close_value in rows:
        candidate_ticker = str(ticker_value or "").strip().upper()
        if tickers is not None and candidate_ticker not in tickers:
            continue

        try:
            ticker, point = _normalize_row(trade_date_value, ticker_value, close_value)
        except PriceSeriesValidationError as exc:
            rejection_reasons[str(exc)] += 1
            continue

        accepted_rows += 1
        tickers_seen.add(ticker)
        min_trade_date = point.date if min_trade_date is None or point.date < min_trade_date else min_trade_date
        max_trade_date = point.date if max_trade_date is None or point.date > max_trade_date else max_trade_date
        if collect_points:
            grouped_points[ticker].append(point)

    inspection = PriceDatasetInspection(
        path="",
        format="",
        row_count=accepted_rows,
        distinct_ticker_count=len(tickers_seen),
        min_date=min_trade_date.isoformat() if min_trade_date else None,
        max_date=max_trade_date.isoformat() if max_trade_date else None,
        required_columns=TABULAR_REQUIRED_COLUMNS,
        missing_columns=(),
        rejected_rows=sum(rejection_reasons.values()),
        rejection_reasons=dict(sorted(rejection_reasons.items())),
    )
    return grouped_points, inspection


def _build_series_from_grouped_points(grouped_points: defaultdict[str, list[PricePoint]]) -> list[PriceSeries]:
    return [
        PriceSeries(
            ticker=ticker,
            prices=tuple(sorted(points, key=lambda point: point.date)),
        )
        for ticker, points in sorted(grouped_points.items())
    ]


def _load_json_series(path: str | Path, tickers: set[str] | None) -> list[PriceSeries]:
    payload = _load_json(path)

    if not isinstance(payload, dict):
        raise PriceSeriesValidationError("Price series file must be an object.")

    dates = _resolve_dates(payload)
    series_entries = payload.get("series")

    if not isinstance(series_entries, list):
        raise PriceSeriesValidationError("Price series file requires a 'series' array.")

    series: list[PriceSeries] = []
    for entry in series_entries:
        if not isinstance(entry, dict):
            raise PriceSeriesValidationError("Each series entry must be an object.")

        ticker = str(entry.get("ticker", "")).strip().upper()
        if tickers is not None and ticker not in tickers:
            continue
        closes = entry.get("closes")

        if not ticker:
            raise PriceSeriesValidationError("Series entries require a ticker.")

        if closes is None:
            closes = _expand_segment_series(entry, len(dates))

        if not isinstance(closes, list):
            raise PriceSeriesValidationError(f"{ticker} requires a 'closes' array.")

        if len(closes) != len(dates):
            raise PriceSeriesValidationError(
                f"{ticker} close count ({len(closes)}) must match date count ({len(dates)})."
            )

        points = tuple(
            PricePoint.from_strings(trade_date, close)
            for trade_date, close in zip(dates, closes, strict=True)
        )
        series.append(PriceSeries(ticker=ticker, prices=points))

    return series


def _inspect_json_series(path: str | Path, tickers: set[str] | None) -> PriceDatasetInspection:
    series = _load_json_series(path, tickers)
    all_points = [point for item in series for point in item.prices]
    if all_points:
        min_trade_date = min(point.date for point in all_points).isoformat()
        max_trade_date = max(point.date for point in all_points).isoformat()
    else:
        min_trade_date = None
        max_trade_date = None
    payload = _load_json(path)
    missing_fields = tuple(field for field in JSON_REQUIRED_FIELDS if field not in payload)
    return PriceDatasetInspection(
        path=str(Path(path)),
        format="json",
        row_count=len(all_points),
        distinct_ticker_count=len(series),
        min_date=min_trade_date,
        max_date=max_trade_date,
        required_columns=JSON_REQUIRED_FIELDS,
        missing_columns=missing_fields,
        rejected_rows=0,
        rejection_reasons={},
    )


def _validate_tabular_columns(columns: Iterable[str]) -> tuple[str, ...]:
    column_set = set(columns)
    missing_columns = tuple(column for column in TABULAR_REQUIRED_COLUMNS if column not in column_set)
    if missing_columns:
        raise PriceSeriesValidationError(
            "Tabular price dataset is missing required columns: " + ", ".join(missing_columns)
        )
    return missing_columns


def _iter_csv_rows(path: Path) -> tuple[Iterable[tuple[Any, Any, Any]], tuple[str, ...]]:
    def generator() -> Iterable[tuple[Any, Any, Any]]:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = tuple(reader.fieldnames or ())
            _validate_tabular_columns(fieldnames)
            for row in reader:
                yield row.get("Date"), row.get("Ticker"), row.get("Close")

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(reader.fieldnames or ())
    _validate_tabular_columns(fieldnames)
    return generator(), fieldnames


def _iter_parquet_rows(path: Path, tickers: set[str] | None) -> tuple[Iterable[tuple[Any, Any, Any]], tuple[str, ...]]:
    if pa_dataset is None:
        raise PriceSeriesValidationError(
            "Parquet support requires pyarrow. Install pyarrow to read .parquet price datasets."
        )

    dataset = pa_dataset.dataset(path, format="parquet")
    fieldnames = tuple(dataset.schema.names)
    _validate_tabular_columns(fieldnames)
    filter_expression = None
    if tickers:
        filter_expression = pa_dataset.field("Ticker").isin(sorted(tickers))

    def generator() -> Iterable[tuple[Any, Any, Any]]:
        scanner = dataset.scanner(columns=list(TABULAR_REQUIRED_COLUMNS), filter=filter_expression, batch_size=65536)
        for batch in scanner.to_batches():
            date_values = batch.column(0).to_pylist()
            ticker_values = batch.column(1).to_pylist()
            close_values = batch.column(2).to_pylist()
            yield from zip(date_values, ticker_values, close_values, strict=True)

    return generator(), fieldnames


def _load_tabular_series(path: Path, file_format: str, tickers: set[str] | None) -> list[PriceSeries]:
    if file_format == "csv":
        rows, _fieldnames = _iter_csv_rows(path)
        grouped_points, inspection = _consume_rows(rows, tickers=tickers, collect_points=True)
    else:
        rows, _fieldnames = _iter_parquet_rows(path, tickers)
        grouped_points, inspection = _consume_rows(rows, tickers=None, collect_points=True)

    if inspection.rejected_rows:
        # Rejected rows are skipped deterministically; parity tools surface the exact reasons.
        pass

    return _build_series_from_grouped_points(grouped_points)


def _inspect_tabular_series(path: Path, file_format: str, tickers: set[str] | None) -> PriceDatasetInspection:
    if file_format == "csv":
        rows, fieldnames = _iter_csv_rows(path)
        _grouped_points, inspection = _consume_rows(rows, tickers=tickers, collect_points=False)
    else:
        rows, fieldnames = _iter_parquet_rows(path, tickers)
        _grouped_points, inspection = _consume_rows(rows, tickers=None, collect_points=False)

    return PriceDatasetInspection(
        path=str(path),
        format=file_format,
        row_count=inspection.row_count,
        distinct_ticker_count=inspection.distinct_ticker_count,
        min_date=inspection.min_date,
        max_date=inspection.max_date,
        required_columns=TABULAR_REQUIRED_COLUMNS,
        missing_columns=tuple(column for column in TABULAR_REQUIRED_COLUMNS if column not in set(fieldnames)),
        rejected_rows=inspection.rejected_rows,
        rejection_reasons=inspection.rejection_reasons,
    )


def load_price_series_file(path: str | Path, *, tickers: Iterable[str] | None = None) -> list[PriceSeries]:
    normalized_tickers = _normalize_tickers(tickers)
    file_path = Path(path)
    file_format = _detect_format(file_path)

    if file_format == "json":
        return _load_json_series(file_path, normalized_tickers)

    return _load_tabular_series(file_path, file_format, normalized_tickers)


def inspect_price_series_file(path: str | Path, *, tickers: Iterable[str] | None = None) -> PriceDatasetInspection:
    normalized_tickers = _normalize_tickers(tickers)
    file_path = Path(path)
    file_format = _detect_format(file_path)

    if file_format == "json":
        return _inspect_json_series(file_path, normalized_tickers)

    return _inspect_tabular_series(file_path, file_format, normalized_tickers)
