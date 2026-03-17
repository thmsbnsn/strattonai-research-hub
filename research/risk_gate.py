"""Unified deterministic trade-entry risk gate for StrattonAI."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .risk_engine import assess_portfolio_risk
from .trading_repository import TradingRepository


@dataclass(frozen=True, slots=True)
class RiskGateConfig:
    max_vol_annualized: float = 0.80
    max_single_position_pct: float = 0.25
    max_sector_pct: float = 0.35
    max_cluster_pct: float = 0.40
    min_adv_dollars: float = 500_000
    penny_max_vol: float = 1.50


@dataclass(frozen=True, slots=True)
class RiskGateResult:
    approved: bool
    hard_blocks: list[str]
    soft_warnings: list[str]
    vol_annualized: float | None
    beta: float | None
    var_95: float | None
    sector: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "approved": self.approved,
            "hardBlocks": self.hard_blocks,
            "softWarnings": self.soft_warnings,
            "volAnnualized": self.vol_annualized,
            "beta": self.beta,
            "var95": self.var_95,
            "sector": self.sector,
        }


def _average_daily_volume_dollars(repository: TradingRepository, ticker: str) -> float:
    bars = repository.load_daily_prices([ticker], limit_per_ticker=20).get(ticker.upper(), [])
    if not bars:
        return 0.0
    notional_values = [
        float(bar.close) * float(bar.volume or 0)
        for bar in bars
        if bar.volume is not None
    ]
    if not notional_values:
        return 0.0
    return sum(notional_values) / len(notional_values)


def apply_risk_gate(
    ticker: str,
    allocation_dollars: float,
    current_portfolio_allocations: dict[str, float],
    config: RiskGateConfig | None = None,
    *,
    repo_root: Path | None = None,
) -> RiskGateResult:
    root = repo_root or Path(__file__).resolve().parent.parent
    repository = TradingRepository(root)
    cfg = config or RiskGateConfig()
    normalized_ticker = ticker.upper()

    proposed_allocations = {
        symbol.upper(): float(value)
        for symbol, value in current_portfolio_allocations.items()
        if float(value) > 0
    }
    proposed_allocations[normalized_ticker] = proposed_allocations.get(normalized_ticker, 0.0) + float(allocation_dollars)
    total_capital = sum(proposed_allocations.values()) or float(allocation_dollars or 1.0)

    report = assess_portfolio_risk(proposed_allocations, repo_root=root)
    metric = next((item for item in report.metrics if item.ticker == normalized_ticker), None)
    latest_price = repository.latest_daily_price(normalized_ticker)
    is_penny = latest_price is not None and float(latest_price.close) < 5.0
    vol_limit = cfg.penny_max_vol if is_penny else cfg.max_vol_annualized
    position_pct = proposed_allocations[normalized_ticker] / float(total_capital or 1.0)
    adv_dollars = _average_daily_volume_dollars(repository, normalized_ticker)

    hard_blocks: list[str] = []
    soft_warnings: list[str] = []

    if metric and metric.annualized_vol is not None and metric.annualized_vol > vol_limit:
        hard_blocks.append(
            f"vol {metric.annualized_vol:.2%} exceeds {'penny ' if is_penny else ''}threshold {vol_limit:.2%}"
        )
    if position_pct > cfg.max_single_position_pct:
        hard_blocks.append(f"single position {position_pct:.2%} exceeds {cfg.max_single_position_pct:.2%}")
    if adv_dollars < cfg.min_adv_dollars:
        hard_blocks.append(f"ADV ${adv_dollars:,.0f} below ${cfg.min_adv_dollars:,.0f}")

    sector = metric.sector if metric else None
    if sector and report.sector_exposure.get(sector, 0.0) > cfg.max_sector_pct:
        hard_blocks.append(
            f"sector {sector} exposure {report.sector_exposure.get(sector, 0.0):.2%} exceeds {cfg.max_sector_pct:.2%}"
        )

    if metric and metric.beta is not None and (metric.beta > 2.0 or metric.beta < -0.5):
        soft_warnings.append(f"beta {metric.beta:.2f} outside preferred range")
    if metric and metric.value_at_risk_95 is not None and abs(metric.value_at_risk_95) * allocation_dollars > allocation_dollars * 0.05:
        soft_warnings.append(f"VaR 95% {metric.value_at_risk_95:.2%} exceeds 5% of position value")
    for cluster in report.clusters:
        if normalized_ticker in cluster.tickers and cluster.total_weight > cfg.max_cluster_pct:
            soft_warnings.append(
                f"cluster {', '.join(cluster.tickers)} concentration {cluster.total_weight:.2%} exceeds {cfg.max_cluster_pct:.2%}"
            )

    return RiskGateResult(
        approved=not hard_blocks,
        hard_blocks=hard_blocks,
        soft_warnings=soft_warnings,
        vol_annualized=metric.annualized_vol if metric else None,
        beta=metric.beta if metric else None,
        var_95=metric.value_at_risk_95 if metric else None,
        sector=sector,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply the deterministic StrattonAI risk gate to a proposed trade.")
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--allocation", type=float, required=True)
    parser.add_argument("--portfolio", default="", help="Comma-separated TICKER:ALLOCATION pairs.")
    args = parser.parse_args()

    portfolio: dict[str, float] = {}
    for part in [value for value in args.portfolio.split(",") if value.strip()]:
        ticker, amount = part.split(":", 1)
        portfolio[ticker.strip().upper()] = float(amount)

    result = apply_risk_gate(args.ticker, args.allocation, portfolio)
    print(json.dumps(result.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
