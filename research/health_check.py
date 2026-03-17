"""Operator health check for the StrattonAI local stack."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from ingestion.load_price_series_file import inspect_price_series_file
from ingestion.write_to_supabase import SupabaseWriter

from .alpaca_client import get_account
from .price_dataset import resolve_price_dataset_path
from .trading_repository import TradingRepository


@dataclass(frozen=True, slots=True)
class HealthCheckResult:
    name: str
    status: str
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "status": self.status, "detail": self.detail}


def _request_json(url: str) -> tuple[int | None, Any]:
    try:
        with urlopen(Request(url, headers={"User-Agent": "StrattonAI/1.0"}), timeout=20) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return response.status, json.loads(raw) if raw else {}
    except URLError as error:
        return None, str(error)


def _business_days_since(last_date: date, current_date: date) -> int:
    days = 0
    cursor = last_date + timedelta(days=1)
    while cursor <= current_date:
        if cursor.weekday() < 5:
            days += 1
        cursor += timedelta(days=1)
    return days


def run_health_check(repo_root: Path) -> tuple[list[HealthCheckResult], str]:
    checks: list[HealthCheckResult] = []
    writer = SupabaseWriter(repo_root)
    repository = TradingRepository(repo_root)

    try:
        with writer.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("select count(*) from public.events")
                event_count = int(cursor.fetchone()[0] or 0)
        checks.append(HealthCheckResult("supabase_connection", "OK", f"events={event_count}"))
    except Exception as error:
        checks.append(HealthCheckResult("supabase_connection", "FAIL", str(error)))
        return checks, "System Not Ready — fix failures before running"

    required_tables = {
        "events",
        "related_companies",
        "signal_scores",
        "daily_prices",
        "paper_trades",
        "market_regimes",
        "portfolio_allocations",
        "company_relationship_graph",
    }
    try:
        with writer.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select table_name
                    from information_schema.tables
                    where table_schema = 'public'
                    """
                )
                tables = {row[0] for row in cursor.fetchall()}
        missing_tables = sorted(required_tables - tables)
        checks.append(
            HealthCheckResult(
                "table_presence",
                "OK" if not missing_tables else "FAIL",
                "all expected tables present" if not missing_tables else f"missing: {', '.join(missing_tables)}",
            )
        )
    except Exception as error:
        checks.append(HealthCheckResult("table_presence", "FAIL", str(error)))

    try:
        with writer.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("select max(created_at) from public.signal_scores")
                latest_signal = cursor.fetchone()[0]
        if latest_signal is None:
            checks.append(HealthCheckResult("signal_recency", "WARN", "signal_scores is empty"))
        else:
            age_days = (datetime.now(UTC) - latest_signal).days
            checks.append(
                HealthCheckResult(
                    "signal_recency",
                    "OK" if age_days <= 7 else "WARN",
                    f"latest signal created_at={latest_signal.isoformat()} age_days={age_days}",
                )
            )
    except Exception as error:
        checks.append(HealthCheckResult("signal_recency", "WARN", str(error)))

    try:
        latest_price = repository.latest_daily_price("SPY")
        if latest_price is None:
            checks.append(HealthCheckResult("price_recency", "WARN", "daily_prices has no SPY rows"))
        else:
            stale = _business_days_since(latest_price.trade_date, datetime.now(UTC).date())
            checks.append(
                HealthCheckResult(
                    "price_recency",
                    "OK" if stale <= 5 else "WARN",
                    f"latest SPY daily_prices row={latest_price.trade_date.isoformat()} stale_business_days={stale}",
                )
            )
    except Exception as error:
        checks.append(HealthCheckResult("price_recency", "WARN", str(error)))

    gateway_status, gateway_payload = _request_json("http://127.0.0.1:8787/health")
    checks.append(
        HealthCheckResult(
            "gateway_reachable",
            "OK" if gateway_status == 200 else "WARN",
            f"status={gateway_status} payload={gateway_payload}",
        )
    )

    ollama_status, _ = _request_json("http://127.0.0.1:11434/api/tags")
    checks.append(
        HealthCheckResult(
            "ollama_reachable",
            "OK" if ollama_status == 200 else "WARN",
            f"status={ollama_status or 'unreachable'}",
        )
    )

    migration_status, migration_payload = _request_json("http://127.0.0.1:8787/health/migrations")
    migration_ok = bool(migration_status == 200 and isinstance(migration_payload, dict) and migration_payload.get("success"))
    if migration_ok:
        migration_ok = bool(migration_payload.get("data", {}).get("all_verified"))
    checks.append(
        HealthCheckResult(
            "migration_status",
            "OK" if migration_ok else "WARN",
            f"status={migration_status} payload={migration_payload}",
        )
    )

    try:
        resolved = resolve_price_dataset_path(repo_root, None, allow_sample_fallback=False)
        inspection = inspect_price_series_file(resolved.path)
        checks.append(
            HealthCheckResult(
                "local_price_file",
                "OK" if inspection.row_count > 100_000 else "WARN",
                f"path={resolved.path} rows={inspection.row_count}",
            )
        )
    except Exception as error:
        checks.append(HealthCheckResult("local_price_file", "FAIL", str(error)))

    try:
        account = get_account(repo_root=repo_root)
        checks.append(HealthCheckResult("alpaca_sandbox", "OK", f"account_status={account.get('status') or account.get('account_status') or 'unknown'}"))
    except Exception as error:
        checks.append(HealthCheckResult("alpaca_sandbox", "WARN", str(error)))

    overall = "System Ready"
    if any(check.status == "FAIL" for check in checks):
        overall = "System Not Ready — fix failures before running"
    elif any(check.status == "WARN" for check in checks):
        overall = "System Ready with warnings"

    return checks, overall


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the full StrattonAI operator health check.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    checks, overall = run_health_check(repo_root)
    if args.json:
        print(json.dumps({"overall": overall, "checks": [check.to_dict() for check in checks]}, indent=2))
    else:
        for check in checks:
            print(f"[{check.status}] {check.name}: {check.detail}")
        print(overall)
    return 0 if "Not Ready" not in overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
