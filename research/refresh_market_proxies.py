"""
Refreshes key market proxy tickers (e.g., SPY/QQQ/DIA) into the preferred local price dataset and optionally into Supabase.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Iterable

from .fill_external_price_gap import ExternalPriceGapFillReport, run_fill

LOGGER = logging.getLogger("research.refresh_market_proxies")
DEFAULT_PROXIES = ("SPY", "QQQ", "DIA")


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format="%(levelname)s %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refresh key market proxy tickers into the enriched local price dataset and Supabase daily_prices."
    )
    parser.add_argument("--price-file", default=None, help="Optional explicit base price dataset override.")
    parser.add_argument(
        "--ticker",
        action="append",
        default=[],
        help="Override ticker list (comma-separated or repeated). Defaults to SPY,QQQ,DIA.",
    )
    parser.add_argument(
        "--json-output",
        default=None,
        help="Optional JSON output path. Defaults to reports/market_proxy_refresh.json relative to repo root.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Run without writing local price files or Supabase.")
    parser.add_argument(
        "--bootstrap-schema",
        action="store_true",
        help="Apply the daily_prices schema before loading Supabase when not in dry-run.",
    )
    parser.add_argument(
        "--no-supabase-load",
        action="store_true",
        help="Do not load refreshed prices into Supabase even when not in dry-run.",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")
    return parser.parse_args()


def _normalize_tickers(values: Iterable[str]) -> list[str]:
    tickers = set[str]()
    for value in values:
        for part in str(value or "").split(","):
            cleaned = part.strip().upper()
            if cleaned:
                tickers.add(cleaned)
    return sorted(tickers) or list(DEFAULT_PROXIES)


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)

    repo_root = Path(__file__).resolve().parent.parent
    tickers = _normalize_tickers(args.ticker)
    json_output = (
        Path(args.json_output).resolve()
        if args.json_output
        else repo_root / "reports" / "market_proxy_refresh.json"
    )

    report: ExternalPriceGapFillReport = run_fill(
        repo_root,
        price_file=args.price_file,
        ticker_overrides=tickers,
        load_supabase=not args.no_supabase_load and not args.dry_run,
        bootstrap_daily_prices_schema=args.bootstrap_schema,
        dry_run=args.dry_run,
    )

    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    LOGGER.info(
        "Market proxy refresh complete. tickers=%s filled=%s unresolved=%s rows_added=%s supabase_rows=%s",
        list(report.target_tickers),
        list(report.tickers_filled),
        list(report.tickers_unresolved),
        report.total_rows_added,
        report.supabase_rows_upserted,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
