from __future__ import annotations

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from research.order_preview import build_order_preview
from research.trading_repository import PriceBar
from research.transaction_costs import TransactionCostBreakdown


class _FakeRepository:
    def __init__(self, _root: Path):
        pass

    def latest_daily_price(self, ticker: str):
        return PriceBar(ticker, __import__("datetime").date(2026, 3, 11), None, None, None, Decimal("50"), 100000, None, None)


class _FakeRiskGate:
    approved = True
    hard_blocks: list[str] = []
    soft_warnings: list[str] = ["beta 2.2 outside preferred range"]


class OrderPreviewTests(unittest.TestCase):
    def test_build_order_preview_returns_expected_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, patch("research.order_preview.TradingRepository", _FakeRepository), patch(
            "research.order_preview.compute_round_trip_cost",
            return_value=TransactionCostBreakdown(1.0, 1.0, 0.0, 0.5, 2.5, 0.01, "large_cap", 1000000, 10000000),
        ), patch(
            "research.order_preview.apply_risk_gate",
            return_value=_FakeRiskGate(),
        ), patch(
            "research.order_preview.get_current_regime",
            return_value=type("Regime", (), {"label": "bull_low_vol"})(),
        ):
            preview = build_order_preview("AAPL", "buy", 10, {"buying_power": 1000.0}, repo_root=Path(temp_dir))
        self.assertTrue(preview.approved)
        self.assertEqual(preview.ticker, "AAPL")
        self.assertEqual(preview.regime_label, "bull_low_vol")


if __name__ == "__main__":
    unittest.main()
