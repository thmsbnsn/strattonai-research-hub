from __future__ import annotations

import json
import unittest
from pathlib import Path


class PrecisionWaveSelectionTests(unittest.TestCase):
    def test_precision_wave_targets_current_top_gap_keys_and_macro_primarys(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        market_payload = json.loads(
            (repo_root / "ingestion" / "targeted_expansion_wave_precision_market_events.json").read_text(encoding="utf-8")
        )
        sec_payload = json.loads(
            (repo_root / "ingestion" / "targeted_expansion_wave_precision_sec_filings.json").read_text(encoding="utf-8")
        )

        targeted_gap_keys = set()
        for record in market_payload.get("events", []):
            targeted_gap_keys.update(record.get("metadata", {}).get("targeted_gap_keys", []))
        for record in sec_payload.get("filings", []):
            targeted_gap_keys.update(record.get("metadata", {}).get("targeted_gap_keys", []))

        expected_keys = {
            "primary::Macro Event::AAPL",
            "primary::Macro Event::NVDA",
            "related::Capital Expenditure::ORCL::Sector Peer",
            "related::Capital Expenditure::AMZN::Competitor",
            "related::Legal/Regulatory::GOOGL::Sector Peer",
            "related::Legal/Regulatory::META::Sector Peer",
            "related::Partnership::TSM::Supplier",
            "related::Partnership::MSFT::Customer",
            "related::Partnership::AVGO::Sector Peer",
            "related::Product Launch::GOOGL::Competitor",
        }

        self.assertTrue(expected_keys.issubset(targeted_gap_keys))


if __name__ == "__main__":
    unittest.main()
