from __future__ import annotations

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from research.risk_gate import apply_risk_gate
from research.trading_repository import PriceBar


class _FakeRepository:
    def __init__(self, _root: Path):
        pass

    def load_daily_prices(self, tickers, *, limit_per_ticker=None, min_date=None):
        return {
            "NVDA": [
                PriceBar("NVDA", __import__("datetime").date(2026, 3, 10), None, None, None, Decimal("10"), 100000, None, None),
                PriceBar("NVDA", __import__("datetime").date(2026, 3, 11), None, None, None, Decimal("11"), 100000, None, None),
            ]
        }

    def latest_daily_price(self, ticker: str):
        return PriceBar(ticker, __import__("datetime").date(2026, 3, 11), None, None, None, Decimal("10"), 100000, None, None)


def _risk_metric(vol=0.5, beta=1.0, var=-0.02, sector="Technology"):
    return SimpleNamespace(
        ticker="NVDA",
        annualized_vol=vol,
        beta=beta,
        value_at_risk_95=var,
        max_drawdown=-0.1,
        size_factor=None,
        momentum_12_1=None,
        blocked_high_vol=False,
        sector=sector,
        weight=0.2,
    )


class RiskGateTests(unittest.TestCase):
    def test_blocks_when_volatility_exceeds_threshold(self) -> None:
        fake_report = SimpleNamespace(metrics=[_risk_metric(vol=0.95)], sector_exposure={"Technology": 0.2}, clusters=[])
        with tempfile.TemporaryDirectory() as temp_dir, patch("research.risk_gate.TradingRepository", _FakeRepository), patch(
            "research.risk_gate.assess_portfolio_risk",
            return_value=fake_report,
        ):
            result = apply_risk_gate("NVDA", 1000.0, {}, repo_root=Path(temp_dir))
        self.assertFalse(result.approved)
        self.assertTrue(any("vol" in reason for reason in result.hard_blocks))

    def test_blocks_when_position_exceeds_max_single_position(self) -> None:
        fake_report = SimpleNamespace(metrics=[_risk_metric()], sector_exposure={"Technology": 0.2}, clusters=[])
        with tempfile.TemporaryDirectory() as temp_dir, patch("research.risk_gate.TradingRepository", _FakeRepository), patch(
            "research.risk_gate.assess_portfolio_risk",
            return_value=fake_report,
        ):
            result = apply_risk_gate("NVDA", 5000.0, {"AAPL": 1000.0}, repo_root=Path(temp_dir))
        self.assertFalse(result.approved)
        self.assertTrue(any("single position" in reason for reason in result.hard_blocks))

    def test_approves_when_all_checks_pass(self) -> None:
        fake_report = SimpleNamespace(metrics=[_risk_metric()], sector_exposure={"Technology": 0.2}, clusters=[])
        with tempfile.TemporaryDirectory() as temp_dir, patch("research.risk_gate.TradingRepository", _FakeRepository), patch(
            "research.risk_gate.assess_portfolio_risk",
            return_value=fake_report,
        ):
            result = apply_risk_gate("NVDA", 1000.0, {"AAPL": 4000.0}, repo_root=Path(temp_dir))
        self.assertTrue(result.approved)
        self.assertEqual(result.hard_blocks, [])

    def test_soft_warning_for_high_beta_does_not_block(self) -> None:
        fake_report = SimpleNamespace(metrics=[_risk_metric(beta=2.4)], sector_exposure={"Technology": 0.2}, clusters=[])
        with tempfile.TemporaryDirectory() as temp_dir, patch("research.risk_gate.TradingRepository", _FakeRepository), patch(
            "research.risk_gate.assess_portfolio_risk",
            return_value=fake_report,
        ):
            result = apply_risk_gate("NVDA", 1000.0, {"AAPL": 4000.0}, repo_root=Path(temp_dir))
        self.assertTrue(result.approved)
        self.assertTrue(any("beta" in reason for reason in result.soft_warnings))


if __name__ == "__main__":
    unittest.main()
