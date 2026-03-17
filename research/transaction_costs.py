"""Deterministic transaction-cost modeling for simulated and paper trades."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .trading_repository import TradingRepository


@dataclass(frozen=True, slots=True)
class TransactionCostConfig:
    large_cap_spread_pct: float = 0.0003
    mid_cap_spread_pct: float = 0.0008
    small_cap_spread_pct: float = 0.0020
    penny_spread_pct: float = 0.0050
    slippage_small_pct: float = 0.0001
    slippage_medium_pct: float = 0.0005
    slippage_large_pct: float = 0.0015
    penny_slippage_floor_pct: float = 0.0010
    illiquid_penalty_pct: float = 0.0025
    fee_per_share: float = 0.0035
    min_fee_per_trade: float = 0.35


@dataclass(frozen=True, slots=True)
class TransactionCostBreakdown:
    spread_cost: float
    slippage_cost: float
    liquidity_cost: float
    fees: float
    total_cost_dollars: float
    total_cost_pct: float
    market_cap_bucket: str
    average_daily_volume: float
    average_daily_dollar_volume: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "spreadCost": self.spread_cost,
            "slippageCost": self.slippage_cost,
            "liquidityCost": self.liquidity_cost,
            "fees": self.fees,
            "totalCostDollars": self.total_cost_dollars,
            "totalCostPct": self.total_cost_pct,
            "marketCapBucket": self.market_cap_bucket,
            "averageDailyVolume": self.average_daily_volume,
            "averageDailyDollarVolume": self.average_daily_dollar_volume,
        }


def _market_cap_bucket(price: float, market_cap: float | None) -> tuple[str, float]:
    if price < 5 or (market_cap is not None and market_cap < 100_000_000):
        return "penny", 0.0050
    if market_cap is not None and market_cap > 10_000_000_000:
        return "large_cap", 0.0003
    if market_cap is not None and market_cap > 1_000_000_000:
        return "mid_cap", 0.0008
    return "small_cap", 0.0020


def compute_round_trip_cost(
    ticker: str,
    shares: float,
    entry_price: float,
    config: TransactionCostConfig | None = None,
    *,
    repo_root: Path | None = None,
) -> TransactionCostBreakdown:
    config = config or TransactionCostConfig()
    repository = TradingRepository(repo_root or Path(__file__).resolve().parent.parent)

    profile = repository.load_company_profiles([ticker.upper()]).get(ticker.upper())
    market_cap = profile.market_cap_value if profile else None
    recent_prices = repository.load_daily_prices([ticker.upper()], limit_per_ticker=20).get(ticker.upper(), [])
    average_daily_volume = (
        sum(float(bar.volume or 0) for bar in recent_prices) / len(recent_prices)
        if recent_prices
        else 0.0
    )
    average_daily_dollar_volume = average_daily_volume * float(entry_price)
    order_value = float(shares) * float(entry_price)

    market_cap_bucket, spread_pct = _market_cap_bucket(float(entry_price), market_cap)
    if market_cap_bucket == "penny":
        spread_pct = config.penny_spread_pct
    elif market_cap_bucket == "large_cap":
        spread_pct = config.large_cap_spread_pct
    elif market_cap_bucket == "mid_cap":
        spread_pct = config.mid_cap_spread_pct
    else:
        spread_pct = config.small_cap_spread_pct

    if average_daily_volume <= 0 or entry_price <= 0:
        adv_ratio = 1.0
    else:
        adv_ratio = order_value / max(average_daily_volume * float(entry_price), 1e-9)

    if adv_ratio < 0.001:
        slippage_pct = config.slippage_small_pct
    elif adv_ratio <= 0.01:
        slippage_pct = config.slippage_medium_pct
    else:
        slippage_pct = config.slippage_large_pct

    if market_cap_bucket == "penny":
        slippage_pct = max(slippage_pct, config.penny_slippage_floor_pct)

    liquidity_pct = config.illiquid_penalty_pct if average_daily_dollar_volume < 500_000 else 0.0
    spread_cost = order_value * spread_pct
    slippage_cost = order_value * slippage_pct * 2.0
    liquidity_cost = order_value * liquidity_pct
    fees = max(float(shares) * config.fee_per_share, config.min_fee_per_trade) * 2.0
    total_cost_dollars = spread_cost + slippage_cost + liquidity_cost + fees
    total_cost_pct = total_cost_dollars / order_value if order_value > 0 else 0.0

    return TransactionCostBreakdown(
        spread_cost=round(spread_cost, 6),
        slippage_cost=round(slippage_cost, 6),
        liquidity_cost=round(liquidity_cost, 6),
        fees=round(fees, 6),
        total_cost_dollars=round(total_cost_dollars, 6),
        total_cost_pct=round(total_cost_pct, 6),
        market_cap_bucket=market_cap_bucket,
        average_daily_volume=round(average_daily_volume, 4),
        average_daily_dollar_volume=round(average_daily_dollar_volume, 4),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Estimate deterministic round-trip transaction costs.")
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--shares", type=float, required=True)
    parser.add_argument("--entry-price", type=float, required=True)
    args = parser.parse_args()

    breakdown = compute_round_trip_cost(args.ticker, args.shares, args.entry_price)
    print(json.dumps(breakdown.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
