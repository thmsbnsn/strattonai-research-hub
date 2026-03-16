from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from research.price_dataset import resolve_price_dataset_path


class PriceDatasetResolverTests(unittest.TestCase):
    def test_explicit_override_wins(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "ui"
            repo_root.mkdir(parents=True, exist_ok=True)
            explicit = repo_root / "custom_prices.json"
            explicit.write_text("{}", encoding="utf-8")

            resolved = resolve_price_dataset_path(repo_root, explicit)

        self.assertEqual(resolved.path, explicit.resolve())
        self.assertEqual(resolved.format, "json")
        self.assertEqual(resolved.resolution_reason, "explicit_override")

    def test_default_prefers_parquet_before_csv(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "ui"
            data_dir = repo_root.parent / "data" / "prices"
            data_dir.mkdir(parents=True, exist_ok=True)
            parquet_path = data_dir / "all_stock_data.parquet"
            csv_path = data_dir / "all_stock_data.csv"
            parquet_path.write_text("parquet", encoding="utf-8")
            csv_path.write_text("csv", encoding="utf-8")

            resolved = resolve_price_dataset_path(repo_root)

        self.assertEqual(resolved.path, parquet_path.resolve())
        self.assertEqual(resolved.format, "parquet")
        self.assertEqual(resolved.resolution_reason, "default_parquet")

    def test_default_prefers_extended_parquet_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "ui"
            data_dir = repo_root.parent / "data" / "prices"
            data_dir.mkdir(parents=True, exist_ok=True)
            extended_path = data_dir / "all_stock_data_extended.parquet"
            base_path = data_dir / "all_stock_data.parquet"
            extended_path.write_text("extended", encoding="utf-8")
            base_path.write_text("base", encoding="utf-8")

            resolved = resolve_price_dataset_path(repo_root)

        self.assertEqual(resolved.path, extended_path.resolve())
        self.assertEqual(resolved.format, "parquet")
        self.assertEqual(resolved.resolution_reason, "default_extended_parquet")

    def test_csv_fallback_is_used_when_parquet_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "ui"
            data_dir = repo_root.parent / "data" / "prices"
            data_dir.mkdir(parents=True, exist_ok=True)
            csv_path = data_dir / "all_stock_data.csv"
            csv_path.write_text("Date,Ticker,Close\n2026-01-05,NVDA,100\n", encoding="utf-8")

            resolved = resolve_price_dataset_path(repo_root)

        self.assertEqual(resolved.path, csv_path.resolve())
        self.assertEqual(resolved.format, "csv")
        self.assertEqual(resolved.resolution_reason, "default_csv")

    def test_sample_json_is_last_resort(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "ui"
            sample_path = repo_root / "research" / "sample_extended_price_series.json"
            sample_path.parent.mkdir(parents=True, exist_ok=True)
            sample_path.write_text("{}", encoding="utf-8")

            resolved = resolve_price_dataset_path(repo_root)

        self.assertEqual(resolved.path, sample_path.resolve())
        self.assertEqual(resolved.format, "json")
        self.assertTrue(resolved.used_sample_fallback)


if __name__ == "__main__":
    unittest.main()
