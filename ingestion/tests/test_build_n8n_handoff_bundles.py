from __future__ import annotations

import unittest

from ingestion.build_n8n_handoff_bundles import build_handoff_bundles


class BuildN8nHandoffBundlesTest(unittest.TestCase):
    def test_builds_market_and_sec_bundles_from_approved_examples(self) -> None:
        review_bundle = {
            "research_slices": [
                {
                    "source_gap_key": "related::Product Launch::AMD::Competitor",
                    "review_status": "approved_for_ingestion",
                    "reviewer_notes": "Approved.",
                    "event_category": "Product Launch",
                    "target_type": "related_company",
                    "primary_ticker": "NVDA",
                    "related_ticker": "AMD",
                    "relationship_type": "Competitor",
                    "suggested_source_type": "market-events",
                    "collected_examples": [
                        {
                            "source_name": "press_release",
                            "source_record_id": "nvda-launch-2026-01-01",
                            "source_url": "https://example.test/nvda",
                            "source_title": "NVIDIA unveils new platform",
                            "source_publisher": "Example",
                            "published_at": "2026-01-01T12:00:00Z",
                            "occurred_at": "2026-01-01T12:00:00Z",
                            "headline": "NVIDIA launches new platform",
                            "summary": "Launch summary.",
                            "primary_ticker": "NVDA",
                            "related_companies": [
                                {
                                    "ticker": "AMD",
                                    "name": "Advanced Micro Devices",
                                    "relationship": "Competitor",
                                    "strength": 0.8,
                                }
                            ],
                            "event_type_hint": "Product Launch",
                            "sentiment_hint": "positive",
                            "relationship_evidence": "Competitor context is explicit.",
                            "extraction_notes": "Reviewed manually.",
                            "evidence_quote": "launches",
                            "evidence_confidence": "high",
                            "duplicate_check_key": "press_release|nvda-launch-2026-01-01|NVDA|Product Launch|2026-01-01T12:00:00Z",
                            "ready_for_ingestion": True,
                        }
                    ],
                },
                {
                    "source_gap_key": "related::Partnership::MSFT::Customer",
                    "review_status": "approved_for_ingestion",
                    "reviewer_notes": "Approved.",
                    "event_category": "Partnership",
                    "target_type": "relationship_slice",
                    "primary_ticker": "NVDA",
                    "related_ticker": "MSFT",
                    "relationship_type": "Customer",
                    "suggested_source_type": "sec-filings",
                    "collected_examples": [
                        {
                            "source_name": "sec_edgar_public_submissions",
                            "source_record_id": "0001326801-26-000041",
                            "source_url": "https://www.sec.gov/Archives/edgar/data/1045810/000132680126000041/d123.htm",
                            "source_title": "NVIDIA Corporation 8-K",
                            "source_publisher": "SEC EDGAR",
                            "published_at": "2026-03-12T00:00:00Z",
                            "occurred_at": "2026-03-12T00:00:00Z",
                            "headline": "NVIDIA Corporation 8-K partnership filing",
                            "summary": "Filing summary.",
                            "primary_ticker": "NVDA",
                            "related_companies": [
                                {
                                    "ticker": "MSFT",
                                    "name": "Microsoft Corporation",
                                    "relationship": "Customer",
                                    "strength": 0.72,
                                }
                            ],
                            "event_type_hint": "Partnership",
                            "sentiment_hint": "neutral",
                            "relationship_evidence": "Customer path is explicit.",
                            "extraction_notes": "Reviewed manually.",
                            "evidence_quote": "8-K",
                            "evidence_confidence": "high",
                            "duplicate_check_key": "sec_edgar_public_submissions|0001326801-26-000041|NVDA|Partnership|2026-03-12T00:00:00Z",
                            "ready_for_ingestion": True,
                        }
                    ],
                },
            ]
        }

        market_bundle, sec_bundle, report = build_handoff_bundles(review_bundle)

        self.assertEqual(report["market_event_count"], 1)
        self.assertEqual(report["sec_filing_count"], 1)

        market_event = market_bundle["events"][0]
        self.assertEqual(market_event["source_name"], "press_release")
        self.assertEqual(market_event["event_type"], "Product Launch")
        self.assertEqual(market_event["sentiment"], "positive")
        self.assertEqual(market_event["related_companies"][0]["ticker"], "AMD")

        filing = sec_bundle["filings"][0]
        self.assertEqual(filing["accession_number"], "0001326801-26-000041")
        self.assertEqual(filing["form_type"], "8-K")
        self.assertEqual(filing["ticker"], "NVDA")
        self.assertEqual(filing["related_tickers"][0]["ticker"], "MSFT")

    def test_excludes_pending_review_by_default(self) -> None:
        review_bundle = {
            "research_slices": [
                {
                    "source_gap_key": "related::Legal/Regulatory::GOOGL::Sector Peer",
                    "review_status": "pending_review",
                    "reviewer_notes": "",
                    "event_category": "Legal/Regulatory",
                    "target_type": "related_company",
                    "primary_ticker": "META",
                    "related_ticker": "GOOGL",
                    "relationship_type": "Sector Peer",
                    "suggested_source_type": "sec-filings",
                    "collected_examples": [
                        {
                            "source_name": "sec_edgar_public_submissions",
                            "source_record_id": "0000000000-26-000001",
                            "primary_ticker": "META",
                            "source_title": "Meta Platforms 8-K",
                            "published_at": "2026-03-12T00:00:00Z",
                            "duplicate_check_key": "dup-1",
                            "ready_for_ingestion": True,
                        }
                    ],
                }
            ]
        }

        market_bundle, sec_bundle, report = build_handoff_bundles(review_bundle)
        self.assertEqual(report["market_event_count"], 0)
        self.assertEqual(report["sec_filing_count"], 0)
        self.assertEqual(market_bundle["events"], [])
        self.assertEqual(sec_bundle["filings"], [])

    def test_dedupes_by_duplicate_check_key(self) -> None:
        example = {
            "source_name": "press_release",
            "source_record_id": "same-id",
            "source_title": "Duplicate example",
            "primary_ticker": "NVDA",
            "published_at": "2026-01-01T00:00:00Z",
            "duplicate_check_key": "same-key",
            "ready_for_ingestion": True,
        }
        review_bundle = {
            "research_slices": [
                {
                    "source_gap_key": "gap-1",
                    "review_status": "approved_for_ingestion",
                    "reviewer_notes": "",
                    "event_category": "Product Launch",
                    "target_type": "primary_exact",
                    "primary_ticker": "NVDA",
                    "related_ticker": None,
                    "relationship_type": None,
                    "suggested_source_type": "market-events",
                    "collected_examples": [example, dict(example)],
                }
            ]
        }

        market_bundle, sec_bundle, report = build_handoff_bundles(review_bundle)
        self.assertEqual(report["market_event_count"], 1)
        self.assertEqual(len(market_bundle["events"]), 1)
        self.assertEqual(sec_bundle["filings"], [])


if __name__ == "__main__":
    unittest.main()
