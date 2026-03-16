from __future__ import annotations

import unittest

from ingestion.classify_event import ClassificationInput, classify_event
from ingestion.map_sec_filing_to_event import map_sec_filing_to_event_payload
from ingestion.normalize import normalize_event_record


class EventClassifierTests(unittest.TestCase):
    def assertClassification(
        self,
        *,
        category: str,
        sentiment: str,
        input_data: ClassificationInput,
    ) -> None:
        result = classify_event(input_data)
        self.assertEqual(result.category, category)
        self.assertEqual(result.sentiment, sentiment)
        self.assertTrue(result.matched_rules)

    def test_nvda_product_launch_is_positive(self) -> None:
        self.assertClassification(
            category="Product Launch",
            sentiment="positive",
            input_data=ClassificationInput(
                source_name="manual_seed",
                event_type_hint="product_launch",
                sentiment_hint="bullish",
                headline="NVIDIA announces next-gen AI training chips with 2x performance",
                summary="The company unveiled its new platform at GTC.",
                extracted_tags=("chip launch",),
                form_type=None,
                metadata={},
            ),
        )

    def test_lly_approval_is_positive(self) -> None:
        self.assertClassification(
            category="Regulatory Approval",
            sentiment="positive",
            input_data=ClassificationInput(
                source_name="manual_seed",
                event_type_hint="approval",
                sentiment_hint=None,
                headline="FDA approves Eli Lilly therapy for expanded indications",
                summary="Formal approval broadens the addressable market.",
                extracted_tags=("fda approval",),
                form_type=None,
                metadata={},
            ),
        )

    def test_tsla_supply_disruption_is_negative(self) -> None:
        self.assertClassification(
            category="Supply Disruption",
            sentiment="negative",
            input_data=ClassificationInput(
                source_name="manual_seed",
                event_type_hint="supply chain disruption",
                sentiment_hint=None,
                headline="Tesla halts output after supply chain shortage",
                summary="The company reported production issues tied to a parts shortage.",
                extracted_tags=("supply chain", "shortage"),
                form_type=None,
                metadata={},
            ),
        )

    def test_aapl_antitrust_is_negative(self) -> None:
        self.assertClassification(
            category="Legal/Regulatory",
            sentiment="negative",
            input_data=ClassificationInput(
                source_name="sec_filing",
                event_type_hint=None,
                sentiment_hint=None,
                headline="Apple discloses antitrust filing and expanded legal proceedings in Europe",
                summary="The company faces additional regulatory review.",
                extracted_tags=("litigation", "regulatory"),
                form_type="8-K",
                metadata={"source_type": "sec_filing"},
            ),
        )

    def test_ambiguous_eight_k_defaults_to_macro_event(self) -> None:
        result = classify_event(
            ClassificationInput(
                source_name="sec_filing",
                event_type_hint=None,
                sentiment_hint=None,
                headline="Issuer files current report on Form 8-K",
                summary="The company furnished a general corporate update.",
                extracted_tags=(),
                form_type="8-K",
                metadata={"source_type": "sec_filing"},
            )
        )

        self.assertEqual(result.category, "Macro Event")
        self.assertEqual(result.sentiment, "neutral")
        self.assertIn("source_hint:sec_filing:8-k->Macro Event", result.matched_rules)

    def test_sec_mapping_flows_into_normalized_classification_metadata(self) -> None:
        normalized = normalize_event_record(
            map_sec_filing_to_event_payload(
                {
                    "accession_number": "0000789019-26-000057",
                    "form_type": "8-K",
                    "filing_date": "2026-03-17",
                    "company_name": "Microsoft Corporation",
                    "ticker": "MSFT",
                    "headline": "Microsoft announces datacenter campus acquisition and expanded capital program",
                    "summary": "The filing outlines a datacenter campus acquisition and broader capital investment program.",
                    "extracted_tags": ["acquisition", "capital expenditure", "facility expansion"],
                    "metadata": {"filing_sections": ["Item 8.01"]},
                }
            )
        )

        self.assertEqual(normalized.category, "Capital Expenditure")
        self.assertEqual(normalized.sentiment, "positive")
        self.assertEqual(normalized.metadata["classification"]["category"], "Capital Expenditure")
        self.assertTrue(normalized.metadata["classification"]["matched_rules"])


if __name__ == "__main__":
    unittest.main()
