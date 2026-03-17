from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from research.trading_loop import run_trading_loop
from research.transaction_costs import TransactionCostBreakdown


class _FakeTradingRepository:
    def __init__(self, _repo_root: Path):
        self.upserted: list[dict] = []

    def load_signal_scores(self, *, signal_keys=None, ticker=None, confidence_bands=None):
        return []

    def latest_daily_price(self, _ticker):
        return None

    def upsert_paper_trade(self, trade: dict) -> None:
        self.upserted.append(trade)


class _FakeRiskReport:
    blocked_high_vol = ()

    def to_dict(self):
        return {"blockedHighVol": []}


class TradingLoopTests(unittest.TestCase):
    def test_run_trading_loop_writes_dry_run_trade_for_penny_candidate(self) -> None:
        repository = _FakeTradingRepository(Path("."))
        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "research.trading_loop.load_alpaca_config",
            return_value=SimpleNamespace(mode="paper", live_confirmed=False),
        ), patch("research.trading_loop.TradingRepository", return_value=repository), patch(
            "research.trading_loop.get_account",
            return_value={"buying_power": "100.00"},
        ), patch(
            "research.trading_loop.get_positions",
            return_value=[],
        ), patch(
            "research.trading_loop.build_penny_stock_candidates",
            return_value=[
                SimpleNamespace(
                    to_dict=lambda: {
                        "ticker": "PENY",
                        "signal_type": "Momentum",
                        "score": 40.0,
                        "entry_price": 2.0,
                        "suggested_qty": 5.0,
                        "estimated_cost": 0.2,
                        "estimated_cost_pct": 0.01,
                        "confidence_band": "Low",
                    }
                )
            ],
        ), patch(
            "research.trading_loop.assess_portfolio_risk",
            return_value=_FakeRiskReport(),
        ), patch(
            "research.trading_loop.compute_round_trip_cost",
            return_value=TransactionCostBreakdown(0.1, 0.1, 0.0, 0.35, 0.55, 0.0275, "penny", 150_000, 300_000),
        ), patch(
            "research.trading_loop.get_current_regime",
            return_value=type("Regime", (), {"label": "bull_low_vol"})(),
        ), patch(
            "research.trading_loop.build_order_preview",
            return_value=type("Preview", (), {"approved": True, "rejection_reason": None, "to_dict": lambda self: {"approved": True}})(),
        ):
            result = run_trading_loop(15.0, "penny", "paper", dry_run=True, repo_root=Path(temp_dir))

        self.assertTrue(result["success"])
        self.assertEqual(len(result["data"]["executed"]), 1)
        self.assertEqual(repository.upserted[0]["universe"], "penny")

    def test_run_trading_loop_blocks_unconfirmed_live_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "research.trading_loop.load_alpaca_config",
            return_value=SimpleNamespace(mode="paper", live_confirmed=False),
        ):
            with self.assertRaises(RuntimeError):
                run_trading_loop(15.0, "penny", "live", repo_root=Path(temp_dir))


if __name__ == "__main__":
    unittest.main()
