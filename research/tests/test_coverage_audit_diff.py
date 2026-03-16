from __future__ import annotations

import unittest

from research.coverage_audit_diff import (
    build_comparison_markdown,
    build_comparison_summary,
    build_snapshot_from_studies_and_signals,
)
from research.coverage_models import CoverageSignal, CoverageStudyStatistic


class CoverageAuditDiffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.before_report = {
            "event_counts_by_category": {
                "Macro Event": 2,
                "Capital Expenditure": 7,
                "Legal/Regulatory": 9,
                "Partnership": 7,
            },
            "confidence_band_distribution_by_category": {
                "Macro Event": {"high": 0, "moderate": 18, "low": 27},
                "Capital Expenditure": {"high": 9, "moderate": 27, "low": 104},
            },
            "top_gap_candidates": [
                {
                    "candidate_key": "related::Capital Expenditure::ORCL::Sector Peer",
                    "required_additional_examples": 5,
                    "rationale": "Capital Expenditure related slice for ORCL is thin.",
                }
            ],
        }
        self.after_report = {
            "event_counts_by_category": {
                "Macro Event": 6,
                "Capital Expenditure": 12,
                "Legal/Regulatory": 13,
                "Partnership": 12,
            },
            "confidence_band_distribution_by_category": {
                "Macro Event": {"high": 1, "moderate": 25, "low": 18},
                "Capital Expenditure": {"high": 14, "moderate": 35, "low": 108},
            },
            "top_gap_candidates": [
                {
                    "candidate_key": "related::Product Launch::QCOM::Supplier",
                    "required_additional_examples": 2,
                    "rationale": "Product Launch related slice for QCOM still needs more depth.",
                }
            ],
        }
        self.before_snapshot = {
            "total_events": 48,
            "detailed_study_rows": 795,
            "ui_summary_rows": 40,
            "signal_count": 865,
            "confidence_bands": {"High": 9, "Moderate": 166, "Low": 690},
            "focused_related_slices": {
                "Capital Expenditure::ORCL::Sector Peer": {
                    "event_category": "Capital Expenditure",
                    "related_ticker": "ORCL",
                    "relationship_type": "Sector Peer",
                    "horizon_count": 0,
                    "min_sample_size": 0,
                },
                "Capital Expenditure::AMZN::Competitor": {
                    "event_category": "Capital Expenditure",
                    "related_ticker": "AMZN",
                    "relationship_type": "Competitor",
                    "horizon_count": 0,
                    "min_sample_size": 0,
                },
                "Legal/Regulatory::GOOGL::Sector Peer": {
                    "event_category": "Legal/Regulatory",
                    "related_ticker": "GOOGL",
                    "relationship_type": "Sector Peer",
                    "horizon_count": 5,
                    "min_sample_size": 1,
                },
                "Legal/Regulatory::META::Sector Peer": {
                    "event_category": "Legal/Regulatory",
                    "related_ticker": "META",
                    "relationship_type": "Sector Peer",
                    "horizon_count": 5,
                    "min_sample_size": 2,
                },
                "Partnership::TSM::Supplier": {
                    "event_category": "Partnership",
                    "related_ticker": "TSM",
                    "relationship_type": "Supplier",
                    "horizon_count": 0,
                    "min_sample_size": 0,
                },
            },
            "focused_primary_slices": {
                "Macro Event::MSFT": {
                    "event_category": "Macro Event",
                    "primary_ticker": "MSFT",
                    "horizon_count": 5,
                    "min_sample_size": 1,
                },
                "Macro Event::NVDA": {
                    "event_category": "Macro Event",
                    "primary_ticker": "NVDA",
                    "horizon_count": 5,
                    "min_sample_size": 1,
                },
            },
        }
        self.after_snapshot = {
            "total_events": 66,
            "detailed_study_rows": 1040,
            "ui_summary_rows": 40,
            "signal_count": 1115,
            "confidence_bands": {"High": 22, "Moderate": 244, "Low": 849},
            "focused_related_slices": {
                "Capital Expenditure::ORCL::Sector Peer": {
                    "event_category": "Capital Expenditure",
                    "related_ticker": "ORCL",
                    "relationship_type": "Sector Peer",
                    "horizon_count": 5,
                    "min_sample_size": 5,
                },
                "Capital Expenditure::AMZN::Competitor": {
                    "event_category": "Capital Expenditure",
                    "related_ticker": "AMZN",
                    "relationship_type": "Competitor",
                    "horizon_count": 5,
                    "min_sample_size": 5,
                },
                "Legal/Regulatory::GOOGL::Sector Peer": {
                    "event_category": "Legal/Regulatory",
                    "related_ticker": "GOOGL",
                    "relationship_type": "Sector Peer",
                    "horizon_count": 5,
                    "min_sample_size": 5,
                },
                "Legal/Regulatory::META::Sector Peer": {
                    "event_category": "Legal/Regulatory",
                    "related_ticker": "META",
                    "relationship_type": "Sector Peer",
                    "horizon_count": 5,
                    "min_sample_size": 5,
                },
                "Partnership::TSM::Supplier": {
                    "event_category": "Partnership",
                    "related_ticker": "TSM",
                    "relationship_type": "Supplier",
                    "horizon_count": 5,
                    "min_sample_size": 5,
                },
            },
            "focused_primary_slices": {
                "Macro Event::MSFT": {
                    "event_category": "Macro Event",
                    "primary_ticker": "MSFT",
                    "horizon_count": 5,
                    "min_sample_size": 3,
                },
                "Macro Event::NVDA": {
                    "event_category": "Macro Event",
                    "primary_ticker": "NVDA",
                    "horizon_count": 5,
                    "min_sample_size": 2,
                },
            },
        }

    def test_comparison_summary_tracks_focused_slice_improvement(self) -> None:
        summary = build_comparison_summary(
            self.before_report,
            self.after_report,
            self.before_snapshot,
            self.after_snapshot,
        )

        self.assertEqual(summary["total_events"]["delta"], 18)
        self.assertEqual(summary["macro_event_depth"]["event_count_after"], 6)
        self.assertEqual(
            summary["focused_related_slices"]["Capital Expenditure::ORCL::Sector Peer"]["delta_sample_size"],
            5,
        )

    def test_markdown_output_mentions_remaining_gaps(self) -> None:
        summary = build_comparison_summary(
            self.before_report,
            self.after_report,
            self.before_snapshot,
            self.after_snapshot,
        )
        markdown = build_comparison_markdown(summary)

        self.assertIn("Coverage Audit Diff", markdown)
        self.assertIn("Capital Expenditure::ORCL::Sector Peer", markdown)
        self.assertIn("related::Product Launch::QCOM::Supplier", markdown)

    def test_snapshot_builder_aggregates_related_slice_sample_size_across_primaries(self) -> None:
        report = {
            "event_counts_by_category": {"Capital Expenditure": 4},
        }
        studies = [
            CoverageStudyStatistic(
                study_key="related||Capital Expenditure||MSFT||ORCL||Sector Peer||1D",
                study_target_type="related",
                event_category="Capital Expenditure",
                primary_ticker="MSFT",
                related_ticker="ORCL",
                relationship_type="Sector Peer",
                horizon="1D",
                sample_size=2,
            ),
            CoverageStudyStatistic(
                study_key="related||Capital Expenditure||GOOGL||ORCL||Sector Peer||1D",
                study_target_type="related",
                event_category="Capital Expenditure",
                primary_ticker="GOOGL",
                related_ticker="ORCL",
                relationship_type="Sector Peer",
                horizon="1D",
                sample_size=3,
            ),
            CoverageStudyStatistic(
                study_key="primary||Macro Event||MSFT||ANY||ANY||1D",
                study_target_type="primary",
                event_category="Macro Event",
                primary_ticker="MSFT",
                horizon="1D",
                sample_size=2,
            ),
        ]
        signals = [
            CoverageSignal("Capital Expenditure", "MSFT", "ORCL", "related", "Sector Peer", "1D", "Moderate", "related"),
            CoverageSignal("Macro Event", "MSFT", "MSFT", "primary", None, "1D", "Low", "primary"),
        ]

        snapshot = build_snapshot_from_studies_and_signals(report, studies, signals)
        orcl_slice = snapshot["focused_related_slices"]["Capital Expenditure::ORCL::Sector Peer"]

        self.assertEqual(snapshot["signal_count"], 2)
        self.assertEqual(orcl_slice["horizon_count"], 1)
        self.assertEqual(orcl_slice["min_sample_size"], 5)


if __name__ == "__main__":
    unittest.main()
