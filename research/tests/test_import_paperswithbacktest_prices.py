from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from research.import_paperswithbacktest_prices import run_import


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


def _write_source_shard(path: Path) -> None:
    table = pa.table(
        {
            "symbol": ["AAPL", "AAPL", "TSLA", "MSFT"],
            "date": ["2024-01-02", "2024-01-03", "2024-01-03", "2024-01-03"],
            "open": [100.0, 101.0, 200.0, 300.0],
            "high": [101.0, 102.0, 201.0, 301.0],
            "low": [99.0, 100.0, 198.0, 299.0],
            "close": [100.5, 101.5, 205.0, 0.0],
            "volume": [1000.0, 1100.0, 5000.0, 7000.0],
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path, compression="snappy")


class PapersWithBacktestImportTests(unittest.TestCase):
    def test_dry_run_reports_incremental_rows_for_selected_tickers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repo_root = root / "ui"
            prices_dir = root / "data" / "prices"
            source_dir = root / "source"
            repo_root.mkdir(parents=True, exist_ok=True)
            _write_base_prices(prices_dir / "all_stock_data_extended.parquet")
            _write_source_shard(source_dir / "train-00000-of-00001.parquet")

            report = run_import(
                repo_root,
                source_dir=str(source_dir),
                price_file=None,
                ticker_overrides=["AAPL", "TSLA"],
                dry_run=True,
            )

        self.assertEqual(report.source_rows_matched, 3)
        self.assertEqual(report.new_rows_added, 2)
        self.assertEqual(report.tickers_with_new_rows, ("AAPL", "TSLA"))
        self.assertEqual(report.tickers_without_source_rows, ())


if __name__ == "__main__":
    unittest.main()
