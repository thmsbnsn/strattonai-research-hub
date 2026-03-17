"""Fill study-universe price gaps and optionally recompute downstream research artifacts."""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .fill_external_price_gap import run_fill
from .trading_repository import TradingRepository


LOGGER = logging.getLogger("research.fill_study_universe_gaps")


@dataclass(frozen=True, slots=True)
class StudyUniverseGapFillReport:
    min_rows: int
    tickers_attempted: tuple[str, ...]
    tickers_successfully_filled: tuple[str, ...]
    tickers_still_missing: tuple[str, ...]
    auto_recompute: bool
    total_rows_added: int
    completed_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Fill study-universe price gaps and optionally rerun downstream research jobs.")
    parser.add_argument("--min-rows", type=int, default=60)
    parser.add_argument("--price-file", default=None)
    parser.add_argument("--ticker", action="append", default=[], help="Optional comma-separated ticker override.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--auto-recompute", action="store_true")
    parser.add_argument(
        "--json-output",
        default=str(repo_root / "reports" / "study_universe_gap_fill.json"),
    )
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format="%(levelname)s %(message)s")


def _embedded_python() -> str:
    candidate = Path(
        r"C:\Users\tlben\.lmstudio\extensions\backends\vendor\_amphibian\cpython3.11-win-x86@6\python.exe"
    )
    return str(candidate) if candidate.exists() else "python"


def _run_module(module: str, args: list[str], repo_root: Path) -> None:
    command = [_embedded_python(), "-m", module, *args]
    LOGGER.info("Running %s", " ".join(command))
    subprocess.run(command, cwd=repo_root, check=True)


def run_gap_fill(
    repo_root: Path,
    *,
    min_rows: int,
    price_file: str | None,
    ticker_filters: list[str] | None = None,
    dry_run: bool,
    auto_recompute: bool,
) -> StudyUniverseGapFillReport:
    repository = TradingRepository(repo_root)
    requested_tickers = {
        part.strip().upper()
        for value in (ticker_filters or [])
        for part in str(value).split(",")
        if part.strip()
    }
    tickers = requested_tickers or set(repository.distinct_event_tickers())
    attempted = tuple(sorted(ticker for ticker in tickers if repository.count_daily_price_rows(ticker) < min_rows))
    if not attempted:
        report = StudyUniverseGapFillReport(
            min_rows=min_rows,
            tickers_attempted=(),
            tickers_successfully_filled=(),
            tickers_still_missing=(),
            auto_recompute=auto_recompute,
            total_rows_added=0,
            completed_at=datetime.now(UTC).isoformat(),
        )
        return report

    fill_report = run_fill(
        repo_root,
        price_file=price_file,
        ticker_overrides=list(attempted),
        load_supabase=not dry_run,
        bootstrap_daily_prices_schema=not dry_run,
        dry_run=dry_run,
    )

    after_missing = tuple(
        sorted(ticker for ticker in attempted if repository.count_daily_price_rows(ticker) < min_rows)
    ) if not dry_run else tuple(sorted(fill_report.tickers_unresolved))
    successful = tuple(sorted(ticker for ticker in attempted if ticker not in after_missing))

    if auto_recompute and not dry_run and successful:
        ticker_value = ",".join(successful)
        ticker_args = ["--ticker-filter", ticker_value]
        _run_module("research.recompute_all_event_studies", (["--price-file", price_file] if price_file else []) + ticker_args, repo_root)
        _run_module("research.rescore_all_recent_events", ["--regime-aware", "--ticker-filter", ticker_value], repo_root)
        _run_module("research.generate_gap_report", ["--price-file", price_file] if price_file else [], repo_root)

    return StudyUniverseGapFillReport(
        min_rows=min_rows,
        tickers_attempted=attempted,
        tickers_successfully_filled=successful,
        tickers_still_missing=after_missing,
        auto_recompute=auto_recompute,
        total_rows_added=fill_report.total_rows_added,
        completed_at=datetime.now(UTC).isoformat(),
    )


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)
    repo_root = Path(__file__).resolve().parent.parent
    report = run_gap_fill(
        repo_root,
        min_rows=args.min_rows,
        price_file=args.price_file,
        ticker_filters=args.ticker,
        dry_run=args.dry_run,
        auto_recompute=args.auto_recompute,
    )
    output_path = Path(args.json_output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    LOGGER.info(
        "Study-universe gap fill complete. attempted=%s filled=%s unresolved=%s rows_added=%s",
        list(report.tickers_attempted),
        list(report.tickers_successfully_filled),
        list(report.tickers_still_missing),
        report.total_rows_added,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
