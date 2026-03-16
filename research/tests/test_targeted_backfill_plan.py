from __future__ import annotations

import unittest

from research.build_targeted_backfill_plan import build_targeted_backfill_plan
from research.export_backfill_templates import build_backfill_templates


class TargetedBackfillPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.audit_report = {
            "weak_signal_categories": [
                {
                    "event_category": "Macro Event",
                    "high": 0,
                    "moderate": 2,
                    "low": 10,
                    "gap_score": 40.0,
                },
                {
                    "event_category": "Product Launch",
                    "high": 0,
                    "moderate": 6,
                    "low": 12,
                    "gap_score": 30.0,
                },
            ],
            "top_gap_candidates": [
                {
                    "candidate_key": "related::Capital Expenditure::ORCL::Sector Peer",
                    "gap_score": 110.0,
                    "event_category": "Capital Expenditure",
                    "target_type": "related",
                    "ticker": "ORCL",
                    "relationship_type": "Sector Peer",
                    "required_additional_examples": 5,
                    "rationale": "Capital Expenditure related slice for ORCL / Sector Peer has sample 0, missing horizons ['1D'], fallback usage 30, signal usage 30.",
                },
                {
                    "candidate_key": "related::Product Launch::AMD::Competitor",
                    "gap_score": 85.0,
                    "event_category": "Product Launch",
                    "target_type": "related",
                    "ticker": "AMD",
                    "relationship_type": "Competitor",
                    "required_additional_examples": 4,
                    "rationale": "Product Launch related slice for AMD / Competitor has sample 1, missing horizons [], fallback usage 10, signal usage 10.",
                },
            ],
            "notes": {"price_file": "sample_extended_price_series.json"},
        }

    def test_plan_ranking_is_stable(self) -> None:
        first = build_targeted_backfill_plan(self.audit_report, limit=5)
        second = build_targeted_backfill_plan(self.audit_report, limit=5)
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.plan_items[0].related_ticker, "ORCL")

    def test_macro_category_item_is_added_when_missing_from_top_candidates(self) -> None:
        plan = build_targeted_backfill_plan(self.audit_report, limit=5)
        self.assertTrue(any(item.event_category == "Macro Event" for item in plan.plan_items))

    def test_grouping_by_source_type_and_category_is_correct(self) -> None:
        plan = build_targeted_backfill_plan(self.audit_report, limit=5)
        group_keys = {group.group_key for group in plan.groups}
        self.assertIn("sec-filings::Capital Expenditure", group_keys)
        self.assertIn("market-events::Product Launch", group_keys)

    def test_template_generation_splits_market_and_sec_items(self) -> None:
        plan = build_targeted_backfill_plan(self.audit_report, limit=5)
        market_template, sec_template = build_backfill_templates(plan.to_dict())
        self.assertEqual(market_template["template_metadata"]["count"], 2)
        self.assertEqual(sec_template["template_metadata"]["count"], 1)
        self.assertIn("notes_to_research", market_template["events"][0]["metadata"])
        self.assertIn("notes_to_research", sec_template["filings"][0]["metadata"])


if __name__ == "__main__":
    unittest.main()
