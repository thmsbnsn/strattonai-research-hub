
from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

try:
    import psycopg
    from psycopg.extras import execute_values
except ImportError:  # pragma: no cover - fallback to psycopg2
    import psycopg2 as psycopg  # type: ignore
    from psycopg2.extras import execute_values  # type: ignore

import requests

try:
    from ingestion.write_to_supabase import build_postgres_dsn, load_ingestion_environment
except ImportError:  # pragma: no cover - script execution fallback
    from write_to_supabase import build_postgres_dsn, load_ingestion_environment  # type: ignore

LOGGER = logging.getLogger("research.fmp_company_profiles")


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    try:
        return str(value)
    except Exception:  # pragma: no cover - defensive
        return None


def _safe_num(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def _map_fmp_profile(ticker: str, payload: dict[str, Any]) -> dict[str, Any]:
    ticker_upper = ticker.upper().strip()
    return {
        "ticker": ticker_upper,
        "name": payload.get("companyName") or payload.get("symbol") or ticker_upper,
        "sector": payload.get("sector"),
        "industry": payload.get("industry"),
        "market_cap": _safe_str(payload.get("mktCap") or payload.get("marketCap")),
        "pe": _safe_num(payload.get("pe")),
        "revenue": _safe_str(payload.get("revenueTTM") or payload.get("revenue")),
        "employees": _safe_str(payload.get("fullTimeEmployees") or payload.get("employees")),
    }


def fetch_profiles(tickers: Sequence[str], api_key: str, verbose: bool = False) -> tuple[list[dict[str, Any]], list[str]]:
    headers = {"User-Agent": "StrattonAI/price-fundamentals"}
    rows: list[dict[str, Any]] = []
    missing: list[str] = []

    for ticker in tickers:
        url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}"
        try:
            resp = requests.get(url, params={"apikey": api_key}, headers=headers, timeout=20)
        except requests.RequestException as exc:  # pragma: no cover - network
            LOGGER.warning("FMP request failed for %s: %s", ticker, exc)
            missing.append(ticker)
            continue

        if resp.status_code != 200:
            LOGGER.warning("FMP returned %s for %s", resp.status_code, ticker)
            missing.append(ticker)
            continue

        try:
            data = resp.json()
        except ValueError:
            LOGGER.warning("FMP returned non-JSON for %s", ticker)
            missing.append(ticker)
            continue

        if not isinstance(data, list) or not data:
            if verbose:
                LOGGER.info("FMP returned empty payload for %s", ticker)
            missing.append(ticker)
            continue

        mapped = _map_fmp_profile(ticker, data[0])
        rows.append(mapped)
        if verbose:
            LOGGER.info("Fetched profile for %s", ticker)

    return rows, missing


def _connect(dsn: str) -> psycopg.Connection:
    connection = psycopg.connect(dsn)
    # psycopg2 compatibility: set autocommit flag explicitly
    if hasattr(connection, "autocommit"):
        connection.autocommit = False  # type: ignore[attr-defined]
    return connection


def derive_tickers_from_supabase(dsn: str, limit: int | None = None) -> list[str]:
    query = """
        with universe as (
            select ticker from public.events
            union select target_ticker as ticker from public.related_companies
            union select primary_ticker as ticker from public.signal_scores
        )
        select upper(ticker) as ticker
        from universe
        where ticker is not null and ticker <> ''
        group by ticker
        order by ticker asc
    """
    tickers: list[str] = []
    with _connect(dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            for row in rows:
                tickers.append(row[0])
    if limit:
        return tickers[:limit]
    return tickers


def upsert_profiles(dsn: str, profiles: list[dict[str, Any]]) -> int:
    if not profiles:
        return 0

    columns = ["ticker", "name", "sector", "industry", "market_cap", "pe", "revenue", "employees"]
    values = [
        (
            p["ticker"],
            p["name"],
            p.get("sector"),
            p.get("industry"),
            p.get("market_cap"),
            p.get("pe"),
            p.get("revenue"),
            p.get("employees"),
        )
        for p in profiles
    ]

    with _connect(dsn) as connection:
        with connection.cursor() as cursor:
            execute_values(
                cursor,
                """
                insert into public.company_profiles (ticker, name, sector, industry, market_cap, pe, revenue, employees)
                values %s
                on conflict (ticker) do update set
                  name = excluded.name,
                  sector = excluded.sector,
                  industry = excluded.industry,
                  market_cap = excluded.market_cap,
                  pe = excluded.pe,
                  revenue = excluded.revenue,
                  employees = excluded.employees,
                  updated_at = timezone('utc', now())
                """,
                values,
            )
        connection.commit()

    return len(profiles)


def write_report(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Enrich company_profiles with FMP fundamentals.")
    parser.add_argument("--tickers", action="append", help="Ticker(s) to fetch; repeatable")
    parser.add_argument("--limit", type=int, help="Limit number of tickers to process")
    parser.add_argument("--report-file", default="reports/fmp_company_profiles.json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)

    repo_root = Path(__file__).resolve().parents[1]
    load_ingestion_environment(repo_root)

    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        LOGGER.error("FMP_API_KEY is required.")
        return 1

    dsn = build_postgres_dsn()

    tickers: list[str]
    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers if t.strip()]
    else:
        tickers = derive_tickers_from_supabase(dsn, args.limit)

    if args.limit:
        tickers = tickers[: args.limit]

    if not tickers:
        LOGGER.error("No tickers to process.")
        return 1

    profiles, missing = fetch_profiles(tickers, api_key, verbose=args.verbose)

    rows_upserted = 0
    if not args.dry_run and profiles:
        rows_upserted = upsert_profiles(dsn, profiles)

    report = {
        "run_at": datetime.utcnow().isoformat() + "Z",
        "tickers_requested": tickers,
        "tickers_found": [p["ticker"] for p in profiles],
        "tickers_missing": missing,
        "rows_upserted": rows_upserted,
        "dry_run": args.dry_run,
    }
    write_report(Path(args.report_file), report)

    if args.verbose:
        LOGGER.info("Upserted %s rows", rows_upserted)
        if missing:
            LOGGER.info("Missing tickers: %s", ", ".join(missing))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
