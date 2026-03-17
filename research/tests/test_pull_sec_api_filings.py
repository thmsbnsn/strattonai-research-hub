from __future__ import annotations

import unittest

from research.pull_sec_api_filings import _build_query, _normalize_filing


class PullSecApiFilingsTests(unittest.TestCase):
    def test_build_query_includes_ticker_forms_and_date_range(self) -> None:
        query = _build_query("NVDA", ("8-K", "10-Q", "10-K"), "2025-01-01", "2026-03-17")
        self.assertIn("ticker:NVDA", query)
        self.assertIn('formType:"8-K"', query)
        self.assertIn("filedAt:[2025-01-01 TO 2026-03-17]", query)

    def test_normalize_filing_maps_query_payload_to_ingestion_shape(self) -> None:
        filing = _normalize_filing(
            {
                "accessionNo": "0001045810-26-000024",
                "formType": "8-K",
                "filedAt": "2026-03-06T16:11:25-05:00",
                "ticker": "NVDA",
                "companyName": "NVIDIA CORP",
                "description": "Form 8-K - Current report - Item 5.02 Item 9.01",
                "linkToTxt": "https://www.sec.gov/Archives/example.txt",
                "items": ["Item 5.02: Departure of Directors", "Item 9.01: Financial Statements and Exhibits"],
                "entities": [{"cik": "1045810"}],
                "dataFiles": [{"type": "EX-101.SCH"}],
            }
        )

        self.assertEqual(filing.accession_number, "0001045810-26-000024")
        self.assertEqual(filing.form_type, "8-K")
        self.assertEqual(filing.filing_date, "2026-03-06")
        self.assertEqual(filing.ticker, "NVDA")
        self.assertTrue(any("departure of directors" in tag for tag in filing.extracted_tags))
        self.assertEqual(filing.metadata["link_to_txt"], "https://www.sec.gov/Archives/example.txt")


if __name__ == "__main__":
    unittest.main()
