"""Apply and verify additive Supabase migrations for trader-side tables."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ingestion.write_to_supabase import SupabaseWriter, load_ingestion_environment


REQUIRED_ARTIFACTS: dict[str, dict[str, set[str]]] = {
    "portfolio_allocations": {
        "table": {"portfolio_allocations"},
        "columns": {
            "id",
            "run_id",
            "method",
            "ticker",
            "allocation_dollars",
            "weight",
            "signal_key",
            "capital_total",
            "created_at",
        },
    },
    "market_regimes": {
        "table": {"market_regimes"},
        "columns": {
            "id",
            "as_of_date",
            "regime_label",
            "spy_price",
            "sma_200",
            "sma_50",
            "vol_20d",
            "drawdown_from_high",
            "created_at",
        },
    },
    "paper_trades_extended": {
        "table": {"paper_trades"},
        "columns": {
            "mode",
            "metadata",
            "alpaca_order_id",
            "exit_price",
            "exit_date",
            "realized_pnl",
            "universe",
        },
    },
    "signal_scores_metadata": {
        "table": {"signal_scores"},
        "columns": {"metadata"},
    },
}

MIGRATIONS: tuple[tuple[str, str], ...] = (
    ("009", "supabase/sql/009_add_portfolio_allocations.sql"),
    ("010", "supabase/sql/010_add_paper_trade_metadata.sql"),
    ("011", "supabase/sql/011_add_market_regimes.sql"),
    ("012", "supabase/sql/012_add_trading_loop_fields.sql"),
    ("013", "supabase/sql/013_add_signal_score_metadata.sql"),
)


@dataclass(frozen=True, slots=True)
class MigrationStatus:
    migration_id: str
    path: str
    status: str
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "migrationId": self.migration_id,
            "path": self.path,
            "status": self.status,
            "detail": self.detail,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply and verify additive Supabase migrations.")
    parser.add_argument("--dry-run", action="store_true", help="Validate migrations inside rolled-back transactions.")
    return parser.parse_args()


def _existing_tables(writer: SupabaseWriter) -> set[str]:
    with writer.connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                select table_name
                from information_schema.tables
                where table_schema = 'public'
                """
            )
            return {str(row[0]) for row in cursor.fetchall()}


def _existing_columns(writer: SupabaseWriter, table_name: str) -> set[str]:
    with writer.connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                select column_name
                from information_schema.columns
                where table_schema = 'public'
                  and table_name = %s
                """,
                (table_name,),
            )
            return {str(row[0]) for row in cursor.fetchall()}


def verify_expected_artifacts(repo_root: Path) -> tuple[dict[str, bool], list[str]]:
    writer = SupabaseWriter(repo_root)
    table_cache = _existing_tables(writer)
    verification: dict[str, bool] = {}
    problems: list[str] = []

    for artifact_name, requirement in REQUIRED_ARTIFACTS.items():
        required_table = next(iter(requirement["table"]))
        table_exists = required_table in table_cache
        if not table_exists:
            verification[artifact_name] = False
            problems.append(f"{artifact_name}: missing table {required_table}")
            continue

        existing_columns = _existing_columns(writer, required_table)
        missing_columns = sorted(requirement["columns"] - existing_columns)
        verification[artifact_name] = not missing_columns
        if missing_columns:
            problems.append(f"{artifact_name}: missing columns {', '.join(missing_columns)}")

    return verification, problems


def apply_migration_file(writer: SupabaseWriter, migration_id: str, sql_path: Path, *, dry_run: bool, connection=None) -> MigrationStatus:
    pre_verification, _ = verify_expected_artifacts(writer.repo_root)
    if migration_id == "009" and pre_verification.get("portfolio_allocations"):
        return MigrationStatus(migration_id, str(sql_path), "ALREADY EXISTS — SKIPPED", "portfolio_allocations verified")
    if migration_id == "010" and pre_verification.get("paper_trades_extended"):
        return MigrationStatus(migration_id, str(sql_path), "ALREADY EXISTS — SKIPPED", "paper_trades extensions verified")
    if migration_id == "011" and pre_verification.get("market_regimes"):
        return MigrationStatus(migration_id, str(sql_path), "ALREADY EXISTS — SKIPPED", "market_regimes verified")
    if migration_id == "012" and pre_verification.get("paper_trades_extended"):
        return MigrationStatus(migration_id, str(sql_path), "ALREADY EXISTS — SKIPPED", "paper_trades broker fields verified")
    if migration_id == "013" and pre_verification.get("signal_scores_metadata"):
        return MigrationStatus(migration_id, str(sql_path), "ALREADY EXISTS — SKIPPED", "signal_scores metadata verified")

    try:
        if connection is None:
            with writer.connect() as live_connection:
                with live_connection.cursor() as cursor:
                    cursor.execute(sql_path.read_text(encoding="utf-8"))
                if dry_run:
                    live_connection.rollback()
                    detail = "validated in dry-run transaction"
                else:
                    live_connection.commit()
                    detail = "applied successfully"
            return MigrationStatus(migration_id, str(sql_path), "APPLIED", detail)
        with connection.cursor() as cursor:
            cursor.execute(sql_path.read_text(encoding="utf-8"))
        detail = "validated in dry-run transaction" if dry_run else "applied successfully"
        return MigrationStatus(migration_id, str(sql_path), "APPLIED", detail)
    except Exception as error:
        return MigrationStatus(migration_id, str(sql_path), "FAILED", str(error))


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    load_ingestion_environment(repo_root)
    writer = SupabaseWriter(repo_root)

    statuses: list[MigrationStatus] = []
    if args.dry_run:
        with writer.connect() as connection:
            for migration_id, relative_path in MIGRATIONS:
                sql_path = (repo_root / relative_path).resolve()
                status = apply_migration_file(writer, migration_id, sql_path, dry_run=True, connection=connection)
                statuses.append(status)
                print(f"[{status.status}] {migration_id} {sql_path.name} — {status.detail}")
                if status.status == "FAILED":
                    connection.rollback()
                    print(f"[VERIFICATION FAILED: migration {migration_id} did not apply]")
                    return 1
            connection.rollback()
        print("[VERIFIED] Dry-run validation passed for migrations 009-013.")
        return 0

    for migration_id, relative_path in MIGRATIONS:
        sql_path = (repo_root / relative_path).resolve()
        status = apply_migration_file(writer, migration_id, sql_path, dry_run=False)
        statuses.append(status)
        print(f"[{status.status}] {migration_id} {sql_path.name} — {status.detail}")
        if status.status == "FAILED":
            print(f"[VERIFICATION FAILED: migration {migration_id} did not apply]")
            return 1

    verification, problems = verify_expected_artifacts(repo_root)
    if all(verification.values()):
        print("[VERIFIED] portfolio/trading migrations are present and all expected columns exist.")
        return 0

    detail = "; ".join(problems) if problems else "Unknown verification failure."
    print(f"[VERIFICATION FAILED: {detail}]")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
