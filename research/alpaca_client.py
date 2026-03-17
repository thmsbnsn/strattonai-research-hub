"""Minimal Alpaca client wrapper for StrattonAI paper-first trading workflows."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:  # pragma: no cover - optional dependency
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None

from ingestion.write_to_supabase import load_ingestion_environment


@dataclass(frozen=True, slots=True)
class AlpacaConfig:
    api_key: str
    secret_key: str
    base_url: str
    mode: str
    live_confirmed: bool


def load_alpaca_config(repo_root: Path | None = None) -> AlpacaConfig:
    root = repo_root or Path(__file__).resolve().parent.parent
    load_ingestion_environment(root)
    api_key = os.environ.get("ALPACA_API_KEY", "")
    secret_key = os.environ.get("ALPACA_SECRET_KEY", "")
    base_url = os.environ.get("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    mode = os.environ.get("ALPACA_MODE", "paper").lower()
    live_confirmed = os.environ.get("ALPACA_LIVE_CONFIRMED", "").lower() == "true"
    if not api_key or not secret_key:
        raise RuntimeError("Alpaca credentials are not configured.")
    return AlpacaConfig(api_key=api_key, secret_key=secret_key, base_url=base_url, mode=mode, live_confirmed=live_confirmed)


def _request(method: str, path: str, *, query: dict[str, Any] | None = None, body: dict[str, Any] | None = None, repo_root: Path | None = None) -> Any:
    config = load_alpaca_config(repo_root)
    if config.mode == "live" and not config.live_confirmed and method in {"POST", "DELETE"}:
        raise RuntimeError("Live Alpaca mode is configured but ALPACA_LIVE_CONFIRMED=true is not set.")
    url = f"{config.base_url.rstrip('/')}{path}"
    if query:
        url = f"{url}?{urlencode(query)}"
    request = Request(
        url,
        headers={
            "APCA-API-KEY-ID": config.api_key,
            "APCA-API-SECRET-KEY": config.secret_key,
            "Content-Type": "application/json",
            "User-Agent": "StrattonAI/1.0",
        },
        method=method,
        data=json.dumps(body).encode("utf-8") if body is not None else None,
    )
    try:
        with urlopen(request, timeout=60) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return json.loads(raw) if raw else {}
    except HTTPError as error:  # pragma: no cover - live network path
        raw = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(raw or f"Alpaca request failed with status {error.code}") from error


def get_account(repo_root: Path | None = None) -> dict[str, Any]:
    return _request("GET", "/v2/account", repo_root=repo_root)


def get_positions(repo_root: Path | None = None) -> list[dict[str, Any]]:
    return _request("GET", "/v2/positions", repo_root=repo_root)


def get_orders(status: str = "open", repo_root: Path | None = None) -> list[dict[str, Any]]:
    return _request("GET", "/v2/orders", query={"status": status}, repo_root=repo_root)


def submit_order(
    ticker: str,
    qty: float,
    side: str,
    order_type: str = "market",
    time_in_force: str = "day",
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    return _request(
        "POST",
        "/v2/orders",
        body={
            "symbol": ticker.upper(),
            "qty": round(float(qty), 6),
            "side": side,
            "type": order_type,
            "time_in_force": time_in_force,
        },
        repo_root=repo_root,
    )


def cancel_order(order_id: str, repo_root: Path | None = None) -> dict[str, Any]:
    return _request("DELETE", f"/v2/orders/{order_id}", repo_root=repo_root)


def list_assets(*, repo_root: Path | None = None) -> list[dict[str, Any]]:
    return _request(
        "GET",
        "/v2/assets",
        query={"status": "active", "asset_class": "us_equity"},
        repo_root=repo_root,
    )


def get_bars(ticker: str, timeframe: str = "1Day", limit: int = 60, *, repo_root: Path | None = None):
    data = _request(
        "GET",
        f"/v2/stocks/{ticker.upper()}/bars",
        query={"timeframe": timeframe, "limit": limit},
        repo_root=repo_root,
    )
    bars = data.get("bars", data if isinstance(data, list) else [])
    if pd is None:  # pragma: no cover
        raise RuntimeError("pandas is required for Alpaca bar frame output.")
    return pd.DataFrame(bars)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Alpaca account connectivity.")
    parser.add_argument("--resource", choices=["account", "positions", "orders"], default="account")
    args = parser.parse_args()
    if args.resource == "account":
        payload = get_account()
    elif args.resource == "positions":
        payload = get_positions()
    else:
        payload = get_orders()
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
