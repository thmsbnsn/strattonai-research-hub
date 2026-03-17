from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research.health_check import run_health_check


class _FakeWriter:
    def __init__(self, _root: Path):
        pass

    def connect(self):
        class _Cursor:
            def __init__(self):
                self.last_sql = ""

            def execute(self, sql, params=None):
                self.last_sql = sql

            def fetchone(self):
                if "count(*) from public.events" in self.last_sql:
                    return [10]
                if "max(created_at) from public.signal_scores" in self.last_sql:
                    import datetime
                    return [datetime.datetime.now(datetime.UTC)]
                return [0]

            def fetchall(self):
                return [(name,) for name in [
                    "events",
                    "related_companies",
                    "signal_scores",
                    "daily_prices",
                    "paper_trades",
                    "market_regimes",
                    "portfolio_allocations",
                    "company_relationship_graph",
                ]]

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        class _Connection:
            def cursor(self):
                return _Cursor()

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        return _Connection()


class _FakeRepo:
    def __init__(self, _root: Path):
        pass

    def latest_daily_price(self, ticker: str):
        from decimal import Decimal
        import datetime
        return type("Price", (), {"trade_date": datetime.date.today(), "close": Decimal("100")})()

    def count_daily_price_rows(self, ticker: str):
        return 1000


class HealthCheckTests(unittest.TestCase):
    def test_health_check_returns_ready_with_mocked_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, patch("research.health_check.SupabaseWriter", _FakeWriter), patch(
            "research.health_check.TradingRepository",
            _FakeRepo,
        ), patch(
            "research.health_check._request_json",
            side_effect=[(200, {"success": True}), (200, {}), (200, {"success": True, "data": {"all_verified": True}})],
        ), patch(
            "research.health_check.resolve_price_dataset_path",
            return_value=type("Resolved", (), {"path": Path(temp_dir) / "prices.parquet"})(),
        ), patch(
            "research.health_check.inspect_price_series_file",
            return_value=type("Inspect", (), {"row_count": 200000})(),
        ), patch(
            "research.health_check.get_account",
            return_value={"status": "ACTIVE"},
        ):
            checks, overall = run_health_check(Path(temp_dir))
        self.assertTrue(any(check.name == "supabase_connection" and check.status == "OK" for check in checks))
        self.assertIn("Ready", overall)


if __name__ == "__main__":
    unittest.main()
