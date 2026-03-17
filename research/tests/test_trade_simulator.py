from __future__ import annotations

import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from research.trade_simulator import simulate_trade
from research.trading_repository import PriceBar
from research.transaction_costs import TransactionCostBreakdown


class _FakeTradingRepository:
    def __init__(self, _repo_root: Path):
        self.upserted: list[dict] = []

    def load_signal_scores(self, *, signal_keys=None, ticker=None, confidence_bands=None):
        return [
            {
                "signal_key": "sig-1",
                "target_ticker": "NVDA",
                "avg_return": 5.0,
                "horizon": "5D",
                "score": 80.0,
                "evidence_summary": "Strong event-study support.",
            }
        ]

    def latest_daily_price(self, _ticker: str):
        return PriceBar(
            ticker="NVDA",
            trade_date=date(2026, 3, 16),
            open=Decimal("100"),
            high=Decimal("101"),
            low=Decimal("99"),
            close=Decimal("100"),
            volume=1_000_000,
        )

    def load_paper_trades(self, *, statuses=None, universe=None):
        return []

    def upsert_paper_trade(self, trade: dict) -> None:
        self.upserted.append(trade)


class _FakeRiskReport:
    blocked_high_vol = ()

    def to_dict(self):
        return {"blockedHighVol": []}


class _FakeBlockedRiskReport:
    blocked_high_vol = ("NVDA",)

    def to_dict(self):
        return {"blockedHighVol": ["NVDA"]}


class TradeSimulatorTests(unittest.TestCase):
    def test_simulate_trade_returns_projected_trade_payload(self) -> None:
        repository = _FakeTradingRepository(Path("."))
        with tempfile.TemporaryDirectory() as temp_dir, patch("research.trade_simulator.TradingRepository", return_value=repository), patch(
            "research.trade_simulator.assess_portfolio_risk",
            return_value=_FakeRiskReport(),
        ), patch(
            "research.trade_simulator.apply_risk_gate",
            return_value=type("Gate", (), {"approved": True, "hard_blocks": [], "soft_warnings": [], "to_dict": lambda self: {"approved": True, "hardBlocks": [], "softWarnings": []}})(),
        ), patch(
            "research.trade_simulator.compute_round_trip_cost",
            return_value=TransactionCostBreakdown(1.0, 1.0, 0.0, 0.7, 2.7, 0.027, "large_cap", 1_000_000, 100_000_000),
        ):
            result = simulate_trade("sig-1", 1000.0, repo_root=Path(temp_dir), dry_run=True, show_costs=True)

        self.assertTrue(result["success"])
        self.assertEqual(result["ticker"], "NVDA")
        self.assertEqual(result["holdDays"], 5)
        self.assertGreater(result["shares"], 0)

    def test_simulate_trade_returns_risk_blocked_when_filter_hits(self) -> None:
        repository = _FakeTradingRepository(Path("."))
        with tempfile.TemporaryDirectory() as temp_dir, patch("research.trade_simulator.TradingRepository", return_value=repository), patch(
            "research.trade_simulator.assess_portfolio_risk",
            return_value=_FakeBlockedRiskReport(),
        ), patch(
            "research.trade_simulator.apply_risk_gate",
            return_value=type("Gate", (), {"approved": False, "hard_blocks": ["vol"], "soft_warnings": [], "to_dict": lambda self: {"approved": False, "hardBlocks": ["vol"], "softWarnings": []}})(),
        ):
            result = simulate_trade("sig-1", 1000.0, repo_root=Path(temp_dir), dry_run=True)

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "risk-blocked")


if __name__ == "__main__":
    unittest.main()
