from __future__ import annotations

import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pyarrow as pa
import pyarrow.parquet as pq

from research.event_study_models import StudyEvent
from research.fill_external_price_gap import ProviderAttempt, _rows_from_databento_frame, run_fill
from research.massive_price_backfill import HistoricalPriceRow
from research.price_dataset import resolve_price_dataset_path


def _write_base_prices(path: Path) -> None:
    table = pa.table(
        {
            "Date": [date(2024, 1, 2)],
            "Ticker": ["AAPL"],
            "Open": [100.0],
            "High": [101.0],
            "Low": [99.0],
            "Close": [100.5],
            "Volume": [1000.0],
            "Dividends": [0.0],
            "Stock Splits": [0.0],
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path, compression="snappy")


class ExternalPriceGapFillTests(unittest.TestCase):
    def test_rows_from_databento_frame_normalizes_rows(self) -> None:
        class _FakeTimestamp:
            def __init__(self, year: int, month: int, day: int) -> None:
                self._date = date(year, month, day)

            def date(self):
                return self._date

        class _FakeFrame:
            empty = False

            def iterrows(self):
                yield _FakeTimestamp(2024, 1, 2), {"open": 10.0, "high": 11.0, "low": 9.5, "close": 10.5, "volume": 1000}
                yield _FakeTimestamp(2024, 1, 3), {"open": 10.6, "high": 11.1, "low": 10.2, "close": 10.9, "volume": 1200}

        rows = _rows_from_databento_frame(_FakeFrame(), "ba")

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].ticker, "BA")
        self.assertEqual(rows[0].trade_date, "2024-01-02")
        self.assertEqual(rows[1].close, 10.9)

    def test_run_fill_writes_enriched_dataset_on_first_successful_provider(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repo_root = root / "ui"
            prices_dir = root / "data" / "prices"
            repo_root.mkdir(parents=True, exist_ok=True)
            _write_base_prices(prices_dir / "all_stock_data_extended.parquet")

            study_events = [
                StudyEvent(
                    id="evt-ttm-1",
                    ticker="TTM",
                    category="Macro Event",
                    timestamp=datetime(2025, 2, 3, 14, 0, tzinfo=timezone.utc),
                )
            ]
            provided_rows = [
                HistoricalPriceRow("2025-02-03", "TTM", 25.0, 26.0, 24.5, 25.5, 1000.0),
                HistoricalPriceRow("2025-02-04", "TTM", 25.5, 26.2, 25.1, 25.9, 1100.0),
            ]

            def provider_one(_repo_root, _ticker, _start, _end):
                return [], ProviderAttempt("massive_rest", "no_rows", 0, "No rows")

            def provider_two(_repo_root, _ticker, _start, _end):
                return provided_rows, ProviderAttempt("alpaca", "success", 2, "Rows found", "2025-02-03", "2025-02-04")

            with patch("research.fill_external_price_gap._load_study_events", return_value=study_events), patch(
                "research.fill_external_price_gap._iter_provider_fetchers",
                return_value=(provider_one, provider_two),
            ):
                report = run_fill(
                    repo_root,
                    price_file=None,
                    ticker_overrides=["TTM"],
                    load_supabase=False,
                    bootstrap_daily_prices_schema=False,
                    dry_run=False,
                )

            self.assertEqual(report.tickers_filled, ("TTM",))
            self.assertEqual(report.total_rows_added, 2)
            resolved = resolve_price_dataset_path(repo_root, allow_sample_fallback=False)
            self.assertEqual(resolved.resolution_reason, "default_enriched_parquet")
            self.assertTrue(Path(report.enriched_parquet_path or "").exists())

    def test_run_fill_reports_unresolved_when_no_provider_returns_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repo_root = root / "ui"
            prices_dir = root / "data" / "prices"
            repo_root.mkdir(parents=True, exist_ok=True)
            _write_base_prices(prices_dir / "all_stock_data_extended.parquet")

            study_events = [
                StudyEvent(
                    id="evt-ttm-1",
                    ticker="TTM",
                    category="Macro Event",
                    timestamp=datetime(2025, 2, 3, 14, 0, tzinfo=timezone.utc),
                )
            ]

            def provider_one(_repo_root, _ticker, _start, _end):
                return [], ProviderAttempt("massive_rest", "no_rows", 0, "No rows")

            def provider_two(_repo_root, _ticker, _start, _end):
                return [], ProviderAttempt("alpaca", "restricted", 0, "Provider restricted")

            with patch("research.fill_external_price_gap._load_study_events", return_value=study_events), patch(
                "research.fill_external_price_gap._iter_provider_fetchers",
                return_value=(provider_one, provider_two),
            ):
                report = run_fill(
                    repo_root,
                    price_file=None,
                    ticker_overrides=["TTM"],
                    load_supabase=False,
                    bootstrap_daily_prices_schema=False,
                    dry_run=True,
                )

            self.assertEqual(report.tickers_unresolved, ("TTM",))
            self.assertEqual(report.total_rows_added, 0)
            self.assertEqual(report.results[0].attempts[1].status, "restricted")


if __name__ == "__main__":
    unittest.main()
