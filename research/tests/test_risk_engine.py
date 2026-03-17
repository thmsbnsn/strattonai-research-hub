from __future__ import annotations

import tempfile
import unittest
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from research.risk_engine import assess_portfolio_risk
from research.trading_repository import CompanyProfileRecord, PriceBar


def _bars(ticker: str, base: float, scale: float) -> list[PriceBar]:
    start = date(2025, 12, 1)
    rows: list[PriceBar] = []
    price = base
    for index in range(80):
        price *= 1 + ((-1) ** index) * scale
        rows.append(
            PriceBar(
                ticker=ticker,
                trade_date=start + timedelta(days=index),
                open=Decimal(str(price)),
                high=Decimal(str(price * 1.01)),
                low=Decimal(str(price * 0.99)),
                close=Decimal(str(price)),
                volume=1_000_000,
            )
        )
    return rows


class _FakeTradingRepository:
    def __init__(self, _repo_root: Path):
        pass

    def load_daily_prices(self, tickers, *, limit_per_ticker=None, min_date=None):
        dataset = {
            "NVDA": _bars("NVDA", 100.0, 0.12),
            "AAPL": _bars("AAPL", 80.0, 0.01),
            "SPY": _bars("SPY", 400.0, 0.005),
        }
        return {ticker: dataset.get(ticker, [])[-limit_per_ticker:] if limit_per_ticker else dataset.get(ticker, []) for ticker in tickers}

    def load_company_profiles(self, _tickers):
        return {
            "NVDA": CompanyProfileRecord("NVDA", "NVIDIA", "Technology", "Semis", "$2.0T", 2_000_000_000_000.0),
            "AAPL": CompanyProfileRecord("AAPL", "Apple", "Technology", "Hardware", "$3.0T", 3_000_000_000_000.0),
        }


class RiskEngineTests(unittest.TestCase):
    def test_assess_portfolio_risk_flags_sector_and_volatility(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, patch("research.risk_engine.TradingRepository", _FakeTradingRepository):
            report = assess_portfolio_risk({"NVDA": 600.0, "AAPL": 400.0}, repo_root=Path(temp_dir), vol_threshold=0.8)

        self.assertEqual(len(report.metrics), 2)
        self.assertIn("NVDA", report.blocked_high_vol)
        self.assertTrue(any("Sector Technology" in warning for warning in report.sector_breach_warnings))
        self.assertIn("NVDA", report.correlation_matrix)


if __name__ == "__main__":
    unittest.main()
