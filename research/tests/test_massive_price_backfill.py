from __future__ import annotations

import csv
import tempfile
import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
from unittest.mock import patch

import pyarrow as pa
import pyarrow.parquet as pq

from research.event_study_engine import build_price_map, compute_event_study_observations
from research.event_study_models import PricePoint, PriceSeries, StudyEvent
from research.massive_config import MassiveConfig
from research.massive_price_backfill import HistoricalPriceRow, _fetch_massive_rows, run_massive_price_backfill
from research.price_dataset import load_resolved_price_series, resolve_price_dataset_path


def _write_base_csv(path: Path, rows: list[tuple[str, str, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["Date", "Ticker", "Open", "High", "Low", "Close", "Volume", "Dividends", "Stock Splits"],
        )
        writer.writeheader()
        for trade_date, ticker, close in rows:
            writer.writerow(
                {
                    "Date": trade_date,
                    "Ticker": ticker,
                    "Open": close,
                    "High": close,
                    "Low": close,
                    "Close": close,
                    "Volume": 1000,
                    "Dividends": 0,
                    "Stock Splits": 0,
                }
            )


def _write_base_parquet(path: Path, rows: list[tuple[str, str, float]]) -> None:
    table = pa.table(
        {
            "Date": [date.fromisoformat(trade_date) for trade_date, _ticker, _close in rows],
            "Ticker": [ticker for _trade_date, ticker, _close in rows],
            "Open": [close for _trade_date, _ticker, close in rows],
            "High": [close for _trade_date, _ticker, close in rows],
            "Low": [close for _trade_date, _ticker, close in rows],
            "Close": [close for _trade_date, _ticker, close in rows],
            "Volume": [1000.0 for _trade_date, _ticker, _close in rows],
            "Dividends": [0.0 for _trade_date, _ticker, _close in rows],
            "Stock Splits": [0.0 for _trade_date, _ticker, _close in rows],
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path, compression="snappy")


class MassivePriceBackfillTests(unittest.TestCase):
    def _create_repo(self) -> tuple[Path, Path]:
        root = Path(tempfile.mkdtemp())
        repo_root = root / "ui"
        prices_dir = root / "data" / "prices"
        repo_root.mkdir(parents=True, exist_ok=True)
        prices_dir.mkdir(parents=True, exist_ok=True)
        (repo_root / ".env").write_text("MASSIVE_API_KEY=test_key\n", encoding="utf-8")
        base_rows = [
            ("2024-11-01", "AAPL", 100.0),
            ("2024-11-04", "AAPL", 101.0),
        ]
        _write_base_csv(prices_dir / "all_stock_data.csv", base_rows)
        _write_base_parquet(prices_dir / "all_stock_data.parquet", base_rows)
        return root, repo_root

    def test_backfill_writes_deterministically_and_prefers_extended_parquet(self) -> None:
        _root, repo_root = self._create_repo()
        fetched_rows = [
            HistoricalPriceRow("2024-11-05", "AAPL", 102.0, 103.0, 101.0, 102.0, 1200.0),
            HistoricalPriceRow("2024-11-06", "AAPL", 103.0, 104.0, 102.0, 103.0, 1300.0),
            HistoricalPriceRow("2024-11-07", "AAPL", 104.0, 105.0, 103.0, 104.0, 1400.0),
        ]

        with patch("research.massive_price_backfill._fetch_massive_rows", return_value=fetched_rows):
            first = run_massive_price_backfill(
                repo_root,
                start_date="2024-11-05",
                end_date="2024-11-07",
                ticker_overrides=["AAPL"],
                dry_run=False,
            )
            second = run_massive_price_backfill(
                repo_root,
                start_date="2024-11-05",
                end_date="2024-11-07",
                ticker_overrides=["AAPL"],
                dry_run=False,
            )

        self.assertEqual(first.previous_price_max_date, "2024-11-04")
        self.assertEqual(first.new_price_max_date, "2024-11-07")
        self.assertEqual(first.fetched_row_count, 3)
        self.assertEqual(first.backfill_row_count, 3)
        self.assertEqual(second.backfill_row_count, 3)

        resolved = resolve_price_dataset_path(repo_root)
        self.assertEqual(resolved.resolution_reason, "default_extended_parquet")
        self.assertTrue(Path(first.extended_parquet_path).exists())
        self.assertTrue(Path(first.extended_csv_path).exists())

    def test_extended_dataset_unlocks_non_zero_observations_for_future_event(self) -> None:
        _root, repo_root = self._create_repo()
        fetched_rows = [
            HistoricalPriceRow("2024-11-05", "AAPL", 102.0, 103.0, 101.0, 102.0, 1200.0),
            HistoricalPriceRow("2024-11-06", "AAPL", 103.0, 104.0, 102.0, 103.0, 1300.0),
            HistoricalPriceRow("2024-11-07", "AAPL", 104.0, 105.0, 103.0, 104.0, 1400.0),
            HistoricalPriceRow("2024-11-08", "AAPL", 105.0, 106.0, 104.0, 105.0, 1500.0),
            HistoricalPriceRow("2024-11-11", "AAPL", 106.0, 107.0, 105.0, 106.0, 1600.0),
            HistoricalPriceRow("2024-11-12", "AAPL", 107.0, 108.0, 106.0, 107.0, 1700.0),
            HistoricalPriceRow("2024-11-13", "AAPL", 108.0, 109.0, 107.0, 108.0, 1800.0),
            HistoricalPriceRow("2024-11-14", "AAPL", 109.0, 110.0, 108.0, 109.0, 1900.0),
            HistoricalPriceRow("2024-11-15", "AAPL", 110.0, 111.0, 109.0, 110.0, 2000.0),
            HistoricalPriceRow("2024-11-18", "AAPL", 111.0, 112.0, 110.0, 111.0, 2100.0),
        ]

        with patch("research.massive_price_backfill._fetch_massive_rows", return_value=fetched_rows):
            run_massive_price_backfill(
                repo_root,
                start_date="2024-11-05",
                end_date="2024-11-18",
                ticker_overrides=["AAPL"],
                dry_run=False,
            )

        base_series, _ = load_resolved_price_series(
            repo_root,
            explicit_path="data/prices/all_stock_data.parquet",
            tickers={"AAPL"},
            allow_sample_fallback=False,
        )
        extended_series, _ = load_resolved_price_series(
            repo_root,
            explicit_path=None,
            tickers={"AAPL"},
            allow_sample_fallback=False,
        )

        event = StudyEvent(
            id="evt-1",
            ticker="AAPL",
            category="Macro Event",
            timestamp=datetime(2024, 11, 6, 14, 0, tzinfo=timezone.utc),
        )
        base_observations, _base_stats = compute_event_study_observations([event], build_price_map(base_series))
        extended_observations, _extended_stats = compute_event_study_observations([event], build_price_map(extended_series))

        self.assertEqual(len(base_observations), 0)
        self.assertGreater(len(extended_observations), 0)
        self.assertTrue(any(observation.study_target_type == "primary" for observation in extended_observations))

    def test_fetch_massive_rows_retries_alias_when_primary_symbol_returns_no_rows(self) -> None:
        class FakeResponse:
            def __init__(self, payload: dict[str, object]):
                self.payload = payload

            def read(self) -> bytes:
                return json.dumps(self.payload).encode("utf-8")

            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, exc_type, exc, tb) -> None:
                return None

        config = MassiveConfig(api_key="test_api_key", base_url="https://api.massive.com")
        calls: list[str] = []

        def fake_urlopen(request, timeout=60):  # type: ignore[no-untyped-def]
            calls.append(request.full_url)
            if "NYSE%3ATTM" in request.full_url:
                return FakeResponse(
                    {
                        "results": [
                            {
                                "t": 1704153600000,
                                "o": 25.0,
                                "h": 26.0,
                                "l": 24.5,
                                "c": 25.5,
                                "v": 1200,
                            }
                        ]
                    }
                )
            return FakeResponse({"results": []})

        with patch("research.massive_price_backfill.urlopen", side_effect=fake_urlopen):
            rows = _fetch_massive_rows(config, "TTM", date(2024, 1, 2), date(2024, 1, 2))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].ticker, "TTM")
        self.assertEqual(rows[0].trade_date, "2024-01-02")
        self.assertEqual(len(calls), 2)
        self.assertIn("/TTM/range/1/day/2024-01-02/2024-01-02", calls[0])
        self.assertIn("/NYSE%3ATTM/range/1/day/2024-01-02/2024-01-02", calls[1])


if __name__ == "__main__":
    unittest.main()
