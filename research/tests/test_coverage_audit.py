from __future__ import annotations

import unittest

from research.coverage_audit import (
    aggregate_confidence_bands_by_category,
    detect_missing_price_history,
    detect_sparse_study_slices,
    identify_weak_signal_categories,
)
from research.coverage_models import (
    CoverageEvent,
    CoverageRelationshipEdge,
    CoverageRelatedCompany,
    CoverageSignal,
    CoverageStudyStatistic,
)


class CoverageAuditTests(unittest.TestCase):
    def test_confidence_band_aggregation_is_grouped_by_category(self) -> None:
        signals = [
            CoverageSignal("Product Launch", "NVDA", "NVDA", "primary", None, "5D", "High", "primary"),
            CoverageSignal("Product Launch", "NVDA", "TSM", "related", "Supplier", "5D", "Moderate", "related"),
            CoverageSignal("Macro Event", "MSFT", "MSFT", "primary", None, "5D", "Low", "category_summary"),
        ]

        distribution = aggregate_confidence_bands_by_category(signals)
        self.assertEqual(distribution["Product Launch"].high, 1)
        self.assertEqual(distribution["Product Launch"].moderate, 1)
        self.assertEqual(distribution["Macro Event"].low, 1)

    def test_sparse_slice_detection_flags_primary_fallbacks(self) -> None:
        events = [
            CoverageEvent(id="evt-1", source_name="manual_seed", ticker="MSFT", category="Macro Event"),
        ]
        related_companies: list[CoverageRelatedCompany] = []
        studies = [
            CoverageStudyStatistic(
                study_key="category_summary||Macro Event||ANY||ANY||ANY||5D",
                study_target_type="category_summary",
                event_category="Macro Event",
                horizon="5D",
                sample_size=2,
            ),
        ]
        signals = [
            CoverageSignal(
                event_category="Macro Event",
                primary_ticker="MSFT",
                target_ticker="MSFT",
                target_type="primary",
                relationship_type=None,
                horizon="5D",
                confidence_band="Low",
                source_study_target_type="category_summary",
            )
        ]

        primary_gaps, related_gaps, relationship_gaps = detect_sparse_study_slices(studies, events, related_companies, signals)
        self.assertTrue(primary_gaps)
        self.assertFalse(related_gaps)
        self.assertFalse(relationship_gaps)
        self.assertEqual(primary_gaps[0].ticker, "MSFT")
        self.assertGreater(primary_gaps[0].fallback_usage_count, 0)

    def test_missing_price_history_detection_flags_short_series(self) -> None:
        events = [CoverageEvent(id="evt-1", source_name="manual_seed", ticker="NVO", category="Regulatory Approval")]
        related_companies = [
            CoverageRelatedCompany(
                event_id="evt-1",
                source_ticker="LLY",
                target_ticker="NVO",
                relationship_type="Competitor",
                origin_type="explicit",
            )
        ]
        graph = [
            CoverageRelationshipEdge(source_ticker="LLY", target_ticker="NVO", relationship_type="Competitor", strength=0.8)
        ]

        gaps = detect_missing_price_history(
            events,
            related_companies,
            graph,
            {"NVO": 18},
            required_days=40,
        )
        self.assertTrue(any(gap.ticker == "NVO" for gap in gaps))

    def test_gap_ranking_for_weak_categories_is_stable(self) -> None:
        signals = [
            CoverageSignal("Macro Event", "MSFT", "MSFT", "primary", None, "5D", "Low", "category_summary"),
            CoverageSignal("Macro Event", "MSFT", "GOOGL", "related", "Sector Peer", "5D", "Low", "relationship"),
            CoverageSignal("Product Launch", "NVDA", "NVDA", "primary", None, "5D", "High", "primary"),
        ]

        weak_categories = identify_weak_signal_categories(signals)
        self.assertEqual([item.event_category for item in weak_categories], ["Macro Event"])
        self.assertAlmostEqual(weak_categories[0].high_confidence_ratio, 0.0)

    def test_sparse_related_slice_aggregates_sample_size_across_primaries(self) -> None:
        events = [
            CoverageEvent(id="evt-1", source_name="sec_filing", ticker="MSFT", category="Capital Expenditure"),
            CoverageEvent(id="evt-2", source_name="sec_filing", ticker="GOOGL", category="Capital Expenditure"),
        ]
        related_companies = [
            CoverageRelatedCompany(
                event_id="evt-1",
                source_ticker="MSFT",
                target_ticker="ORCL",
                relationship_type="Sector Peer",
                origin_type="explicit",
            ),
            CoverageRelatedCompany(
                event_id="evt-2",
                source_ticker="GOOGL",
                target_ticker="ORCL",
                relationship_type="Sector Peer",
                origin_type="explicit",
            ),
        ]
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
        ]
        signals: list[CoverageSignal] = []

        _primary_gaps, related_gaps, _relationship_gaps = detect_sparse_study_slices(
            studies,
            events,
            related_companies,
            signals,
        )
        orcl_gap = next(gap for gap in related_gaps if gap.ticker == "ORCL")
        self.assertEqual(orcl_gap.current_sample_size, 5)
        self.assertEqual(orcl_gap.missing_horizons, ("3D", "5D", "10D", "20D"))


if __name__ == "__main__":
    unittest.main()
