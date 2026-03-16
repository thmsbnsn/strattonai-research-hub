from __future__ import annotations

from pathlib import Path
import unittest

from ingestion.run_ingestion import load_records, normalize_records


class PrecisionQualityWaveTests(unittest.TestCase):
    def test_wave_inputs_normalize_without_failures_and_keep_stable_ids(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        market_input = repo_root / "ingestion" / "targeted_expansion_wave_quality_market_events.json"
        sec_input = repo_root / "ingestion" / "targeted_expansion_wave_quality_sec_filings.json"

        first_market_events, first_market_failures = normalize_records("market-events", load_records("market-events", str(market_input)))
        second_market_events, second_market_failures = normalize_records("market-events", load_records("market-events", str(market_input)))
        first_sec_events, first_sec_failures = normalize_records("sec-filings", load_records("sec-filings", str(sec_input)))
        second_sec_events, second_sec_failures = normalize_records("sec-filings", load_records("sec-filings", str(sec_input)))

        self.assertEqual(len(first_market_failures), 0)
        self.assertEqual(len(second_market_failures), 0)
        self.assertEqual(len(first_sec_failures), 0)
        self.assertEqual(len(second_sec_failures), 0)

        self.assertEqual([event.id for event in first_market_events], [event.id for event in second_market_events])
        self.assertEqual([event.id for event in first_sec_events], [event.id for event in second_sec_events])
        self.assertEqual(len({event.source_record_id for event in [*first_market_events, *first_sec_events]}), len(first_market_events) + len(first_sec_events))


if __name__ == "__main__":
    unittest.main()
