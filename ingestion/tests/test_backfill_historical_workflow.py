from __future__ import annotations

import unittest
from pathlib import Path

from ingestion.run_ingestion import load_records, normalize_records


class HistoricalBackfillWorkflowTests(unittest.TestCase):
    def test_historical_market_backfill_is_stable_and_unique(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        records = load_records("market-events", str(repo_root / "ingestion" / "sample_historical_events.json"))
        first_pass, failures = normalize_records("market-events", records)
        second_pass, second_failures = normalize_records("market-events", records)

        self.assertFalse(failures)
        self.assertFalse(second_failures)
        self.assertGreaterEqual(len(first_pass), 20)
        self.assertEqual([event.id for event in first_pass], [event.id for event in second_pass])
        self.assertEqual(len({event.id for event in first_pass}), len(first_pass))

    def test_historical_sec_backfill_is_stable_and_unique(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        records = load_records("sec-filings", str(repo_root / "ingestion" / "sample_historical_sec_filings.json"))
        first_pass, failures = normalize_records("sec-filings", records)
        second_pass, second_failures = normalize_records("sec-filings", records)

        self.assertFalse(failures)
        self.assertFalse(second_failures)
        self.assertGreaterEqual(len(first_pass), 6)
        self.assertEqual([event.id for event in first_pass], [event.id for event in second_pass])
        self.assertEqual(len({event.id for event in first_pass}), len(first_pass))

    def test_targeted_wave_market_backfill_is_stable_and_unique(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        records = load_records("market-events", str(repo_root / "ingestion" / "targeted_expansion_wave_market_events.json"))
        first_pass, failures = normalize_records("market-events", records)
        second_pass, second_failures = normalize_records("market-events", records)

        self.assertFalse(failures)
        self.assertFalse(second_failures)
        self.assertGreaterEqual(len(first_pass), 8)
        self.assertEqual([event.id for event in first_pass], [event.id for event in second_pass])
        self.assertEqual(len({event.id for event in first_pass}), len(first_pass))

    def test_targeted_wave_sec_backfill_is_stable_and_unique(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        records = load_records("sec-filings", str(repo_root / "ingestion" / "targeted_expansion_wave_sec_filings.json"))
        first_pass, failures = normalize_records("sec-filings", records)
        second_pass, second_failures = normalize_records("sec-filings", records)

        self.assertFalse(failures)
        self.assertFalse(second_failures)
        self.assertGreaterEqual(len(first_pass), 10)
        self.assertEqual([event.id for event in first_pass], [event.id for event in second_pass])
        self.assertEqual(len({event.id for event in first_pass}), len(first_pass))

    def test_precision_wave_market_backfill_is_stable_and_unique(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        records = load_records("market-events", str(repo_root / "ingestion" / "targeted_expansion_wave_precision_market_events.json"))
        first_pass, failures = normalize_records("market-events", records)
        second_pass, second_failures = normalize_records("market-events", records)

        self.assertFalse(failures)
        self.assertFalse(second_failures)
        self.assertGreaterEqual(len(first_pass), 3)
        self.assertEqual([event.id for event in first_pass], [event.id for event in second_pass])
        self.assertEqual(len({event.id for event in first_pass}), len(first_pass))

    def test_precision_wave_sec_backfill_is_stable_and_unique(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        records = load_records("sec-filings", str(repo_root / "ingestion" / "targeted_expansion_wave_precision_sec_filings.json"))
        first_pass, failures = normalize_records("sec-filings", records)
        second_pass, second_failures = normalize_records("sec-filings", records)

        self.assertFalse(failures)
        self.assertFalse(second_failures)
        self.assertGreaterEqual(len(first_pass), 3)
        self.assertEqual([event.id for event in first_pass], [event.id for event in second_pass])
        self.assertEqual(len({event.id for event in first_pass}), len(first_pass))


if __name__ == "__main__":
    unittest.main()
