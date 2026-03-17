from __future__ import annotations

import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from research.portfolio_metrics import compute_portfolio_metrics
from research.trading_repository import PaperTradeRecord


class _FakeTradingRepository:
    def __init__(self, _repo_root: Path):
        pass

    def load_paper_trades(self, *, statuses=None, universe=None):
        return [
            PaperTradeRecord(
                id="1",
                ticker="NVDA",
                direction="Long",
                signal="Launch",
                entry_price=Decimal("100"),
                current_price=Decimal("110"),
                entry_date=date(2026, 3, 1),
                quantity=Decimal("10"),
                status="simulated",
                realized_pnl=Decimal("100"),
            ),
            PaperTradeRecord(
                id="2",
                ticker="AAPL",
                direction="Long",
                signal="Approval",
                entry_price=Decimal("50"),
                current_price=Decimal("48"),
                entry_date=date(2026, 3, 2),
                quantity=Decimal("20"),
                status="closed",
                realized_pnl=Decimal("-40"),
                exit_date=date(2026, 3, 5),
            ),
        ]


class PortfolioMetricsTests(unittest.TestCase):
    def test_compute_portfolio_metrics_builds_equity_curve_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, patch("research.portfolio_metrics.TradingRepository", _FakeTradingRepository):
            metrics = compute_portfolio_metrics(repo_root=Path(temp_dir))

        payload = metrics.to_dict()
        self.assertEqual(len(payload["equityCurve"]), 2)
        self.assertIn("cumulativePnl", payload["equityCurve"][0])
        self.assertNotEqual(payload["turnover"], 0)


if __name__ == "__main__":
    unittest.main()
