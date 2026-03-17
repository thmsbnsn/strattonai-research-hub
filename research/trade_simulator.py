"""Signal-driven deterministic paper-trade simulation."""

from __future__ import annotations

import argparse
import json
from datetime import timedelta
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from .risk_gate import apply_risk_gate
from .risk_engine import assess_portfolio_risk
from .trading_repository import TradingRepository
from .transaction_costs import TransactionCostConfig, compute_round_trip_cost


TRADE_SIM_NAMESPACE = uuid5(NAMESPACE_URL, "strattonai/trade-simulator")
HOLD_DAYS = {"1D": 1, "3D": 3, "5D": 5, "10D": 10, "20D": 20}


def _deterministic_trade_id(signal_key: str, capital_allocation: float, universe: str = "main") -> str:
    return str(uuid5(TRADE_SIM_NAMESPACE, f"{signal_key}|{capital_allocation:.4f}|{universe}"))


def simulate_trade(
    signal_key: str,
    capital_allocation: float,
    *,
    repo_root: Path | None = None,
    dry_run: bool = False,
    show_costs: bool = False,
    metadata_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    repository = TradingRepository(repo_root or Path(__file__).resolve().parent.parent)
    signals = repository.load_signal_scores(signal_keys=[signal_key])
    if not signals:
        raise ValueError(f"Signal {signal_key} was not found.")

    signal = signals[0]
    latest_price = repository.latest_daily_price(signal["target_ticker"])
    if latest_price is None:
        return {"success": False, "status": "missing-price", "signalKey": signal_key, "error": "No daily_prices row found."}

    entry_price = float(latest_price.close)
    shares = float(capital_allocation) / float(entry_price or 1)
    direction = "Long" if signal["avg_return"] >= 0 else "Short"
    projected_exit_price = entry_price * (1.0 + signal["avg_return"] / 100.0)
    hold_days = HOLD_DAYS.get(signal["horizon"], 5)

    existing_allocations = {
        trade.ticker: float(trade.entry_price * trade.quantity)
        for trade in repository.load_paper_trades(statuses=["simulated", "open", "Open"])
    }
    existing_allocations[signal["target_ticker"]] = existing_allocations.get(signal["target_ticker"], 0.0) + capital_allocation
    risk_report = assess_portfolio_risk(existing_allocations, repo_root=repo_root)
    risk_gate = apply_risk_gate(signal["target_ticker"], capital_allocation, existing_allocations, repo_root=repo_root)
    trade_id = _deterministic_trade_id(signal_key, capital_allocation)

    if not risk_gate.approved:
        payload = {
            "success": False,
            "status": "risk-blocked",
            "signalKey": signal_key,
            "ticker": signal["target_ticker"],
            "riskReport": risk_report.to_dict(),
            "riskGate": risk_gate.to_dict(),
        }
        if not dry_run:
            repository.upsert_paper_trade(
                {
                    "id": trade_id,
                    "ticker": signal["target_ticker"],
                    "direction": direction,
                    "signal": signal["evidence_summary"],
                    "entry_price": entry_price,
                    "current_price": entry_price,
                    "entry_date": latest_price.trade_date,
                    "quantity": shares,
                    "status": "risk-blocked",
                    "mode": "simulated",
                    "metadata": {
                        "signal_key": signal_key,
                        "risk_report": risk_report.to_dict(),
                        "risk_gate": risk_gate.to_dict(),
                        "hold_days": hold_days,
                        "horizon": signal["horizon"],
                        "score": signal["score"],
                        **(metadata_overrides or {}),
                    },
                    "alpaca_order_id": None,
                    "exit_price": None,
                    "exit_date": None,
                    "realized_pnl": None,
                    "universe": "main",
                }
            )
        return payload

    costs = compute_round_trip_cost(
        signal["target_ticker"],
        shares,
        entry_price,
        TransactionCostConfig(),
        repo_root=repo_root,
    )
    gross_pnl = (projected_exit_price - entry_price) * shares if direction == "Long" else (entry_price - projected_exit_price) * shares
    net_pnl = gross_pnl - costs.total_cost_dollars
    payload = {
        "success": True,
        "status": "simulated",
        "id": trade_id,
        "signalKey": signal_key,
        "ticker": signal["target_ticker"],
        "direction": direction,
        "entryPrice": round(entry_price, 6),
        "exitPrice": round(projected_exit_price, 6),
        "shares": round(shares, 6),
        "holdDays": hold_days,
        "grossPnl": round(gross_pnl, 6),
        "netPnl": round(net_pnl, 6),
        "costs": costs.to_dict() if show_costs or True else None,
        "riskReport": risk_report.to_dict(),
        "riskGate": risk_gate.to_dict(),
    }

    if dry_run:
        return payload

    repository.upsert_paper_trade(
        {
            "id": trade_id,
            "ticker": signal["target_ticker"],
            "direction": direction,
            "signal": signal["evidence_summary"],
            "entry_price": entry_price,
            "current_price": projected_exit_price,
            "entry_date": latest_price.trade_date,
            "quantity": shares,
            "status": "simulated",
            "mode": "simulated",
            "metadata": {
                "signal_key": signal_key,
                "signal_snapshot": signal,
                "hold_days": hold_days,
                "transaction_costs": costs.to_dict(),
                "risk_report": risk_report.to_dict(),
                "risk_gate": risk_gate.to_dict(),
                "projected_exit_date": (latest_price.trade_date + timedelta(days=hold_days)).isoformat(),
                **(metadata_overrides or {}),
            },
            "alpaca_order_id": None,
            "exit_price": projected_exit_price,
            "exit_date": latest_price.trade_date + timedelta(days=hold_days),
            "realized_pnl": net_pnl,
            "universe": "main",
        }
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulate a deterministic paper trade from a scored signal.")
    parser.add_argument("--signal-key", required=True)
    parser.add_argument("--capital", type=float, required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--show-costs", action="store_true")
    args = parser.parse_args()

    result = simulate_trade(
        args.signal_key,
        args.capital,
        dry_run=args.dry_run,
        show_costs=args.show_costs,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
