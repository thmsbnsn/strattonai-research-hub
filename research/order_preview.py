"""Deterministic order preview builder for StrattonAI trading workflows."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .alpaca_client import get_bars
from .market_regime import get_current_regime
from .risk_gate import apply_risk_gate
from .trading_repository import TradingRepository
from .transaction_costs import TransactionCostBreakdown, compute_round_trip_cost


@dataclass(frozen=True, slots=True)
class OrderPreview:
    ticker: str
    side: str
    qty: float
    estimated_entry_price: float
    estimated_shares_value: float
    transaction_cost: TransactionCostBreakdown
    net_cost_after_fees: float
    buying_power_remaining: float
    risk_flags: list[str]
    regime_label: str
    approved: bool
    rejection_reason: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticker": self.ticker,
            "side": self.side,
            "qty": self.qty,
            "estimatedEntryPrice": self.estimated_entry_price,
            "estimatedSharesValue": self.estimated_shares_value,
            "transactionCost": self.transaction_cost.to_dict(),
            "netCostAfterFees": self.net_cost_after_fees,
            "buyingPowerRemaining": self.buying_power_remaining,
            "riskFlags": self.risk_flags,
            "regimeLabel": self.regime_label,
            "approved": self.approved,
            "rejectionReason": self.rejection_reason,
        }


def _latest_price(ticker: str, *, repo_root: Path) -> float:
    repository = TradingRepository(repo_root)
    latest = repository.latest_daily_price(ticker)
    if latest is not None:
        return float(latest.close)
    bars = get_bars(ticker, limit=1, repo_root=repo_root)
    if hasattr(bars, "empty") and not bars.empty:
        return float(bars.iloc[-1].get("c") or bars.iloc[-1].get("close") or 0.0)
    raise ValueError(f"No latest price is available for {ticker}.")


def build_order_preview(
    ticker: str,
    side: str,
    qty: float,
    account_state: dict[str, Any],
    regime: str | None = None,
    *,
    current_portfolio_allocations: dict[str, float] | None = None,
    repo_root: Path | None = None,
) -> OrderPreview:
    root = repo_root or Path(__file__).resolve().parent.parent
    normalized_ticker = ticker.upper()
    price = _latest_price(normalized_ticker, repo_root=root)
    shares_value = float(qty) * price
    transaction_cost = compute_round_trip_cost(normalized_ticker, qty, price, repo_root=root)
    total_cost = shares_value + transaction_cost.total_cost_dollars
    buying_power = float(account_state.get("buying_power") or account_state.get("buyingPower") or 0.0)
    buying_power_remaining = buying_power - total_cost
    regime_label = regime or get_current_regime(repo_root=root, persist=True).label

    risk_gate = apply_risk_gate(
        normalized_ticker,
        shares_value,
        current_portfolio_allocations or {},
        repo_root=root,
    )
    risk_flags = [*risk_gate.hard_blocks, *risk_gate.soft_warnings]
    rejection_reason: str | None = None
    approved = risk_gate.approved
    if buying_power_remaining < 0:
        approved = False
        rejection_reason = "insufficient_buying_power"
    elif not risk_gate.approved:
        rejection_reason = risk_gate.hard_blocks[0] if risk_gate.hard_blocks else "risk_gate_blocked"

    return OrderPreview(
        ticker=normalized_ticker,
        side=side,
        qty=float(qty),
        estimated_entry_price=round(price, 6),
        estimated_shares_value=round(shares_value, 6),
        transaction_cost=transaction_cost,
        net_cost_after_fees=round(total_cost, 6),
        buying_power_remaining=round(buying_power_remaining, 6),
        risk_flags=risk_flags,
        regime_label=regime_label,
        approved=approved,
        rejection_reason=rejection_reason,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview a proposed order with costs and risk-gate checks.")
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--side", choices=["buy", "sell"], required=True)
    parser.add_argument("--qty", type=float, required=True)
    parser.add_argument("--buying-power", type=float, default=0.0)
    args = parser.parse_args()

    preview = build_order_preview(
        args.ticker,
        args.side,
        args.qty,
        {"buying_power": args.buying_power},
    )
    print(json.dumps(preview.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
