from __future__ import annotations

import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from research.penny_stock_signals import PennyStockSignalCandidate, build_penny_stock_candidates
from research.penny_stock_universe import PennyStockCandidate
from research.trading_repository import PriceBar
from research.transaction_costs import TransactionCostBreakdown


class _FakeTradingRepository:
    def __init__(self, _repo_root: Path):
        pass

    def load_signal_scores(self, *, signal_keys=None, ticker=None, confidence_bands=None):
        return [
            {
                "target_ticker": "PENY",
                "score": 62.0,
                "event_category": "Product Launch",
                "confidence_band": "Moderate",
            }
        ]

    def load_daily_prices(self, tickers, *, limit_per_ticker=None):
        bars = [
            PriceBar("PENY", date(2026, 3, day), Decimal("2.0"), Decimal("2.1"), Decimal("1.9"), Decimal(str(2.0 + day * 0.01)), 150_000)
            for day in range(1, 26)
        ]
        return {"PENY": bars[-limit_per_ticker:] if limit_per_ticker else bars}


class _FakeRiskReport:
    blocked_high_vol = ()


class PennyStockSignalsTests(unittest.TestCase):
    def test_build_penny_stock_candidates_uses_best_signal_and_costs(self) -> None:
        universe = [PennyStockCandidate("PENY", "Penny Co", "NASDAQ", 2.35, 150_000, 200_000_000)]
        with tempfile.TemporaryDirectory() as temp_dir, patch("research.penny_stock_signals.TradingRepository", _FakeTradingRepository), patch(
            "research.penny_stock_signals.load_penny_stock_universe",
            return_value=universe,
        ), patch(
            "research.penny_stock_signals.compute_round_trip_cost",
            return_value=TransactionCostBreakdown(1.0, 1.0, 0.0, 0.7, 2.7, 0.027, "small_cap", 150_000, 352_500),
        ), patch(
            "research.penny_stock_signals.assess_portfolio_risk",
            return_value=_FakeRiskReport(),
        ):
            candidates = build_penny_stock_candidates(15.0, repo_root=Path(temp_dir), top_n=5)

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].ticker, "PENY")
        self.assertEqual(candidates[0].confidence_band, "Moderate")


if __name__ == "__main__":
    unittest.main()
