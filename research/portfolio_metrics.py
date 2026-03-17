"""Compute deterministic portfolio monitoring metrics from paper trades."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from .trading_repository import PaperTradeRecord, TradingRepository


@dataclass(frozen=True, slots=True)
class EquityPoint:
    date: str
    cumulative_pnl: float


@dataclass(frozen=True, slots=True)
class PortfolioMetrics:
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    turnover: float
    equity_curve: tuple[EquityPoint, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "sharpeRatio": self.sharpe_ratio,
            "sortinoRatio": self.sortino_ratio,
            "maxDrawdown": self.max_drawdown,
            "turnover": self.turnover,
            "equityCurve": [
                {
                    "date": point.date,
                    "cumulativePnl": point.cumulative_pnl,
                }
                for point in self.equity_curve
            ],
        }


def _trade_pnl(trade: PaperTradeRecord) -> float:
    if trade.realized_pnl is not None:
        return float(trade.realized_pnl)
    current = float(trade.current_price or trade.entry_price)
    entry = float(trade.entry_price)
    qty = float(trade.quantity)
    if trade.direction.lower() == "short":
        return (entry - current) * qty
    return (current - entry) * qty


def _hold_days(trade: PaperTradeRecord) -> int:
    if trade.exit_date:
        return max((trade.exit_date - trade.entry_date).days, 1)
    metadata = trade.metadata or {}
    return max(int(metadata.get("hold_days", 1)), 1)


def compute_portfolio_metrics(*, repo_root: Path | None = None) -> PortfolioMetrics:
    repository = TradingRepository(repo_root or Path(__file__).resolve().parent.parent)
    trades = repository.load_paper_trades(statuses=["simulated", "open", "closed", "Open", "Closed"])
    if not trades:
        return PortfolioMetrics(0.0, 0.0, 0.0, 0.0, ())

    daily_returns: list[float] = []
    downside_returns: list[float] = []
    equity_curve: list[EquityPoint] = []
    cumulative_pnl = 0.0
    trade_values: list[float] = []
    portfolio_values: list[float] = []

    for trade in sorted(trades, key=lambda item: item.entry_date):
        pnl = _trade_pnl(trade)
        gross_value = float(trade.entry_price * trade.quantity)
        per_day_return = pnl / gross_value / _hold_days(trade) if gross_value else 0.0
        daily_returns.append(per_day_return)
        if per_day_return < 0:
            downside_returns.append(per_day_return)
        cumulative_pnl += pnl
        equity_curve.append(EquityPoint(date=trade.entry_date.isoformat(), cumulative_pnl=round(cumulative_pnl, 6)))
        trade_values.append(abs(gross_value))
        portfolio_values.append(max(gross_value + cumulative_pnl, gross_value))

    mean_daily_return = mean(daily_returns) if daily_returns else 0.0
    std_daily_return = pstdev(daily_returns) if len(daily_returns) > 1 else 0.0
    downside_std = pstdev(downside_returns) if len(downside_returns) > 1 else 0.0
    sharpe = ((mean_daily_return - 0.0) / std_daily_return) * math.sqrt(252) if std_daily_return else 0.0
    sortino = ((mean_daily_return - 0.0) / downside_std) * math.sqrt(252) if downside_std else 0.0

    peak = equity_curve[0].cumulative_pnl if equity_curve else 0.0
    max_drawdown = 0.0
    for point in equity_curve:
        peak = max(peak, point.cumulative_pnl)
        denominator = abs(peak) if abs(peak) > 1e-9 else 1.0
        drawdown = (point.cumulative_pnl - peak) / denominator
        max_drawdown = min(max_drawdown, drawdown)

    turnover = (sum(trade_values) / (mean(portfolio_values) if portfolio_values else 1.0)) if trade_values else 0.0

    return PortfolioMetrics(
        sharpe_ratio=round(sharpe, 6),
        sortino_ratio=round(sortino, 6),
        max_drawdown=round(max_drawdown, 6),
        turnover=round(turnover, 6),
        equity_curve=tuple(equity_curve),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute deterministic portfolio monitoring metrics.")
    parser.parse_args()
    metrics = compute_portfolio_metrics()
    print(json.dumps(metrics.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
