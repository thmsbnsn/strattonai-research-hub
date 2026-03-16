from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import perf_counter
from typing import Any

from .event_study_engine import aggregate_observations, build_price_map, compute_event_study_observations
from .price_dataset import collect_study_tickers, load_resolved_price_series
from .write_event_studies_to_supabase import EventStudySupabaseWriter


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Benchmark CSV vs Parquet price loading for event-study recomputation.")
    parser.add_argument(
        "--csv-file",
        default="data/prices/all_stock_data.csv",
        help="Explicit CSV dataset path.",
    )
    parser.add_argument(
        "--parquet-file",
        default="data/prices/all_stock_data.parquet",
        help="Explicit Parquet dataset path.",
    )
    parser.add_argument(
        "--json-output",
        default=str(repo_root / "reports" / "price_workflow_benchmark.json"),
        help="Path for the JSON benchmark report.",
    )
    parser.add_argument(
        "--markdown-output",
        default=str(repo_root / "reports" / "price_workflow_benchmark.md"),
        help="Path for the Markdown benchmark report.",
    )
    return parser.parse_args()


def _run_case(repo_root: Path, price_file: str | Path | None) -> dict[str, Any]:
    writer = EventStudySupabaseWriter(repo_root)
    events = writer.load_study_events()
    tickers = collect_study_tickers(events)

    started_at = perf_counter()
    price_series, resolved = load_resolved_price_series(repo_root, price_file, tickers=tickers)
    price_map = build_price_map(price_series)
    observations, stats = compute_event_study_observations(events, price_map)
    aggregates = aggregate_observations(observations)
    elapsed_seconds = perf_counter() - started_at

    return {
        "price_path": str(resolved.path),
        "price_format": resolved.format,
        "resolution_reason": resolved.resolution_reason,
        "event_count": len(events),
        "ticker_count": len(tickers),
        "loaded_ticker_count": len(price_series),
        "observation_count": len(observations),
        "aggregate_count": len(aggregates),
        "missing_primary_series": stats["missing_primary_series"],
        "missing_related_series": stats["missing_related_series"],
        "missing_horizon": stats["missing_horizon"],
        "elapsed_seconds": round(elapsed_seconds, 3),
    }


def build_report(repo_root: Path, csv_file: str | Path, parquet_file: str | Path) -> dict[str, Any]:
    csv_case = _run_case(repo_root, csv_file)
    parquet_case = _run_case(repo_root, parquet_file)
    auto_case = _run_case(repo_root, None)
    return {
        "csv_case": csv_case,
        "parquet_case": parquet_case,
        "auto_case": auto_case,
        "comparison": {
            "parquet_speedup_vs_csv_seconds": round(csv_case["elapsed_seconds"] - parquet_case["elapsed_seconds"], 3),
            "parquet_speedup_vs_csv_percent": round(
                ((csv_case["elapsed_seconds"] - parquet_case["elapsed_seconds"]) / csv_case["elapsed_seconds"]) * 100,
                2,
            )
            if csv_case["elapsed_seconds"] > 0
            else None,
            "auto_matches_parquet_path": auto_case["price_path"] == parquet_case["price_path"],
            "csv_vs_parquet_observations_equal": csv_case["observation_count"] == parquet_case["observation_count"],
            "csv_vs_parquet_aggregates_equal": csv_case["aggregate_count"] == parquet_case["aggregate_count"],
        },
    }


def build_markdown_report(report: dict[str, Any]) -> str:
    csv_case = report["csv_case"]
    parquet_case = report["parquet_case"]
    auto_case = report["auto_case"]
    comparison = report["comparison"]
    lines = [
        "# Price Workflow Benchmark",
        "",
        f"- CSV: {csv_case['elapsed_seconds']}s using {csv_case['price_path']}",
        f"- Parquet: {parquet_case['elapsed_seconds']}s using {parquet_case['price_path']}",
        f"- Auto: {auto_case['elapsed_seconds']}s using {auto_case['price_path']}",
        "",
        "## Comparison",
        f"- parquet_speedup_vs_csv_seconds: {comparison['parquet_speedup_vs_csv_seconds']}",
        f"- parquet_speedup_vs_csv_percent: {comparison['parquet_speedup_vs_csv_percent']}",
        f"- auto_matches_parquet_path: {comparison['auto_matches_parquet_path']}",
        f"- csv_vs_parquet_observations_equal: {comparison['csv_vs_parquet_observations_equal']}",
        f"- csv_vs_parquet_aggregates_equal: {comparison['csv_vs_parquet_aggregates_equal']}",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    report = build_report(repo_root, args.csv_file, args.parquet_file)

    json_output = Path(args.json_output)
    markdown_output = Path(args.markdown_output)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    markdown_output.write_text(build_markdown_report(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
