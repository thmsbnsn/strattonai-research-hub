"""Generate penny-stock trade candidates from existing signals plus deterministic momentum fallback."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from .penny_stock_universe import load_penny_stock_universe
from .risk_engine import assess_portfolio_risk
from .trading_repository import TradingRepository
from .transaction_costs import compute_round_trip_cost


@dataclass(frozen=True, slots=True)
class PennyStockSignalCandidate:
    ticker: str
    signal_type: str
    score: float
    entry_price: float
    suggested_qty: float
    estimated_cost: float
    estimated_cost_pct: float
    confidence_band: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticker": self.ticker,
            "signalType": self.signal_type,
            "score": self.score,
            "entryPrice": self.entry_price,
            "suggestedQty": self.suggested_qty,
            "estimatedCost": self.estimated_cost,
            "estimatedCostPct": self.estimated_cost_pct,
            "confidenceBand": self.confidence_band,
        }


def _momentum_signal_score(prices: list[float]) -> float:
    if len(prices) < 21:
        return 0.0
    return_5d = (prices[-1] - prices[-6]) / prices[-6] if prices[-6] else 0.0
    return_20d = (prices[-1] - prices[-21]) / prices[-21] if prices[-21] else 0.0
    if return_5d > 0.03 and return_20d > 0:
        return min(return_5d * 1000, 40.0)
    return 0.0


def build_penny_stock_candidates(
    capital: float,
    *,
    repo_root: Path | None = None,
    top_n: int = 10,
) -> list[PennyStockSignalCandidate]:
    root = repo_root or Path(__file__).resolve().parent.parent
    repository = TradingRepository(root)
    universe = load_penny_stock_universe(repo_root=root)
    universe_tickers = [candidate.ticker for candidate in universe]
    signal_rows = repository.load_signal_scores(ticker=None, confidence_bands=["High", "Moderate"])
    prices = repository.load_daily_prices(universe_tickers, limit_per_ticker=25)

    by_ticker: dict[str, dict[str, Any]] = {}
    for signal in signal_rows:
        target = signal["target_ticker"]
        existing = by_ticker.get(target)
        if existing is None or signal["score"] > existing["score"]:
            by_ticker[target] = signal

    candidates: list[PennyStockSignalCandidate] = []
    for universe_candidate in universe:
        signal = by_ticker.get(universe_candidate.ticker)
        score = 0.0
        signal_type = "Momentum"
        confidence_band = "Low"
        if signal is not None:
            score = float(signal["score"])
            signal_type = signal["event_category"]
            confidence_band = signal["confidence_band"]
        else:
            series = [float(bar.close) for bar in prices.get(universe_candidate.ticker, [])]
            score = _momentum_signal_score(series)
            if score <= 0 and not series:
                # OTC-derived universes may not have daily_prices coverage. Use the screener-provided
                # changePct as a deterministic momentum proxy.
                change_pct = float(getattr(universe_candidate, "change_pct", 0.0) or 0.0)
                if change_pct > 0:
                    score = min(change_pct * 1000.0, 25.0)
        if score <= 0:
            continue
        qty = max(capital / max(universe_candidate.last_price, 0.01), 0.0)
        cost = compute_round_trip_cost(universe_candidate.ticker, qty, universe_candidate.last_price, repo_root=root)
        risk = assess_portfolio_risk({universe_candidate.ticker: capital}, repo_root=root, vol_threshold=1.50)
        if universe_candidate.ticker in risk.blocked_high_vol:
            continue
        candidates.append(
            PennyStockSignalCandidate(
                ticker=universe_candidate.ticker,
                signal_type=signal_type,
                score=round(score, 6),
                entry_price=universe_candidate.last_price,
                suggested_qty=round(qty, 6),
                estimated_cost=cost.total_cost_dollars,
                estimated_cost_pct=cost.total_cost_pct,
                confidence_band=confidence_band,
            )
        )

    return sorted(candidates, key=lambda item: item.score, reverse=True)[:top_n]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build penny-stock trade candidates for paper-first execution.")
    parser.add_argument("--capital", type=float, required=True)
    parser.add_argument("--mode", default="paper")
    parser.add_argument("--top-n", type=int, default=10)
    args = parser.parse_args()
    candidates = build_penny_stock_candidates(args.capital, top_n=args.top_n)
    print(json.dumps([candidate.to_dict() for candidate in candidates], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
