from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research.fill_external_price_gap import ExternalPriceGapFillReport, TickerGapFillResult
from research.fill_study_universe_gaps import run_gap_fill


class _FakeTradingRepository:
    def __init__(self, _repo_root: Path):
        self.counts = {"AAPL": 100, "TTM": 10}

    def distinct_event_tickers(self):
        return ["AAPL", "TTM"]

    def count_daily_price_rows(self, ticker: str) -> int:
        return self.counts.get(ticker, 0)


class FillStudyUniverseGapsTests(unittest.TestCase):
    def test_run_gap_fill_attempts_only_undercovered_tickers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "research.fill_study_universe_gaps.TradingRepository",
            _FakeTradingRepository,
        ), patch(
            "research.fill_study_universe_gaps.run_fill",
            return_value=ExternalPriceGapFillReport(
                base_price_path="base.parquet",
                base_price_format="parquet",
                enriched_parquet_path=None,
                enriched_csv_path=None,
                backfill_parquet_path="backfill.parquet",
                backfill_csv_path="backfill.csv",
                target_tickers=("TTM",),
                tickers_filled=(),
                tickers_unresolved=("TTM",),
                total_rows_added=0,
                cumulative_backfill_rows=0,
                previous_price_max_date="2026-03-01",
                new_price_max_date="2026-03-01",
                supabase_rows_upserted=0,
                results=(
                    TickerGapFillResult(
                        ticker="TTM",
                        start_date="2025-01-01",
                        end_date="2025-03-01",
                        selected_provider=None,
                        rows_found=0,
                        rows_added=0,
                        attempts=(),
                    ),
                ),
                completed_at="2026-03-16T00:00:00+00:00",
            ),
        ):
            report = run_gap_fill(Path(temp_dir), min_rows=60, price_file=None, dry_run=True, auto_recompute=False)

        self.assertEqual(report.tickers_attempted, ("TTM",))
        self.assertEqual(report.tickers_still_missing, ("TTM",))

    def test_run_gap_fill_triggers_recompute_modules_when_requested(self) -> None:
        repository = _FakeTradingRepository(Path("."))

        def _successful_fill(*args, **kwargs):
            repository.counts["TTM"] = 120
            return ExternalPriceGapFillReport(
                base_price_path="base.parquet",
                base_price_format="parquet",
                enriched_parquet_path=None,
                enriched_csv_path=None,
                backfill_parquet_path="backfill.parquet",
                backfill_csv_path="backfill.csv",
                target_tickers=("TTM",),
                tickers_filled=("TTM",),
                tickers_unresolved=(),
                total_rows_added=10,
                cumulative_backfill_rows=10,
                previous_price_max_date="2026-03-01",
                new_price_max_date="2026-03-16",
                supabase_rows_upserted=10,
                results=(),
                completed_at="2026-03-16T00:00:00+00:00",
            )

        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "research.fill_study_universe_gaps.TradingRepository",
            return_value=repository,
        ), patch(
            "research.fill_study_universe_gaps.run_fill",
            side_effect=_successful_fill,
        ), patch(
            "research.fill_study_universe_gaps._run_module"
        ) as run_module:
            report = run_gap_fill(Path(temp_dir), min_rows=60, price_file="prices.parquet", dry_run=False, auto_recompute=True)

        self.assertEqual(report.tickers_successfully_filled, ("TTM",))
        self.assertEqual(run_module.call_count, 3)


if __name__ == "__main__":
    unittest.main()
