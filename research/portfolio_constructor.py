"""Deterministic portfolio-construction methods for scored StrattonAI signals."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from uuid import NAMESPACE_URL, uuid5

from .order_preview import build_order_preview
from .risk_gate import apply_risk_gate
from .risk_engine import assess_portfolio_risk
from .trade_simulator import simulate_trade
from .trading_repository import TradingRepository

try:  # pragma: no cover - optional dependency
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

try:  # pragma: no cover - optional dependency
    from scipy.optimize import minimize
except ImportError:  # pragma: no cover
    minimize = None


PORTFOLIO_RUN_NAMESPACE = uuid5(NAMESPACE_URL, "strattonai/portfolio-constructor")


@dataclass(frozen=True, slots=True)
class AllocationSimulationResult:
    run_id: str
    method: str
    capital: float
    total_allocated: float
    allocations: list[dict[str, Any]]
    simulated: list[dict[str, Any]]
    risk_blocked: list[dict[str, Any]]
    risk_warnings: list[str]
    dry_run: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "runId": self.run_id,
            "method": self.method,
            "capital": self.capital,
            "totalAllocated": self.total_allocated,
            "allocations": self.allocations,
            "simulated": self.simulated,
            "riskBlocked": self.risk_blocked,
            "riskWarnings": self.risk_warnings,
            "dryRun": self.dry_run,
        }


def _returns_matrix(repository: TradingRepository, tickers: list[str], lookback: int = 60) -> dict[str, list[float]]:
    bars = repository.load_daily_prices(tickers, limit_per_ticker=lookback + 1)
    matrix: dict[str, list[float]] = {}
    for ticker in tickers:
        series = bars.get(ticker, [])
        returns: list[float] = []
        for previous, current in zip(series, series[1:]):
            if previous.close == 0:
                continue
            returns.append(float((current.close - previous.close) / previous.close))
        matrix[ticker] = returns
    return matrix


def _normalize_with_cap(raw_weights: dict[str, float], cap: float) -> dict[str, float]:
    positive = {ticker: max(weight, 0.0) for ticker, weight in raw_weights.items()}
    total = sum(positive.values())
    if total <= 0:
        equal = 1.0 / max(len(raw_weights), 1)
        return {ticker: min(equal, cap) for ticker in raw_weights}

    normalized = {ticker: weight / total for ticker, weight in positive.items()}
    capped = {ticker: min(weight, cap) for ticker, weight in normalized.items()}
    total_after = sum(capped.values()) or 1.0
    return {ticker: weight / total_after for ticker, weight in capped.items()}


def mean_variance_allocation(signals: list[dict[str, Any]], total_capital: float, repository: TradingRepository) -> dict[str, float]:
    unique = {signal["target_ticker"]: signal for signal in signals}
    tickers = sorted(unique)
    expected = [unique[ticker]["avg_return"] / 100.0 for ticker in tickers]
    returns = _returns_matrix(repository, tickers)

    if np is None or minimize is None or len(tickers) == 1:
        weights = _normalize_with_cap({ticker: max(unique[ticker]["score"], 0.0) for ticker in tickers}, 0.25)
        return {ticker: round(weight * total_capital, 6) for ticker, weight in weights.items()}

    min_overlap = min((len(returns[ticker]) for ticker in tickers), default=0)
    if min_overlap < 2:
        weights = _normalize_with_cap({ticker: max(unique[ticker]["score"], 0.0) for ticker in tickers}, 0.25)
        return {ticker: round(weight * total_capital, 6) for ticker, weight in weights.items()}

    matrix = np.array([returns[ticker][-min_overlap:] for ticker in tickers])
    covariance = np.cov(matrix)
    expected_vector = np.array(expected)

    def objective(weights: Any) -> float:
        portfolio_return = float(np.dot(weights, expected_vector))
        portfolio_vol = float(np.sqrt(np.dot(weights.T, np.dot(covariance, weights)))) or 1e-9
        return -(portfolio_return / portfolio_vol)

    initial = np.array([1.0 / len(tickers)] * len(tickers))
    bounds = [(0.0, 0.25)] * len(tickers)
    constraints = ({"type": "eq", "fun": lambda weights: np.sum(weights) - 1.0},)
    result = minimize(objective, initial, method="SLSQP", bounds=bounds, constraints=constraints)
    if not result.success:
        weights = _normalize_with_cap({ticker: max(unique[ticker]["score"], 0.0) for ticker in tickers}, 0.25)
    else:
        weights = {ticker: float(weight) for ticker, weight in zip(tickers, result.x)}
        weights = _normalize_with_cap(weights, 0.25)
    return {ticker: round(weight * total_capital, 6) for ticker, weight in weights.items()}


def kelly_allocation(signals: list[dict[str, Any]], total_capital: float) -> dict[str, float]:
    unique = {signal["target_ticker"]: signal for signal in signals}
    fractions: dict[str, float] = {}
    for ticker, signal in unique.items():
        win_rate = max(min(float(signal["win_rate"]) / 100.0, 0.99), 0.01)
        avg_return = float(signal["avg_return"]) / 100.0
        if avg_return == 0:
            fractions[ticker] = 0.0
            continue
        avg_return_loss = abs(avg_return * 0.5) or 0.01
        edge_ratio = abs(avg_return) / avg_return_loss
        fraction = win_rate - ((1 - win_rate) / edge_ratio)
        fractions[ticker] = max(fraction * 0.25, 0.0)
    weights = _normalize_with_cap(fractions, 0.20)
    return {ticker: round(weight * total_capital, 6) for ticker, weight in weights.items()}


def risk_parity_allocation(signals: list[dict[str, Any]], total_capital: float, repository: TradingRepository) -> dict[str, float]:
    unique = {signal["target_ticker"]: signal for signal in signals}
    tickers = sorted(unique)
    returns = _returns_matrix(repository, tickers)
    inverse_vol: dict[str, float] = {}
    for ticker in tickers:
        series = returns.get(ticker, [])
        volatility = (float(np.std(series)) if np is not None and series else None) or (math.sqrt(sum(value * value for value in series) / len(series)) if series else 0.0)
        inverse_vol[ticker] = 1.0 / volatility if volatility else 1.0
    weights = _normalize_with_cap(inverse_vol, 1.0)
    return {ticker: round(weight * total_capital, 6) for ticker, weight in weights.items()}


def construct_portfolio(
    method: str,
    total_capital: float,
    *,
    signal_keys: Iterable[str] | None = None,
    repo_root: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    repository = TradingRepository(repo_root or Path(__file__).resolve().parent.parent)
    signals = repository.load_signal_scores(signal_keys=signal_keys)
    if not signals:
        return {"success": False, "data": {"allocations": []}, "error": "No signals were resolved for portfolio construction."}

    unique_signals = {}
    for signal in signals:
        existing = unique_signals.get(signal["target_ticker"])
        if existing is None or signal["score"] > existing["score"]:
            unique_signals[signal["target_ticker"]] = signal
    signal_list = list(unique_signals.values())

    normalized_method = method.lower()
    if normalized_method == "mean-variance":
        allocations = mean_variance_allocation(signal_list, total_capital, repository)
    elif normalized_method == "kelly":
        allocations = kelly_allocation(signal_list, total_capital)
    elif normalized_method == "risk-parity":
        allocations = risk_parity_allocation(signal_list, total_capital, repository)
    else:
        raise ValueError(f"Unsupported portfolio construction method: {method}")

    run_id = str(uuid5(PORTFOLIO_RUN_NAMESPACE, f"{normalized_method}|{total_capital:.4f}|{'|'.join(sorted(signal['signal_key'] for signal in signal_list))}"))
    signal_key_map = {signal["target_ticker"]: signal["signal_key"] for signal in signal_list}
    rows = [
        {
            "ticker": ticker,
            "allocationDollars": round(allocation, 6),
            "weight": round(allocation / float(total_capital or 1), 6),
            "method": normalized_method,
            "signalKey": signal_key_map.get(ticker),
        }
        for ticker, allocation in sorted(allocations.items())
    ]
    if not dry_run:
        repository.upsert_portfolio_allocations(
            run_id=run_id,
            method=normalized_method,
            allocations=allocations,
            capital_total=total_capital,
            signal_keys=signal_key_map,
        )
    return {"success": True, "data": {"runId": run_id, "method": normalized_method, "capital": total_capital, "allocations": rows}, "error": None}


def allocate_and_simulate(
    method: str,
    capital: float,
    signal_keys: list[str],
    dry_run: bool = True,
    *,
    repo_root: Path | None = None,
) -> AllocationSimulationResult:
    root = repo_root or Path(__file__).resolve().parent.parent
    constructed = construct_portfolio(method, capital, signal_keys=signal_keys, repo_root=root, dry_run=dry_run)
    allocations = list(constructed["data"]["allocations"])
    repository = TradingRepository(root)
    signal_lookup = {signal["signal_key"]: signal for signal in repository.load_signal_scores(signal_keys=signal_keys)}
    allocation_map = {row["ticker"]: float(row["allocationDollars"]) for row in allocations}
    run_id = str(uuid5(PORTFOLIO_RUN_NAMESPACE, f"simulate|{method}|{capital:.4f}|{'|'.join(sorted(signal_keys))}"))
    advisory_report = assess_portfolio_risk(allocation_map, repo_root=root)
    risk_warnings = [
        *advisory_report.sector_breach_warnings,
        *advisory_report.cluster_warnings,
    ]

    simulated: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for allocation in allocations:
        ticker = str(allocation["ticker"]).upper()
        dollars = float(allocation["allocationDollars"])
        signal_key = allocation.get("signalKey")
        if not signal_key:
            blocked.append({"ticker": ticker, "reason": "missing_signal_key"})
            continue
        gate = apply_risk_gate(ticker, dollars, allocation_map, repo_root=root)
        if not gate.approved:
            blocked.append({"ticker": ticker, "reason": "; ".join(gate.hard_blocks), "riskGate": gate.to_dict()})
            continue
        latest = repository.latest_daily_price(ticker)
        if latest is None:
            blocked.append({"ticker": ticker, "reason": "missing_latest_price"})
            continue
        preview = build_order_preview(
            ticker,
            "buy",
            dollars / max(float(latest.close), 0.01),
            {"buying_power": capital},
            current_portfolio_allocations=allocation_map,
            repo_root=root,
        )
        if not preview.approved:
            blocked.append({"ticker": ticker, "reason": preview.rejection_reason or "preview_rejected", "preview": preview.to_dict()})
            continue
        result = simulate_trade(
            signal_key,
            dollars,
            repo_root=root,
            dry_run=dry_run,
            show_costs=True,
            metadata_overrides={"run_id": run_id, "method": method},
        )
        if result.get("success"):
            simulated.append(
                {
                    "tradeId": result.get("id"),
                    "ticker": ticker,
                    "qty": result.get("shares"),
                    "entryPrice": result.get("entryPrice"),
                    "netCost": preview.net_cost_after_fees,
                    "transactionCostPct": preview.transaction_cost.total_cost_pct,
                    "signalKey": signal_key,
                }
            )
        else:
            blocked.append({"ticker": ticker, "reason": result.get("status", "simulation_failed"), "result": result})

    return AllocationSimulationResult(
        method=constructed["data"]["method"],
        run_id=run_id,
        capital=float(capital),
        total_allocated=round(sum(float(row["allocationDollars"]) for row in allocations), 6),
        allocations=allocations,
        simulated=simulated,
        risk_blocked=blocked,
        risk_warnings=risk_warnings,
        dry_run=dry_run,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Construct a deterministic portfolio from scored signals.")
    parser.add_argument("--method", choices=["mean-variance", "kelly", "risk-parity"], required=True)
    parser.add_argument("--capital", type=float, required=True)
    parser.add_argument("--signal-key", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = construct_portfolio(args.method, args.capital, signal_keys=args.signal_key, dry_run=args.dry_run)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
