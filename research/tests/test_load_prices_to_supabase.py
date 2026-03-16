from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from research.load_prices_to_supabase import run_load


def _write_price_parquet(path: Path) -> None:
    table = pa.table(
        {
            "Date": [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)],
            "Ticker": ["aapl", "AAPL", "msft"],
            "Open": [100.0, 101.0, 200.0],
            "High": [101.0, 102.0, 201.0],
            "Low": [99.0, 100.0, 199.0],
            "Close": [100.5, 0.0, None],
            "Volume": [1000, 1100, 1200],
            "Dividends": [0.0, 0.0, 0.0],
            "Stock Splits": [0.0, 0.0, 0.0],
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path, compression="snappy")


class LoadPricesToSupabaseTests(unittest.TestCase):
    def test_dry_run_skips_zero_or_null_close_and_uppercases_tickers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repo_root = root / "ui"
            prices_dir = root / "data" / "prices"
            repo_root.mkdir(parents=True, exist_ok=True)
            prices_dir.mkdir(parents=True, exist_ok=True)
            _write_price_parquet(prices_dir / "all_stock_data_extended.parquet")

            summary = run_load(
                repo_root,
                price_file=None,
                bootstrap_schema=False,
                schema_file=str(repo_root / "supabase" / "sql" / "008_add_daily_prices.sql"),
                ticker_filters=[],
                study_universe=False,
                dry_run=True,
            )

            self.assertEqual(summary.total_rows_read, 3)
            self.assertEqual(summary.rows_skipped, 2)
            self.assertEqual(summary.rows_upserted, 1)
            self.assertEqual(summary.tickers_loaded, ("AAPL",))
            self.assertTrue((repo_root / "reports" / "daily_prices_load.json").exists())

    def test_dry_run_respects_ticker_filter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repo_root = root / "ui"
            prices_dir = root / "data" / "prices"
            repo_root.mkdir(parents=True, exist_ok=True)
            prices_dir.mkdir(parents=True, exist_ok=True)
            _write_price_parquet(prices_dir / "all_stock_data_extended.parquet")

            summary = run_load(
                repo_root,
                price_file=None,
                bootstrap_schema=False,
                schema_file=str(repo_root / "supabase" / "sql" / "008_add_daily_prices.sql"),
                ticker_filters=["MSFT"],
                study_universe=False,
                dry_run=True,
            )

            self.assertEqual(summary.total_rows_read, 1)
            self.assertEqual(summary.rows_skipped, 1)
            self.assertEqual(summary.rows_upserted, 0)
            self.assertEqual(summary.tickers_loaded, ())

    def test_dry_run_merges_explicit_tickers_with_study_universe(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repo_root = root / "ui"
            prices_dir = root / "data" / "prices"
            repo_root.mkdir(parents=True, exist_ok=True)
            prices_dir.mkdir(parents=True, exist_ok=True)
            _write_price_parquet(prices_dir / "all_stock_data_extended.parquet")

            from unittest.mock import patch

            with patch("research.load_prices_to_supabase.collect_study_tickers", return_value={"AAPL"}), patch(
                "research.load_prices_to_supabase.EventStudySupabaseWriter"
            ) as writer_cls:
                writer_cls.return_value.load_study_events.return_value = ["stub"]
                summary = run_load(
                    repo_root,
                    price_file=None,
                    bootstrap_schema=False,
                    schema_file=str(repo_root / "supabase" / "sql" / "008_add_daily_prices.sql"),
                    ticker_filters=["MSFT"],
                    study_universe=True,
                    dry_run=True,
                )

            self.assertEqual(summary.total_rows_read, 3)
            self.assertEqual(summary.rows_skipped, 2)
            self.assertEqual(summary.rows_upserted, 1)
            self.assertEqual(summary.tickers_loaded, ("AAPL",))


if __name__ == "__main__":
    unittest.main()
