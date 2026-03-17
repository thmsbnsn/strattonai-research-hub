"""Deterministic portfolio and signal-side risk assessment utilities."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from .trading_repository import PriceBar, TradingRepository


@dataclass(frozen=True, slots=True)
class RiskMetric:
    ticker: str
    annualized_vol: float | None
    beta: float | None
    value_at_risk_95: float | None
    max_drawdown: float | None
    size_factor: float | None
    momentum_12_1: float | None
    blocked_high_vol: bool
    sector: str | None
    weight: float


@dataclass(frozen=True, slots=True)
class RiskCluster:
    tickers: tuple[str, ...]
    total_weight: float

    def to_dict(self) -> dict[str, Any]:
        return {"tickers": list(self.tickers), "totalWeight": self.total_weight}


@dataclass(frozen=True, slots=True)
class RiskReport:
    total_capital: float
    metrics: tuple[RiskMetric, ...]
    correlation_matrix: dict[str, dict[str, float]]
    sector_exposure: dict[str, float]
    sector_breach_warnings: tuple[str, ...]
    cluster_warnings: tuple[str, ...]
    blocked_high_vol: tuple[str, ...]
    clusters: tuple[RiskCluster, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "totalCapital": self.total_capital,
            "metrics": [
                {
                    "ticker": metric.ticker,
                    "annualizedVol": metric.annualized_vol,
                    "beta": metric.beta,
                    "valueAtRisk95": metric.value_at_risk_95,
                    "maxDrawdown": metric.max_drawdown,
                    "sizeFactor": metric.size_factor,
                    "momentum121": metric.momentum_12_1,
                    "blockedHighVol": metric.blocked_high_vol,
                    "sector": metric.sector,
                    "weight": metric.weight,
                }
                for metric in self.metrics
            ],
            "correlationMatrix": self.correlation_matrix,
            "sectorExposure": self.sector_exposure,
            "sectorBreachWarnings": list(self.sector_breach_warnings),
            "clusterWarnings": list(self.cluster_warnings),
            "blockedHighVol": list(self.blocked_high_vol),
            "clusters": [cluster.to_dict() for cluster in self.clusters],
        }


def _returns_from_bars(bars: list[PriceBar]) -> list[float]:
    returns: list[float] = []
    for previous, current in zip(bars, bars[1:]):
        if previous.close == 0:
            continue
        returns.append(float((current.close - previous.close) / previous.close))
    return returns


def _annualized_volatility(returns: list[float]) -> float | None:
    if len(returns) < 2:
        return None
    return pstdev(returns) * math.sqrt(252)


def _historical_var_95(returns: list[float]) -> float | None:
    if len(returns) < 5:
        return None
    ordered = sorted(returns)
    index = max(int(math.floor(0.05 * len(ordered))) - 1, 0)
    return ordered[index]


def _max_drawdown_from_prices(bars: list[PriceBar]) -> float | None:
    if len(bars) < 2:
        return None
    peak = float(bars[0].close)
    max_drawdown = 0.0
    for bar in bars:
        price = float(bar.close)
        peak = max(peak, price)
        if peak == 0:
            continue
        drawdown = (price - peak) / peak
        max_drawdown = min(max_drawdown, drawdown)
    return max_drawdown


def _correlation(left: list[float], right: list[float]) -> float:
    if len(left) < 2 or len(right) < 2 or len(left) != len(right):
        return 0.0
    left_mean = mean(left)
    right_mean = mean(right)
    left_var = sum((value - left_mean) ** 2 for value in left)
    right_var = sum((value - right_mean) ** 2 for value in right)
    if left_var == 0 or right_var == 0:
        return 0.0
    covariance = sum((lv - left_mean) * (rv - right_mean) for lv, rv in zip(left, right))
    return covariance / math.sqrt(left_var * right_var)


def _beta(asset_returns: list[float], benchmark_returns: list[float]) -> float | None:
    if len(asset_returns) < 2 or len(asset_returns) != len(benchmark_returns):
        return None
    benchmark_mean = mean(benchmark_returns)
    benchmark_var = sum((value - benchmark_mean) ** 2 for value in benchmark_returns)
    if benchmark_var == 0:
        return None
    asset_mean = mean(asset_returns)
    covariance = sum(
        (asset - asset_mean) * (benchmark - benchmark_mean)
        for asset, benchmark in zip(asset_returns, benchmark_returns)
    )
    return covariance / benchmark_var


def _momentum_12_1(bars: list[PriceBar]) -> float | None:
    if len(bars) < 22:
        return None
    if len(bars) < 252:
        base = float(bars[0].close)
        recent = float(bars[-22].close)
    else:
        base = float(bars[-252].close)
        recent = float(bars[-22].close)
    if base == 0:
        return None
    return (recent - base) / base


def _simple_clusters(correlation_matrix: dict[str, dict[str, float]], weights: dict[str, float]) -> list[RiskCluster]:
    remaining = set(correlation_matrix.keys())
    clusters: list[RiskCluster] = []
    while remaining:
        ticker = sorted(remaining)[0]
        stack = [ticker]
        cluster: set[str] = set()
        while stack:
            current = stack.pop()
            if current in cluster:
                continue
            cluster.add(current)
            for other, corr in correlation_matrix.get(current, {}).items():
                if other in remaining and corr > 0.75:
                    stack.append(other)
        remaining -= cluster
        total_weight = sum(weights.get(member, 0.0) for member in cluster)
        clusters.append(RiskCluster(tickers=tuple(sorted(cluster)), total_weight=round(total_weight, 6)))
    return clusters


def assess_portfolio_risk(
    allocations: dict[str, float],
    *,
    repo_root: Path | None = None,
    vol_threshold: float = 0.80,
) -> RiskReport:
    repository = TradingRepository(repo_root or Path(__file__).resolve().parent.parent)
    tickers = sorted({ticker.upper() for ticker, value in allocations.items() if value > 0})
    total_capital = float(sum(allocations.values()))
    weights = {ticker: float(allocations[ticker]) / float(total_capital or 1) for ticker in tickers}

    daily_prices = repository.load_daily_prices(tickers + ["SPY"], limit_per_ticker=260)
    profiles = repository.load_company_profiles(tickers)
    benchmark_returns = _returns_from_bars(daily_prices.get("SPY", [])[-61:])

    correlation_matrix: dict[str, dict[str, float]] = {}
    metrics: list[RiskMetric] = []
    blocked: list[str] = []
    sector_exposure: dict[str, float] = {}
    returns_by_ticker = {ticker: _returns_from_bars(daily_prices.get(ticker, [])[-61:]) for ticker in tickers}

    for ticker in tickers:
        profile = profiles.get(ticker)
        sector = profile.sector if profile else None
        sector_key = sector or "Unknown"
        sector_exposure[sector_key] = sector_exposure.get(sector_key, 0.0) + weights[ticker]

        annualized_vol = _annualized_volatility(returns_by_ticker[ticker][-20:] or returns_by_ticker[ticker])
        metric = RiskMetric(
            ticker=ticker,
            annualized_vol=annualized_vol,
            beta=_beta(returns_by_ticker[ticker], benchmark_returns) if benchmark_returns else None,
            value_at_risk_95=_historical_var_95(returns_by_ticker[ticker]),
            max_drawdown=_max_drawdown_from_prices(daily_prices.get(ticker, [])[-60:]),
            size_factor=math.log(profile.market_cap_value) if profile and profile.market_cap_value and profile.market_cap_value > 0 else None,
            momentum_12_1=_momentum_12_1(daily_prices.get(ticker, [])),
            blocked_high_vol=bool(annualized_vol is not None and annualized_vol > vol_threshold),
            sector=sector,
            weight=round(weights[ticker], 6),
        )
        if metric.blocked_high_vol:
            blocked.append(ticker)
        metrics.append(metric)

    for left in tickers:
        correlation_matrix[left] = {}
        for right in tickers:
            if left == right:
                correlation_matrix[left][right] = 1.0
                continue
            left_series = returns_by_ticker[left]
            right_series = returns_by_ticker[right]
            overlap = min(len(left_series), len(right_series))
            correlation_matrix[left][right] = round(
                _correlation(left_series[-overlap:], right_series[-overlap:]) if overlap > 1 else 0.0,
                6,
            )

    clusters = _simple_clusters(correlation_matrix, weights)
    cluster_warnings = tuple(
        f"Cluster {', '.join(cluster.tickers)} exceeds 40% capital concentration ({cluster.total_weight:.1%})."
        for cluster in clusters
        if cluster.total_weight > 0.40 and len(cluster.tickers) > 1
    )
    sector_warnings = tuple(
        f"Sector {sector} exceeds 35% capital concentration ({weight:.1%})."
        for sector, weight in sorted(sector_exposure.items())
        if weight > 0.35
    )

    return RiskReport(
        total_capital=round(total_capital, 6),
        metrics=tuple(metrics),
        correlation_matrix=correlation_matrix,
        sector_exposure={sector: round(weight, 6) for sector, weight in sector_exposure.items()},
        sector_breach_warnings=sector_warnings,
        cluster_warnings=cluster_warnings,
        blocked_high_vol=tuple(sorted(blocked)),
        clusters=tuple(clusters),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Assess deterministic portfolio risk for a set of tickers.")
    parser.add_argument("--tickers", required=True, help="Comma-separated tickers.")
    parser.add_argument("--capital", type=float, default=1000.0)
    args = parser.parse_args()

    tickers = [ticker.strip().upper() for ticker in args.tickers.split(",") if ticker.strip()]
    if not tickers:
        raise SystemExit("No tickers provided.")
    per_ticker = args.capital / len(tickers)
    report = assess_portfolio_risk({ticker: per_ticker for ticker in tickers})
    print(json.dumps(report.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
