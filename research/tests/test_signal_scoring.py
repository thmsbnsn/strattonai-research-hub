from __future__ import annotations

import unittest
from datetime import datetime, timezone
from decimal import Decimal

from research.signal_models import SignalEvent, SignalRelatedCompany, SignalStudyStatistic
from research.signal_scoring import build_signal_key, compute_signal_score, index_studies, score_event_signals


class SignalScoringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 3, 13, 12, 0, tzinfo=timezone.utc)
        self.event = SignalEvent(
            id="evt-1",
            ticker="NVDA",
            category="Product Launch",
            timestamp=datetime(2026, 3, 13, 8, 30, tzinfo=timezone.utc),
            headline="NVDA launches next-gen AI platform",
            sentiment="positive",
            classifier_confidence="High",
            classifier_rationale={"confidence": "High", "matched_rules": ["alias:product_launch"]},
            related_companies=(
                SignalRelatedCompany(
                    target_ticker="TSM",
                    relationship_type="Supplier",
                    origin_type="explicit",
                    rationale={"origin": "explicit"},
                ),
                SignalRelatedCompany(
                    target_ticker="AMD",
                    relationship_type="Competitor",
                    origin_type="inferred",
                    rationale={"origin": "inferred"},
                ),
            ),
        )

    def test_strong_score_for_well_supported_pattern(self) -> None:
        study = SignalStudyStatistic(
            study_key="primary||Product Launch||NVDA||ANY||ANY||5D",
            study_target_type="primary",
            event_category="Product Launch",
            primary_ticker="NVDA",
            related_ticker=None,
            relationship_type=None,
            horizon="5D",
            sample_size=18,
            avg_return=Decimal("3.2000"),
            median_return=Decimal("2.6000"),
            win_rate=Decimal("68.0000"),
            notes="Primary ticker study.",
            metadata={},
        )
        score = compute_signal_score(
            event=self.event,
            study=study,
            target_ticker="NVDA",
            target_type="primary",
            relationship_type=None,
            origin_type="primary",
            now=self.now,
        )
        self.assertGreaterEqual(score.score, Decimal("80"))
        self.assertEqual(score.confidence_band, "High")

    def test_weaker_score_for_low_sample_size(self) -> None:
        study = SignalStudyStatistic(
            study_key="primary||Product Launch||NVDA||ANY||ANY||1D",
            study_target_type="primary",
            event_category="Product Launch",
            primary_ticker="NVDA",
            related_ticker=None,
            relationship_type=None,
            horizon="1D",
            sample_size=3,
            avg_return=Decimal("1.1000"),
            median_return=Decimal("0.6000"),
            win_rate=Decimal("55.0000"),
            notes="Small sample.",
            metadata={},
        )
        score = compute_signal_score(
            event=self.event,
            study=study,
            target_ticker="NVDA",
            target_type="primary",
            relationship_type=None,
            origin_type="primary",
            now=self.now,
        )
        self.assertLess(score.score, Decimal("35"))
        self.assertEqual(score.confidence_band, "Low")

    def test_penalty_for_inferred_relationship(self) -> None:
        study = SignalStudyStatistic(
            study_key="relationship||Product Launch||ANY||ANY||Competitor||5D",
            study_target_type="relationship",
            event_category="Product Launch",
            primary_ticker=None,
            related_ticker=None,
            relationship_type="Competitor",
            horizon="5D",
            sample_size=12,
            avg_return=Decimal("2.1000"),
            median_return=Decimal("1.8000"),
            win_rate=Decimal("62.0000"),
            notes="Competitor study.",
            metadata={},
        )
        explicit_score = compute_signal_score(
            event=self.event,
            study=study,
            target_ticker="TSM",
            target_type="related",
            relationship_type="Competitor",
            origin_type="explicit",
            now=self.now,
        )
        inferred_score = compute_signal_score(
            event=self.event,
            study=study,
            target_ticker="AMD",
            target_type="related",
            relationship_type="Competitor",
            origin_type="inferred",
            now=self.now,
        )
        self.assertGreater(explicit_score.score, inferred_score.score)

    def test_stable_signal_key_for_reruns(self) -> None:
        first = build_signal_key("evt-1", "related", "TSM", "Supplier", "5D")
        second = build_signal_key("evt-1", "related", "TSM", "Supplier", "5D")
        self.assertEqual(first, second)

    def test_missing_study_statistics_are_skipped_gracefully(self) -> None:
        primary_study = SignalStudyStatistic(
            study_key="primary||Product Launch||NVDA||ANY||ANY||5D",
            study_target_type="primary",
            event_category="Product Launch",
            primary_ticker="NVDA",
            related_ticker=None,
            relationship_type=None,
            horizon="5D",
            sample_size=10,
            avg_return=Decimal("2.5000"),
            median_return=Decimal("2.0000"),
            win_rate=Decimal("65.0000"),
            notes="Primary study.",
            metadata={},
        )
        studies = index_studies([primary_study])
        signals = score_event_signals(self.event, studies, now=self.now)
        self.assertTrue(any(signal.target_type == "primary" for signal in signals))
        self.assertFalse(any(signal.target_ticker == "TSM" for signal in signals))

    def test_score_strength_increases_with_deeper_evidence(self) -> None:
        thin_study = SignalStudyStatistic(
            study_key="primary||Product Launch||NVDA||ANY||ANY||3D",
            study_target_type="primary",
            event_category="Product Launch",
            primary_ticker="NVDA",
            related_ticker=None,
            relationship_type=None,
            horizon="3D",
            sample_size=3,
            avg_return=Decimal("1.3000"),
            median_return=Decimal("1.1000"),
            win_rate=Decimal("55.0000"),
            notes="Thin evidence.",
            metadata={},
        )
        deep_study = SignalStudyStatistic(
            study_key="primary||Product Launch||NVDA||ANY||ANY||3D",
            study_target_type="primary",
            event_category="Product Launch",
            primary_ticker="NVDA",
            related_ticker=None,
            relationship_type=None,
            horizon="3D",
            sample_size=8,
            avg_return=Decimal("2.2000"),
            median_return=Decimal("1.9000"),
            win_rate=Decimal("66.0000"),
            notes="Deeper evidence.",
            metadata={},
        )
        thin_score = compute_signal_score(
            event=self.event,
            study=thin_study,
            target_ticker="NVDA",
            target_type="primary",
            relationship_type=None,
            origin_type="primary",
            now=self.now,
        )
        deep_score = compute_signal_score(
            event=self.event,
            study=deep_study,
            target_ticker="NVDA",
            target_type="primary",
            relationship_type=None,
            origin_type="primary",
            now=self.now,
        )
        self.assertGreater(deep_score.score, thin_score.score)
        self.assertEqual(deep_score.confidence_band, "Moderate")


if __name__ == "__main__":
    unittest.main()
