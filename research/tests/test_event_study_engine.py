from __future__ import annotations

import unittest
from datetime import date, datetime, timezone
from decimal import Decimal

from research.compute_forward_returns import align_event_to_trading_index, compute_close_to_close_forward_return
from research.event_study_engine import aggregate_observations, build_price_map, compute_event_study_observations
from research.event_study_models import ForwardReturnObservation, PricePoint, PriceSeries, StudyEvent, StudyRelatedCompany


class EventStudyEngineTests(unittest.TestCase):
    def test_forward_return_calculation_is_correct(self) -> None:
        series = PriceSeries(
            ticker="NVDA",
            prices=(
                PricePoint(date(2026, 3, 13), Decimal("100")),
                PricePoint(date(2026, 3, 16), Decimal("105")),
                PricePoint(date(2026, 3, 17), Decimal("110")),
                PricePoint(date(2026, 3, 18), Decimal("120")),
            ),
        )

        result = compute_close_to_close_forward_return(
            series,
            datetime(2026, 3, 14, 10, 0, tzinfo=timezone.utc),
            2,
        )

        self.assertIsNotNone(result)
        forward_return, start_index, end_index = result or (Decimal("0"), -1, -1)
        self.assertEqual(start_index, 1)
        self.assertEqual(end_index, 3)
        self.assertEqual(forward_return.quantize(Decimal("0.0001")), Decimal("14.2857"))

    def test_missing_horizon_returns_none(self) -> None:
        series = PriceSeries(
            ticker="TSLA",
            prices=(
                PricePoint(date(2026, 3, 13), Decimal("200")),
                PricePoint(date(2026, 3, 16), Decimal("198")),
            ),
        )
        result = compute_close_to_close_forward_return(
            series,
            datetime(2026, 3, 13, 9, 0, tzinfo=timezone.utc),
            5,
        )
        self.assertIsNone(result)

    def test_alignment_uses_next_trading_day(self) -> None:
        series = PriceSeries(
            ticker="AAPL",
            prices=(
                PricePoint(date(2026, 3, 13), Decimal("100")),
                PricePoint(date(2026, 3, 16), Decimal("101")),
            ),
        )
        index = align_event_to_trading_index(series, datetime(2026, 3, 14, 12, 0, tzinfo=timezone.utc))
        self.assertEqual(index, 1)

    def test_aggregation_by_horizon_is_correct(self) -> None:
        observations = [
            ForwardReturnObservation(
                event_id="1",
                study_target_type="primary",
                event_category="Product Launch",
                horizon="5D",
                forward_return=Decimal("2.0000"),
                aligned_trade_date=date(2026, 3, 13),
                exit_trade_date=date(2026, 3, 20),
                primary_ticker="NVDA",
            ),
            ForwardReturnObservation(
                event_id="2",
                study_target_type="primary",
                event_category="Product Launch",
                horizon="5D",
                forward_return=Decimal("-1.0000"),
                aligned_trade_date=date(2026, 3, 13),
                exit_trade_date=date(2026, 3, 20),
                primary_ticker="AMD",
            ),
        ]

        aggregates = aggregate_observations(observations)
        summary = next(
            aggregate
            for aggregate in aggregates
            if aggregate.study_target_type == "category_summary" and aggregate.horizon == "5D"
        )
        self.assertEqual(summary.sample_size, 2)
        self.assertEqual(summary.avg_return, Decimal("0.5000"))
        self.assertEqual(summary.median_return, Decimal("0.5000"))
        self.assertEqual(summary.win_rate, Decimal("50.0000"))

    def test_primary_and_related_studies_are_both_produced(self) -> None:
        price_map = build_price_map(
            [
                PriceSeries(
                    ticker="NVDA",
                    prices=(
                        PricePoint(date(2026, 3, 13), Decimal("100")),
                        PricePoint(date(2026, 3, 16), Decimal("101")),
                        PricePoint(date(2026, 3, 17), Decimal("103")),
                        PricePoint(date(2026, 3, 18), Decimal("104")),
                        PricePoint(date(2026, 3, 19), Decimal("105")),
                        PricePoint(date(2026, 3, 20), Decimal("107")),
                    ),
                ),
                PriceSeries(
                    ticker="TSM",
                    prices=(
                        PricePoint(date(2026, 3, 13), Decimal("50")),
                        PricePoint(date(2026, 3, 16), Decimal("51")),
                        PricePoint(date(2026, 3, 17), Decimal("52")),
                        PricePoint(date(2026, 3, 18), Decimal("52.5")),
                        PricePoint(date(2026, 3, 19), Decimal("53")),
                        PricePoint(date(2026, 3, 20), Decimal("54")),
                    ),
                ),
            ]
        )
        events = [
            StudyEvent(
                id="evt-1",
                ticker="NVDA",
                category="Product Launch",
                timestamp=datetime(2026, 3, 13, 8, 30, tzinfo=timezone.utc),
                related_companies=(StudyRelatedCompany(target_ticker="TSM", relationship_type="Supplier", origin_type="explicit"),),
            )
        ]

        observations, stats = compute_event_study_observations(events, price_map)
        self.assertEqual(stats["missing_primary_series"], 0)
        self.assertEqual(stats["missing_related_series"], 0)
        self.assertTrue(any(observation.study_target_type == "primary" for observation in observations))
        self.assertTrue(any(observation.study_target_type == "related" for observation in observations))


if __name__ == "__main__":
    unittest.main()
