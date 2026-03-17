"""Paper-first autonomous trading loop with explicit live-mode guardrails."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from .alpaca_client import get_account, get_orders, get_positions, load_alpaca_config, submit_order
from .market_regime import get_current_regime
from .penny_stock_signals import build_penny_stock_candidates
from .order_preview import build_order_preview
from .risk_engine import assess_portfolio_risk
from .trading_repository import TradingRepository
from .transaction_costs import compute_round_trip_cost


TRADING_LOOP_NAMESPACE = uuid5(NAMESPACE_URL, "strattonai/trading-loop")


def run_trading_loop(
    capital: float,
    universe: str,
    mode: str,
    max_positions: int = 5,
    max_position_pct: float = 0.25,
    dry_run: bool = True,
    *,
    repo_root: Path | None = None,
    job_id: str | None = None,
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parent.parent
    config = load_alpaca_config(root)
    if mode == "live" and not (config.mode == "live" and config.live_confirmed):
        raise RuntimeError("Live trading loop requires ALPACA_MODE=live and ALPACA_LIVE_CONFIRMED=true.")
    repository = TradingRepository(root)
    account = get_account(repo_root=root)
    positions = get_positions(repo_root=root)
    open_tickers = {str(position.get("symbol", "")).upper() for position in positions}
    buying_power = float(account.get("buying_power", capital) or capital)
    available_capital = min(float(capital), buying_power)
    loop_job_id = job_id or str(uuid5(TRADING_LOOP_NAMESPACE, f"{mode}|{universe}|{capital:.4f}|{dry_run}"))
    regime_label = get_current_regime(repo_root=root, persist=True).label

    if universe == "penny":
        candidates = [candidate.to_dict() for candidate in build_penny_stock_candidates(available_capital, repo_root=root, top_n=max_positions)]
    else:
        signal_rows = repository.load_signal_scores(confidence_bands=["High", "Moderate"])
        candidates = [
            {
                "ticker": signal["target_ticker"],
                "signal_type": signal["event_category"],
                "score": signal["score"],
                "entry_price": float(repository.latest_daily_price(signal["target_ticker"]).close) if repository.latest_daily_price(signal["target_ticker"]) else 0.0,
                "suggested_qty": 0.0,
                "estimated_cost": 0.0,
                "estimated_cost_pct": 0.0,
                "confidence_band": signal["confidence_band"],
                "signal_key": signal["signal_key"],
            }
            for signal in signal_rows[:max_positions * 2]
        ]

    executed: list[dict[str, Any]] = []
    rejection_reasons: Counter[str] = Counter()
    orders_previewed = 0
    orders_approved = 0
    orders_failed = 0
    for index, candidate in enumerate(candidates):
        ticker = str(candidate["ticker"]).upper()
        if ticker in open_tickers:
            rejection_reasons["already_open"] += 1
            continue
        position_value = min(available_capital * max_position_pct, available_capital / max(1, max_positions - index))
        allocation_map = {ticker: position_value}
        risk = assess_portfolio_risk(allocation_map, repo_root=root)
        if ticker in risk.blocked_high_vol:
            rejection_reasons["blocked_high_vol"] += 1
            continue
        entry_price = float(candidate.get("entry_price") or 0.0)
        if entry_price <= 0:
            rejection_reasons["missing_price"] += 1
            continue
        shares = max(position_value / entry_price, 0.0)
        cost = compute_round_trip_cost(ticker, shares, entry_price, repo_root=root)
        affordable_shares = max((position_value - cost.total_cost_dollars) / entry_price, 0.0)
        signal_key = candidate.get("signal_key") or f"{universe}:{ticker}"
        orders_previewed += 1
        preview = build_order_preview(
            ticker,
            "buy",
            round(affordable_shares, 6),
            account,
            regime=regime_label,
            current_portfolio_allocations={ticker: position_value},
            repo_root=root,
        )
        if not preview.approved:
            rejection_reasons[preview.rejection_reason or "risk_gate_blocked"] += 1
            continue
        orders_approved += 1
        order_payload = {"dryRun": dry_run, "ticker": ticker, "qty": round(affordable_shares, 6), "side": "buy"}
        order = None
        if not dry_run:
            try:
                order = submit_order(ticker, affordable_shares, "buy", repo_root=root)
            except Exception:
                orders_failed += 1
                rejection_reasons["submit_failed"] += 1
                continue

        trade_id = str(uuid5(TRADING_LOOP_NAMESPACE, f"{mode}|{universe}|{signal_key}|{position_value:.4f}"))
        repository.upsert_paper_trade(
            {
                "id": trade_id,
                "ticker": ticker,
                "direction": "Long",
                "signal": str(candidate.get("signal_type", "LoopCandidate")),
                "entry_price": entry_price,
                "current_price": entry_price,
                "entry_date": datetime.utcnow().date(),
                "quantity": affordable_shares,
                "status": "simulated" if dry_run else "open",
                "mode": mode,
                "metadata": {
                    "signal_key": signal_key,
                    "transaction_costs": cost.to_dict(),
                    "risk_report": risk.to_dict(),
                    "order_preview": preview.to_dict(),
                    "loop_mode": mode,
                    "dry_run": dry_run,
                    "job_id": loop_job_id,
                    "run_id": loop_job_id,
                },
                "alpaca_order_id": order.get("id") if order else None,
                "exit_price": None,
                "exit_date": None,
                "realized_pnl": None,
                "universe": universe,
            }
        )
        executed.append({"ticker": ticker, "shares": affordable_shares, "dryRun": dry_run, "order": order_payload if dry_run else order})

    account_after = get_account(repo_root=root)
    summary = {
        "job_id": loop_job_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "mode": mode,
        "universe": universe,
        "dry_run": dry_run,
        "capital": capital,
        "account_before": {
            "buying_power": account.get("buying_power"),
            "portfolio_value": account.get("portfolio_value") or account.get("equity"),
        },
        "candidates_evaluated": len(candidates),
        "orders_previewed": orders_previewed,
        "orders_approved": orders_approved,
        "orders_rejected": sum(rejection_reasons.values()),
        "rejection_reasons": dict(sorted(rejection_reasons.items())),
        "orders_submitted": len(executed),
        "orders_failed": orders_failed,
        "positions_exited": 0,
        "realized_pnl_this_run": 0.0,
        "account_after": {
            "buying_power": account_after.get("buying_power"),
            "portfolio_value": account_after.get("portfolio_value") or account_after.get("equity"),
        },
        "regime": regime_label,
        "error": None,
    }
    report_path = root / "reports" / f"trading_loop_run_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return {
        "success": True,
        "data": {
            "mode": mode,
            "universe": universe,
            "dryRun": dry_run,
            "account": account_after,
            "positions": positions,
            "executed": executed,
            "summary": summary,
            "jobId": loop_job_id,
        },
        "error": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the deterministic trading loop once.")
    parser.add_argument("--universe", choices=["penny", "main"], required=True)
    parser.add_argument("--capital", type=float, required=True)
    parser.add_argument("--mode", choices=["paper", "live"], required=True)
    parser.add_argument("--max-positions", type=int, default=5)
    parser.add_argument("--max-position-pct", type=float, default=0.25)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = run_trading_loop(
        capital=args.capital,
        universe=args.universe,
        mode=args.mode,
        max_positions=args.max_positions,
        max_position_pct=args.max_position_pct,
        dry_run=args.dry_run,
        job_id=None,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
