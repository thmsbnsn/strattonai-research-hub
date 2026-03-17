from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research.portfolio_constructor import construct_portfolio


class _FakeTradingRepository:
    def __init__(self, _repo_root: Path):
        self.upserted = None

    def load_signal_scores(self, *, signal_keys=None, ticker=None, confidence_bands=None):
        return [
            {
                "signal_key": "sig-nvda",
                "target_ticker": "NVDA",
                "score": 82.0,
                "avg_return": 3.2,
                "win_rate": 68.0,
            },
            {
                "signal_key": "sig-aapl",
                "target_ticker": "AAPL",
                "score": 71.0,
                "avg_return": 1.5,
                "win_rate": 61.0,
            },
        ]

    def upsert_portfolio_allocations(self, **kwargs):
        self.upserted = kwargs
        return []


class PortfolioConstructorTests(unittest.TestCase):
    def test_construct_portfolio_returns_kelly_allocations(self) -> None:
        repository = _FakeTradingRepository(Path("."))
        with tempfile.TemporaryDirectory() as temp_dir, patch("research.portfolio_constructor.TradingRepository", return_value=repository):
            result = construct_portfolio("kelly", 1000.0, repo_root=Path(temp_dir), dry_run=True)

        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["method"], "kelly")
        self.assertGreater(len(result["data"]["allocations"]), 0)


if __name__ == "__main__":
    unittest.main()
