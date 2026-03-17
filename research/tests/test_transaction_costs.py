from __future__ import annotations

import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from research.trading_repository import CompanyProfileRecord, PriceBar
from research.transaction_costs import compute_round_trip_cost


class _FakeTradingRepository:
    def __init__(self, _repo_root: Path):
        pass

    def load_company_profiles(self, _tickers):
        return {
            "AAPL": CompanyProfileRecord(
                ticker="AAPL",
                name="Apple Inc.",
                sector="Technology",
                industry="Hardware",
                market_cap_text="$3.00T",
                market_cap_value=3_000_000_000_000.0,
            )
        }

    def load_daily_prices(self, _tickers, *, limit_per_ticker=None):
        bars = [
            PriceBar(
                ticker="AAPL",
                trade_date=date(2026, 3, index + 1),
                open=Decimal("100"),
                high=Decimal("101"),
                low=Decimal("99"),
                close=Decimal("100"),
                volume=1_000_000,
            )
            for index in range(20)
        ]
        return {"AAPL": bars[-limit_per_ticker:] if limit_per_ticker else bars}


class TransactionCostTests(unittest.TestCase):
    def test_compute_round_trip_cost_returns_positive_breakdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "research.transaction_costs.TradingRepository",
            _FakeTradingRepository,
        ):
            result = compute_round_trip_cost("AAPL", 100, 150.0, repo_root=Path(temp_dir))

        self.assertEqual(result.market_cap_bucket, "large_cap")
        self.assertGreater(result.spread_cost, 0)
        self.assertGreater(result.fees, 0)
        self.assertGreater(result.total_cost_dollars, result.fees)


if __name__ == "__main__":
    unittest.main()
