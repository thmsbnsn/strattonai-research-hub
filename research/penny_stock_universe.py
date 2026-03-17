"""Build and cache a deterministic penny-stock candidate universe from Alpaca assets."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from .alpaca_client import get_bars, list_assets
from .trading_repository import TradingRepository


CACHE_PATH = Path("reports") / "penny_stock_universe.json"
OTC_UNIVERSE_PATH = Path("reports") / "otc_markets_universe.json"
ALLOWED_EXCHANGES = {"NYSE", "NASDAQ", "AMEX"}


@dataclass(frozen=True, slots=True)
class PennyStockCandidate:
    ticker: str
    name: str
    exchange: str
    last_price: float
    avg_volume: float
    market_cap_est: float
    change_pct: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticker": self.ticker,
            "name": self.name,
            "exchange": self.exchange,
            "lastPrice": self.last_price,
            "avgVolume": self.avg_volume,
            "marketCapEst": self.market_cap_est,
            "changePct": self.change_pct,
        }


def _load_cache(repo_root: Path) -> list[PennyStockCandidate] | None:
    cache_path = repo_root / CACHE_PATH
    if not cache_path.exists():
        return None
    payload = json.loads(cache_path.read_text(encoding="utf-8"))
    generated_at = datetime.fromisoformat(payload.get("generatedAt"))
    if datetime.now(UTC) - generated_at > timedelta(hours=24):
        return None
    normalized: list[PennyStockCandidate] = []
    for row in payload.get("candidates", []):
        normalized.append(
            PennyStockCandidate(
                ticker=row.get("ticker"),
                name=row.get("name"),
                exchange=row.get("exchange"),
                last_price=float(row.get("last_price", row.get("lastPrice", 0.0))),
                avg_volume=float(row.get("avg_volume", row.get("avgVolume", 0.0))),
                market_cap_est=float(row.get("market_cap_est", row.get("marketCapEst", 0.0))),
                change_pct=float(row.get("change_pct", row.get("changePct", 0.0)) or 0.0),
            )
        )
    return normalized


def _load_otc_universe(repo_root: Path) -> list[PennyStockCandidate]:
    path = repo_root / OTC_UNIVERSE_PATH
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    candidates: list[PennyStockCandidate] = []
    for row in payload.get("candidates", []):
        ticker = str(row.get("ticker", "")).strip().upper()
        if not ticker:
            continue
        candidates.append(
            PennyStockCandidate(
                ticker=ticker,
                name=str(row.get("name") or ticker),
                exchange=str(row.get("exchange") or "OTC"),
                last_price=float(row.get("lastPrice", 0.0) or 0.0),
                avg_volume=float(row.get("avgVolume", 0.0) or 0.0),
                market_cap_est=float(row.get("marketCapEst", 0.0) or 0.0),
                change_pct=float(row.get("changePct", 0.0) or 0.0),
            )
        )
    return candidates


def load_penny_stock_universe(
    *,
    repo_root: Path | None = None,
    refresh: bool = False,
    min_price: float = 0.50,
    max_price: float = 5.00,
    min_volume: float = 50_000,
) -> list[PennyStockCandidate]:
    root = repo_root or Path(__file__).resolve().parent.parent
    if not refresh:
        cached = _load_cache(root)
        if cached is not None:
            return cached

    repository = TradingRepository(root)
    candidates: list[PennyStockCandidate] = []
    for asset in list_assets(repo_root=root):
        exchange = str(asset.get("exchange", "")).upper()
        if exchange not in ALLOWED_EXCHANGES:
            continue
        symbol = str(asset.get("symbol", "")).upper()
        if not symbol:
            continue
        try:
            bars = get_bars(symbol, limit=20, repo_root=root)
        except Exception:
            continue
        if bars.empty or "c" not in bars or "v" not in bars:
            continue
        last_price = float(bars["c"].iloc[-1])
        avg_volume = float(bars["v"].mean())
        if last_price < min_price or last_price > max_price or avg_volume <= min_volume:
            continue

        profile = repository.load_company_profiles([symbol]).get(symbol)
        market_cap_est = profile.market_cap_value if profile and profile.market_cap_value else last_price * avg_volume * 20
        candidates.append(
            PennyStockCandidate(
                ticker=symbol,
                name=str(asset.get("name", symbol)),
                exchange=exchange,
                last_price=round(last_price, 6),
                avg_volume=round(avg_volume, 6),
                market_cap_est=round(float(market_cap_est), 6),
            )
        )

    # Optional OTC Markets universe overlay: treated as an additive universe source for the sandbox.
    # This does not override Alpaca-backed candidates; it adds any missing tickers deterministically.
    otc_candidates = _load_otc_universe(root)
    if otc_candidates:
        by_ticker = {candidate.ticker: candidate for candidate in candidates}
        for candidate in otc_candidates:
            if candidate.last_price < min_price or candidate.last_price > max_price or candidate.avg_volume <= min_volume:
                continue
            by_ticker.setdefault(candidate.ticker, candidate)
        candidates = list(by_ticker.values())

    cache_payload = {
        "generatedAt": datetime.now(UTC).isoformat(),
        "candidates": [candidate.to_dict() for candidate in candidates],
    }
    cache_path = root / CACHE_PATH
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache_payload, indent=2), encoding="utf-8")
    return candidates


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Alpaca-backed penny-stock candidate universe.")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--min-price", type=float, default=0.50)
    parser.add_argument("--max-price", type=float, default=5.00)
    parser.add_argument("--min-volume", type=float, default=100_000)
    args = parser.parse_args()
    candidates = load_penny_stock_universe(
        refresh=args.refresh,
        min_price=args.min_price,
        max_price=args.max_price,
        min_volume=args.min_volume,
    )
    print(json.dumps([candidate.to_dict() for candidate in candidates], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
