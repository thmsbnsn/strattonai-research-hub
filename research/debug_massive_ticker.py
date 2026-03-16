from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
from textwrap import shorten
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from .massive_config import load_massive_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Debug a single Massive ticker day-aggregate lookup.")
    parser.add_argument("--ticker", required=True, help="Ticker symbol to debug.")
    parser.add_argument("--date", default="2024-01-02", help="Single trade date to request (YYYY-MM-DD).")
    return parser.parse_args()


def _build_url(base_url: str, ticker: str, trade_date: str, api_key: str) -> str:
    params = urlencode(
        {
            "adjusted": "true",
            "sort": "asc",
            "limit": "50000",
            "apiKey": api_key,
        }
    )
    return f"{base_url}/v2/aggs/ticker/{quote(ticker, safe='')}/range/1/day/{trade_date}/{trade_date}?{params}"


def _print_response(status: int, headers: list[tuple[str, str]], body: str) -> None:
    print(f"status: {status}")
    print("headers:")
    for key, value in headers:
        print(f"  {key}: {value}")
    print("body:")
    print(shorten(body, width=2000, placeholder="..."))


def main() -> int:
    args = parse_args()
    trade_date = date.fromisoformat(args.date).isoformat()
    repo_root = Path(__file__).resolve().parent.parent
    config = load_massive_config(repo_root)
    url = _build_url(config.base_url, args.ticker, trade_date, config.api_key)
    request = Request(url, headers={"User-Agent": "StrattonAI/1.0"})

    try:
        with urlopen(request, timeout=60) as response:
            body = response.read().decode("utf-8", errors="replace")
            _print_response(response.status, list(response.headers.items()), body)
            return 0
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        _print_response(exc.code, list(exc.headers.items()) if exc.headers else [], body)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
