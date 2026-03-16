from __future__ import annotations

import unittest

from research.low_confidence_diagnostics import (
    build_low_confidence_diagnostics_report,
    build_low_confidence_diff,
    build_signal_record,
)


class LowConfidenceDiagnosticsTests(unittest.TestCase):
    def test_sparse_exact_coverage_is_flagged_for_fallback_heavy_slice(self) -> None:
        records = [
            build_signal_record(
                event_category="Legal/Regulatory",
                primary_ticker="AAPL",
                target_ticker="GOOGL",
                target_type="related",
                relationship_type="Sector Peer",
                horizon="5D",
                confidence_band="Low",
                sample_size=10,
                avg_return="1.2000",
                median_return="1.0000",
                win_rate="58.0000",
                score="32.0000",
                rationale={
                    "study": {"study_target_type": "relationship"},
                    "scoring": {"components": {"consistency_rate": "58", "recency_multiplier": "0.96"}},
                },
            ),
            build_signal_record(
                event_category="Legal/Regulatory",
                primary_ticker="MSFT",
                target_ticker="GOOGL",
                target_type="related",
                relationship_type="Sector Peer",
                horizon="10D",
                confidence_band="Low",
                sample_size=10,
                avg_return="1.3000",
                median_return="1.1000",
                win_rate="59.0000",
                score="33.0000",
                rationale={
                    "study": {"study_target_type": "relationship"},
                    "scoring": {"components": {"consistency_rate": "59", "recency_multiplier": "0.96"}},
                },
            ),
        ]
        plan = {"plan_items": [{"source_gap_key": "related::Legal/Regulatory::GOOGL::Sector Peer", "gap_size": 1}]}

        report = build_low_confidence_diagnostics_report(
            records,
            plan=plan,
            focus_slice_keys=("related::Legal/Regulatory::GOOGL::Sector Peer",),
        )
        focus = report["focus_slices"]["related::Legal/Regulatory::GOOGL::Sector Peer"]

        self.assertIn("sparse_exact_coverage", focus["dominant_causes"])
        self.assertIn("relationship_sparsity", focus["dominant_causes"])
        self.assertTrue(focus["can_improve_with_depth"])

    def test_weak_edge_is_flagged_when_returns_are_small(self) -> None:
        records = [
            build_signal_record(
                event_category="Product Launch",
                primary_ticker="NVDA",
                target_ticker="NVDA",
                target_type="primary",
                relationship_type=None,
                horizon="5D",
                confidence_band="Low",
                sample_size=8,
                avg_return="0.2000",
                median_return="0.1000",
                win_rate="53.0000",
                score="25.0000",
                rationale={
                    "study": {"study_target_type": "primary"},
                    "scoring": {"components": {"consistency_rate": "53", "recency_multiplier": "0.92"}},
                },
            )
        ]

        report = build_low_confidence_diagnostics_report(records)
        top_slice = report["top_low_confidence_slices"][0]

        self.assertIn("weak_edge", top_slice["dominant_causes"])
        self.assertIn("weak_win_rate", top_slice["dominant_causes"])

    def test_low_confidence_diff_reports_category_changes(self) -> None:
        before = {
            "category_summaries": [
                {"event_category": "Product Launch", "low_count": 40, "moderate_count": 5, "high_count": 1, "low_ratio": 0.8696, "dominant_causes": ["sparse_exact_coverage"]},
            ],
            "focus_slices": {
                "related::Product Launch::GOOGL::Competitor": {
                    "low_count": 20,
                    "average_sample_size": 5,
                    "dominant_causes": ["sparse_exact_coverage"],
                }
            },
        }
        after = {
            "category_summaries": [
                {"event_category": "Product Launch", "low_count": 32, "moderate_count": 10, "high_count": 2, "low_ratio": 0.7273, "dominant_causes": ["thin_sample_depth"]},
            ],
            "focus_slices": {
                "related::Product Launch::GOOGL::Competitor": {
                    "low_count": 12,
                    "average_sample_size": 6,
                    "dominant_causes": ["thin_sample_depth"],
                }
            },
            "efficient_upgrade_candidates": [],
        }

        diff = build_low_confidence_diff(before, after)

        self.assertEqual(diff["category_changes"][0]["low_delta"], -8)
        self.assertIn("related::Product Launch::GOOGL::Competitor", diff["focus_slice_changes"])
        self.assertEqual(diff["exact_slice_changes"][0]["slice_key"], "related::Product Launch::GOOGL::Competitor")
        self.assertEqual(diff["exact_slice_changes"][0]["low_delta"], -8)


if __name__ == "__main__":
    unittest.main()
