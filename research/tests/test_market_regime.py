from __future__ import annotations

import unittest
from datetime import date, timedelta
from decimal import Decimal

from research.market_regime import _compute_regime_from_bars
from research.trading_repository import PriceBar


def _spy_bars() -> list[PriceBar]:
    rows: list[PriceBar] = []
    start = date(2025, 1, 1)
    price = 400.0
    for index in range(260):
        price *= 1.0005
        rows.append(
            PriceBar(
                ticker="SPY",
                trade_date=start + timedelta(days=index),
                open=Decimal(str(price)),
                high=Decimal(str(price * 1.002)),
                low=Decimal(str(price * 0.998)),
                close=Decimal(str(price)),
                volume=1_000_000,
            )
        )
    return rows


class MarketRegimeTests(unittest.TestCase):
    def test_compute_regime_from_bars_identifies_bull_low_vol(self) -> None:
        bars = _spy_bars()
        result = _compute_regime_from_bars(bars, bars[-1].trade_date)

        self.assertEqual(result.label, "bull_low_vol")
        self.assertGreater(result.spy_price, result.sma_200)
        self.assertIn("spyPrice", result.to_dict())


if __name__ == "__main__":
    unittest.main()
