"""Deterministic market-regime classification for StrattonAI."""

from __future__ import annotations

import argparse
import json
import logging
import math
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from statistics import pstdev
from typing import Any

from .price_dataset import load_resolved_price_series
from .trading_repository import PriceBar, TradingRepository


LOGGER = logging.getLogger("research.market_regime")


@dataclass(frozen=True, slots=True)
class RegimeResult:
    label: str
    spy_price: float
    sma_200: float
    sma_50: float
    vol_20d: float
    drawdown_from_high: float
    as_of_date: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "spyPrice": self.spy_price,
            "sma200": self.sma_200,
            "sma50": self.sma_50,
            "vol20d": self.vol_20d,
            "drawdownFromHigh": self.drawdown_from_high,
            "asOfDate": self.as_of_date,
        }


def _load_spy_bars(repo_root: Path) -> list[PriceBar]:
    repository = TradingRepository(repo_root)
    bars = repository.load_daily_prices(["SPY"], limit_per_ticker=400).get("SPY", [])
    if bars:
        return bars

    series, _ = load_resolved_price_series(repo_root, None, tickers={"SPY"})
    if not series:
        return []
    spy_series = series[0]
    return [
        PriceBar(
            ticker="SPY",
            trade_date=point.date,
            open=None,
            high=None,
            low=None,
            close=point.close,
            volume=None,
        )
        for point in spy_series.prices
    ]


def _daily_returns(bars: list[PriceBar]) -> list[float]:
    returns: list[float] = []
    for previous, current in zip(bars, bars[1:]):
        if previous.close == 0:
            continue
        returns.append(float((current.close - previous.close) / previous.close))
    return returns


def _compute_regime_from_bars(bars: list[PriceBar], as_of: date) -> RegimeResult:
    historical = [bar for bar in bars if bar.trade_date <= as_of]
    if len(historical) < 200:
        raise ValueError("SPY history is too short to classify market regime.")

    closes = [float(bar.close) for bar in historical]
    spy_price = closes[-1]
    sma_200 = sum(closes[-200:]) / 200
    sma_50 = sum(closes[-50:]) / 50
    returns = _daily_returns(historical[-21:])
    vol_20d = pstdev(returns) * math.sqrt(252) if len(returns) > 1 else 0.0
    high_52w = max(closes[-252:] if len(closes) >= 252 else closes)
    drawdown = (spy_price - high_52w) / high_52w if high_52w else 0.0

    if drawdown <= -0.20:
        label = "bear"
    elif spy_price > sma_200 and vol_20d < 0.25:
        label = "bull_low_vol"
    elif spy_price > sma_200 and vol_20d >= 0.25:
        label = "bull_high_vol"
    else:
        label = "neutral"

    return RegimeResult(
        label=label,
        spy_price=round(spy_price, 6),
        sma_200=round(sma_200, 6),
        sma_50=round(sma_50, 6),
        vol_20d=round(vol_20d, 6),
        drawdown_from_high=round(drawdown, 6),
        as_of_date=as_of.isoformat(),
    )


def get_current_regime(as_of_date: str | None = None, *, repo_root: Path | None = None, persist: bool = False) -> RegimeResult:
    root = repo_root or Path(__file__).resolve().parent.parent
    bars = _load_spy_bars(root)
    if not bars:
        raise ValueError("SPY price history is unavailable.")
    as_of = date.fromisoformat(as_of_date) if as_of_date else bars[-1].trade_date
    result = _compute_regime_from_bars(bars, as_of)
    if persist:
        try:
            TradingRepository(root).upsert_market_regime(
                {
                    "as_of_date": result.as_of_date,
                    "regime_label": result.label,
                    "spy_price": result.spy_price,
                    "sma_200": result.sma_200,
                    "sma_50": result.sma_50,
                    "vol_20d": result.vol_20d,
                    "drawdown_from_high": result.drawdown_from_high,
                }
            )
        except Exception as error:
            LOGGER.warning("Market regime persistence skipped: %s", error)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute deterministic market-regime labels from SPY.")
    parser.add_argument("--as-of", default=None)
    parser.add_argument("--backfill-days", type=int, default=0)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    if args.backfill_days > 0:
        bars = _load_spy_bars(root)
        last_date = bars[-1].trade_date
        start_date = last_date - timedelta(days=args.backfill_days - 1)
        results = []
        for bar in bars:
            if bar.trade_date < start_date:
                continue
            try:
                result = get_current_regime(bar.trade_date.isoformat(), repo_root=root, persist=True)
            except ValueError:
                continue
            results.append(result.to_dict())
        print(json.dumps(results, indent=2))
        return 0

    result = get_current_regime(args.as_of, repo_root=root, persist=True)
    print(json.dumps(result.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
