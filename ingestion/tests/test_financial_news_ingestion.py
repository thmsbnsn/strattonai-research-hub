from __future__ import annotations

import unittest

from ingestion.map_financial_news_to_event import (
    FinancialNewsMappingError,
    get_financial_news_company_mapping_decision,
    map_financial_news_to_event_payload,
    resolve_financial_news_company_ticker,
)
from ingestion.normalize import normalize_event_record
from ingestion.run_ingestion import normalize_records_with_diagnostics


class FinancialNewsIngestionTests(unittest.TestCase):
    def test_company_mapping_is_deterministic(self) -> None:
        self.assertEqual(resolve_financial_news_company_ticker("Microsoft"), "MSFT")
        self.assertEqual(resolve_financial_news_company_ticker("JP Morgan Chase"), "JPM")
        self.assertEqual(resolve_financial_news_company_ticker("Tata Motors"), "TTM")
        self.assertIsNone(resolve_financial_news_company_ticker("Samsung Electronics"))
        self.assertIsNone(resolve_financial_news_company_ticker("Reliance Industries"))

    def test_mapping_decision_explains_supported_and_unsupported_names(self) -> None:
        tata = get_financial_news_company_mapping_decision("Tata Motors")
        samsung = get_financial_news_company_mapping_decision("Samsung Electronics")

        self.assertEqual(tata.ticker, "TTM")
        self.assertEqual(tata.strategy, "nyse_adr")
        self.assertFalse(samsung.is_supported)
        self.assertIn("canonical foreign-listing convention", samsung.notes)

    def test_source_record_id_is_stable_for_reruns(self) -> None:
        row = {
            "Date": "2025-03-02",
            "Headline": "Tech Giant's New Product Launch Sparks Sector-Wide Gains",
            "Source": "Barron's",
            "Market_Event": "IPO Launch",
            "Sentiment": "Neutral",
            "Sector": "Telecommunications",
            "Impact_Level": "Medium",
            "Related_Company": "Microsoft",
        }
        first = map_financial_news_to_event_payload(row, 7)
        second = map_financial_news_to_event_payload(row, 7)

        self.assertEqual(first["source_name"], "financial_news_local")
        self.assertEqual(first["source_record_id"], second["source_record_id"])

    def test_product_launch_headline_maps_through_shared_classifier(self) -> None:
        row = {
            "Date": "2025-03-02",
            "Headline": "Tech Giant's New Product Launch Sparks Sector-Wide Gains",
            "Source": "Barron's",
            "Market_Event": "IPO Launch",
            "Sentiment": "Positive",
            "Sector": "Technology",
            "Impact_Level": "High",
            "Related_Company": "Microsoft",
        }

        normalized = normalize_event_record(map_financial_news_to_event_payload(row, 1))
        self.assertEqual(normalized.ticker, "MSFT")
        self.assertEqual(normalized.category, "Product Launch")
        self.assertEqual(normalized.sentiment, "positive")

    def test_breach_headline_maps_to_legal_regulatory(self) -> None:
        row = {
            "Date": "2025-04-05",
            "Headline": "A massive data breach sends a tech company's stock tumbling",
            "Source": "Wall Street Journal",
            "Market_Event": "Geopolitical Event",
            "Sentiment": "Negative",
            "Sector": "Technology",
            "Impact_Level": "High",
            "Related_Company": "Apple Inc.",
        }

        normalized = normalize_event_record(map_financial_news_to_event_payload(row, 4))
        self.assertEqual(normalized.ticker, "AAPL")
        self.assertEqual(normalized.category, "Legal/Regulatory")
        self.assertEqual(normalized.sentiment, "negative")

    def test_supply_chain_headline_maps_to_supply_disruption(self) -> None:
        row = {
            "Date": "2025-04-28",
            "Headline": "Supply chain shutdown forces aerospace production halt",
            "Source": "The Economist",
            "Market_Event": "Government Policy Announcement",
            "Sentiment": "Neutral",
            "Sector": "Healthcare",
            "Impact_Level": "High",
            "Related_Company": "Boeing",
        }

        normalized = normalize_event_record(map_financial_news_to_event_payload(row, 9))
        self.assertEqual(normalized.ticker, "BA")
        self.assertEqual(normalized.category, "Supply Disruption")

    def test_unmapped_company_is_skipped_instead_of_guessed(self) -> None:
        row = {
            "Date": "2025-05-21",
            "Headline": "Nikkei 225 index benefits from a weaker yen",
            "Source": "Times of India",
            "Market_Event": "Commodity Price Shock",
            "Sentiment": "",
            "Sector": "Technology",
            "Impact_Level": "High",
            "Related_Company": "Samsung Electronics",
        }

        with self.assertRaises(FinancialNewsMappingError) as error:
            map_financial_news_to_event_payload(row, 1)
        self.assertIn("canonical foreign-listing convention", str(error.exception))

    def test_tata_motors_maps_through_shared_classifier(self) -> None:
        row = {
            "Date": "2025-06-17",
            "Headline": "Automaker signs an electric commercial vehicle software partnership to scale fleet deployments",
            "Source": "Reuters",
            "Market_Event": "Government Policy Announcement",
            "Sentiment": "Positive",
            "Sector": "Automotive",
            "Impact_Level": "Medium",
            "Related_Company": "Tata Motors",
        }

        normalized = normalize_event_record(map_financial_news_to_event_payload(row, 3))
        self.assertEqual(normalized.ticker, "TTM")
        self.assertEqual(normalized.category, "Partnership")
        self.assertEqual(normalized.sentiment, "positive")

    def test_batch_normalization_skips_unsupported_rows_without_failing_the_run(self) -> None:
        records = [
            {
                "Date": "2025-03-02",
                "Headline": "Tech Giant's New Product Launch Sparks Sector-Wide Gains",
                "Source": "Barron's",
                "Market_Event": "IPO Launch",
                "Sentiment": "Positive",
                "Sector": "Technology",
                "Impact_Level": "High",
                "Related_Company": "Microsoft",
            },
            {
                "Date": "2025-05-21",
                "Headline": "Nikkei 225 index benefits from a weaker yen",
                "Source": "Times of India",
                "Market_Event": "Commodity Price Shock",
                "Sentiment": "",
                "Sector": "Technology",
                "Impact_Level": "High",
                "Related_Company": "Samsung Electronics",
            },
        ]

        normalized, failures, skipped = normalize_records_with_diagnostics(
            "financial-news",
            records,
            log_each_record=False,
        )

        self.assertEqual(len(normalized), 1)
        self.assertEqual(len(failures), 0)
        self.assertEqual(len(skipped), 1)
        self.assertIn("Unsupported Related_Company mapping", skipped[0].reason)


if __name__ == "__main__":
    unittest.main()
