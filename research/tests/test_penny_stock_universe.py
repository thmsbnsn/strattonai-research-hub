from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research.penny_stock_universe import load_penny_stock_universe
from research.trading_repository import CompanyProfileRecord


class _FakeSeriesILoc:
    def __init__(self, values):
        self.values = values

    def __getitem__(self, index):
        return self.values[index]


class _FakeSeries:
    def __init__(self, values):
        self.values = values
        self.iloc = _FakeSeriesILoc(values)

    def mean(self):
        return sum(self.values) / len(self.values)


class _FakeFrame:
    def __init__(self, closes, volumes):
        self.empty = False
        self._data = {"c": _FakeSeries(closes), "v": _FakeSeries(volumes)}

    def __contains__(self, item):
        return item in self._data

    def __getitem__(self, item):
        return self._data[item]


class _FakeTradingRepository:
    def __init__(self, _repo_root: Path):
        pass

    def load_company_profiles(self, tickers):
        return {
            "PENY": CompanyProfileRecord("PENY", "Penny Co", "Healthcare", "Biotech", "$200.0M", 200_000_000.0)
        }


class PennyStockUniverseTests(unittest.TestCase):
    def test_load_penny_stock_universe_filters_to_allowed_exchange_and_price_band(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, patch("research.penny_stock_universe.TradingRepository", _FakeTradingRepository), patch(
            "research.penny_stock_universe.list_assets",
            return_value=[
                {"symbol": "PENY", "exchange": "NASDAQ", "name": "Penny Co"},
                {"symbol": "OTCX", "exchange": "OTC", "name": "Excluded"},
            ],
        ), patch(
            "research.penny_stock_universe.get_bars",
            side_effect=lambda symbol, limit, repo_root=None: _FakeFrame([2.1, 2.2, 2.3], [150_000, 160_000, 170_000]),
        ):
            candidates = load_penny_stock_universe(repo_root=Path(temp_dir), refresh=True, min_volume=100_000)

        self.assertEqual([candidate.ticker for candidate in candidates], ["PENY"])


if __name__ == "__main__":
    unittest.main()
