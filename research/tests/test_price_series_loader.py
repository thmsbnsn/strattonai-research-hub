from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ingestion.load_price_series_file import inspect_price_series_file, load_price_series_file

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
except ImportError:  # pragma: no cover - dependency enforced in workflow
    pa = None
    pq = None


class PriceSeriesLoaderTests(unittest.TestCase):
    def test_segment_based_series_expands_deterministically(self) -> None:
        payload = {
            "date_range": {"start": "2026-01-05", "end": "2026-01-09"},
            "series": [
                {
                    "ticker": "NVDA",
                    "start_close": 100,
                    "segments": [
                        {"days": 2, "daily_move": 1.5},
                        {"days": 2, "daily_move": -0.5},
                    ],
                }
            ],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "prices.json"
            file_path.write_text(json.dumps(payload), encoding="utf-8")
            series = load_price_series_file(file_path)

        self.assertEqual(len(series), 1)
        self.assertEqual(series[0].ticker, "NVDA")
        self.assertEqual([float(point.close) for point in series[0].prices], [100.0, 101.5, 103.0, 102.5, 102.0])

    def test_csv_loader_supports_ticker_filter(self) -> None:
        payload = "\n".join(
            [
                "Date,Ticker,Open,High,Low,Close,Volume,Dividends,Stock Splits",
                "2026-01-05,NVDA,0,0,0,100,0,0,0",
                "2026-01-05,AMD,0,0,0,50,0,0,0",
                "2026-01-06,NVDA,0,0,0,102,0,0,0",
            ]
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "prices.csv"
            file_path.write_text(payload, encoding="utf-8")
            series = load_price_series_file(file_path, tickers={"NVDA"})

        self.assertEqual(len(series), 1)
        self.assertEqual(series[0].ticker, "NVDA")
        self.assertEqual([point.date.isoformat() for point in series[0].prices], ["2026-01-05", "2026-01-06"])

    @unittest.skipUnless(pa is not None and pq is not None, "pyarrow is required for parquet loader tests")
    def test_parquet_loader_matches_csv_parity_for_representative_sample(self) -> None:
        rows = {
            "Date": [date_str for date_str in ("2026-01-05", "2026-01-06", "2026-01-05", "2026-01-06")],
            "Ticker": ["NVDA", "NVDA", "AMD", "AMD"],
            "Close": [100.0, 102.0, 50.0, 51.0],
            "Open": [0.0, 0.0, 0.0, 0.0],
            "High": [0.0, 0.0, 0.0, 0.0],
            "Low": [0.0, 0.0, 0.0, 0.0],
            "Volume": [0.0, 0.0, 0.0, 0.0],
            "Dividends": [0.0, 0.0, 0.0, 0.0],
            "Stock Splits": [0.0, 0.0, 0.0, 0.0],
        }
        csv_payload = "\n".join(
            [
                "Date,Ticker,Open,High,Low,Close,Volume,Dividends,Stock Splits",
                "2026-01-05,NVDA,0,0,0,100,0,0,0",
                "2026-01-06,NVDA,0,0,0,102,0,0,0",
                "2026-01-05,AMD,0,0,0,50,0,0,0",
                "2026-01-06,AMD,0,0,0,51,0,0,0",
            ]
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            csv_path = temp_path / "prices.csv"
            parquet_path = temp_path / "prices.parquet"
            csv_path.write_text(csv_payload, encoding="utf-8")
            pq.write_table(pa.table(rows), parquet_path)

            csv_series = load_price_series_file(csv_path, tickers={"NVDA", "AMD"})
            parquet_series = load_price_series_file(parquet_path, tickers={"NVDA", "AMD"})
            csv_inspection = inspect_price_series_file(csv_path)
            parquet_inspection = inspect_price_series_file(parquet_path)

        self.assertEqual(
            [(series.ticker, [(point.date.isoformat(), float(point.close)) for point in series.prices]) for series in csv_series],
            [(series.ticker, [(point.date.isoformat(), float(point.close)) for point in series.prices]) for series in parquet_series],
        )
        self.assertEqual(csv_inspection.row_count, parquet_inspection.row_count)
        self.assertEqual(csv_inspection.distinct_ticker_count, parquet_inspection.distinct_ticker_count)
        self.assertEqual(csv_inspection.min_date, parquet_inspection.min_date)
        self.assertEqual(csv_inspection.max_date, parquet_inspection.max_date)


if __name__ == "__main__":
    unittest.main()
