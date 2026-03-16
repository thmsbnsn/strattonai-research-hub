from __future__ import annotations

import unittest

from ingestion.map_sec_filing_to_event import map_sec_filing_to_event_payload
from ingestion.normalize import normalize_event_record


class EntityExpansionTests(unittest.TestCase):
    def test_nvda_product_launch_infers_tsm_and_amd(self) -> None:
        event = normalize_event_record(
            {
                "source_name": "test_case",
                "source_record_id": "nvda-product-launch-no-explicit",
                "headline": "NVIDIA unveils new Blackwell AI platform",
                "primary_ticker": "NVDA",
                "event_type": "product_launch",
                "sentiment": "positive",
                "occurred_at": "2026-03-13T08:32:00Z",
                "details": "The launch expands hyperscale AI deployment.",
                "related_companies": [],
                "metadata": {},
            }
        )

        related_tickers = [related.target_ticker for related in event.related_companies]
        self.assertEqual(related_tickers[:2], ["TSM", "AMD"])

    def test_tsla_supply_disruption_infers_competitor_and_supplier(self) -> None:
        event = normalize_event_record(
            {
                "source_name": "test_case",
                "source_record_id": "tsla-supply-disruption-no-explicit",
                "headline": "Tesla halts production after supplier shortage",
                "primary_ticker": "TSLA",
                "event_type": "supply_disruption",
                "sentiment": "negative",
                "occurred_at": "2026-03-13T06:45:00Z",
                "details": "Production was interrupted after a battery component shortage.",
                "related_companies": [],
                "metadata": {},
            }
        )

        related_tickers = {related.target_ticker for related in event.related_companies}
        self.assertIn("RIVN", related_tickers)
        self.assertIn("PANW", related_tickers)

    def test_lly_regulatory_approval_infers_nvo_from_graph(self) -> None:
        event = normalize_event_record(
            map_sec_filing_to_event_payload(
                {
                    "accession_number": "000594918-26-entity-test",
                    "form_type": "8-K",
                    "filing_date": "2026-03-15",
                    "company_name": "Eli Lilly and Company",
                    "ticker": "LLY",
                    "headline": "Eli Lilly discloses positive regulatory approval update",
                    "summary": "The company reported an approval milestone for an obesity treatment.",
                    "extracted_tags": ["approval"],
                    "metadata": {"filing_sections": ["Item 8.01"]},
                }
            )
        )

        related_tickers = [related.target_ticker for related in event.related_companies]
        self.assertIn("NVO", related_tickers)

    def test_explicit_related_companies_are_not_duplicated(self) -> None:
        event = normalize_event_record(
            {
                "source_name": "test_case",
                "source_record_id": "nvda-explicit-amd",
                "headline": "NVIDIA launches updated inference systems",
                "primary_ticker": "NVDA",
                "event_type": "product_launch",
                "sentiment": "positive",
                "occurred_at": "2026-03-13T09:00:00Z",
                "details": "The launch affects competitive AI hardware markets.",
                "related_companies": [
                    {"ticker": "AMD", "name": "AMD", "relationship": "Competitor", "strength": 0.9}
                ],
                "metadata": {},
            }
        )

        amd_rows = [related for related in event.related_companies if related.target_ticker == "AMD"]
        self.assertEqual(len(amd_rows), 1)
        self.assertEqual(amd_rows[0].origin_type, "explicit")

    def test_entity_expansion_is_deterministic(self) -> None:
        payload = {
            "source_name": "test_case",
            "source_record_id": "deterministic-tsla",
            "headline": "Tesla reports supply disruption at a major facility",
            "primary_ticker": "TSLA",
            "event_type": "supply_disruption",
            "sentiment": "negative",
            "occurred_at": "2026-03-13T10:00:00Z",
            "details": "The event affects several suppliers and competitors.",
            "related_companies": [],
            "metadata": {},
        }

        first = normalize_event_record(payload)
        second = normalize_event_record(payload)

        self.assertEqual(
            [(related.target_ticker, related.relationship, related.origin_type) for related in first.related_companies],
            [(related.target_ticker, related.relationship, related.origin_type) for related in second.related_companies],
        )


if __name__ == "__main__":
    unittest.main()
