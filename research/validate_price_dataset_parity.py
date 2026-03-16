from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ingestion.load_price_series_file import inspect_price_series_file, load_price_series_file

from .price_dataset import collect_study_tickers, resolve_price_dataset_path
from .write_event_studies_to_supabase import EventStudySupabaseWriter


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Validate CSV vs Parquet price-dataset parity for StrattonAI research workflows.")
    parser.add_argument(
        "--parquet-file",
        default="data/prices/all_stock_data.parquet",
        help="Explicit Parquet dataset path. Relative paths are resolved against the repo and parent workspace.",
    )
    parser.add_argument(
        "--csv-file",
        default="data/prices/all_stock_data.csv",
        help="Explicit CSV dataset path. Relative paths are resolved against the repo and parent workspace.",
    )
    parser.add_argument(
        "--json-output",
        default=str(repo_root / "reports" / "price_dataset_parity.json"),
        help="Path for the JSON parity report.",
    )
    parser.add_argument(
        "--markdown-output",
        default=str(repo_root / "reports" / "price_dataset_parity.md"),
        help="Path for the Markdown parity report.",
    )
    return parser.parse_args()


def _collect_referenced_tickers(repo_root: Path) -> tuple[set[str], str | None]:
    try:
        writer = EventStudySupabaseWriter(repo_root)
        events = writer.load_study_events()
    except Exception as exc:  # pragma: no cover - depends on local Supabase availability
        return set(), str(exc)
    return collect_study_tickers(events), None


def _summarize_series(series_list: list[Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for series in series_list:
        prices = tuple(series.prices)
        summary[series.ticker] = {
            "day_count": len(prices),
            "min_date": prices[0].date.isoformat() if prices else None,
            "max_date": prices[-1].date.isoformat() if prices else None,
            "points": tuple((point.date.isoformat(), float(point.close)) for point in prices),
        }
    return summary


def _build_referenced_ticker_parity(
    parquet_path: Path,
    csv_path: Path,
    tickers: set[str],
) -> dict[str, Any]:
    parquet_series = load_price_series_file(parquet_path, tickers=tickers)
    csv_series = load_price_series_file(csv_path, tickers=tickers)
    parquet_summary = _summarize_series(parquet_series)
    csv_summary = _summarize_series(csv_series)

    mismatches: list[dict[str, Any]] = []
    for ticker in sorted(set(parquet_summary) | set(csv_summary)):
        parquet_item = parquet_summary.get(ticker)
        csv_item = csv_summary.get(ticker)
        if parquet_item != csv_item:
            mismatches.append(
                {
                    "ticker": ticker,
                    "parquet_day_count": parquet_item["day_count"] if parquet_item else None,
                    "csv_day_count": csv_item["day_count"] if csv_item else None,
                    "parquet_min_date": parquet_item["min_date"] if parquet_item else None,
                    "csv_min_date": csv_item["min_date"] if csv_item else None,
                    "parquet_max_date": parquet_item["max_date"] if parquet_item else None,
                    "csv_max_date": csv_item["max_date"] if csv_item else None,
                    "points_equal": bool(parquet_item and csv_item and parquet_item["points"] == csv_item["points"]),
                }
            )

    return {
        "referenced_ticker_count": len(tickers),
        "parquet_loaded_ticker_count": len(parquet_summary),
        "csv_loaded_ticker_count": len(csv_summary),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches[:25],
    }


def build_parity_report(repo_root: Path, parquet_file: str | Path, csv_file: str | Path) -> dict[str, Any]:
    parquet_resolved = resolve_price_dataset_path(repo_root, parquet_file, allow_sample_fallback=False)
    csv_resolved = resolve_price_dataset_path(repo_root, csv_file, allow_sample_fallback=False)

    parquet_inspection = inspect_price_series_file(parquet_resolved.path)
    csv_inspection = inspect_price_series_file(csv_resolved.path)
    referenced_tickers, ticker_error = _collect_referenced_tickers(repo_root)

    report: dict[str, Any] = {
        "parquet": parquet_inspection.to_dict(),
        "csv": csv_inspection.to_dict(),
        "parity": {
            "row_count_equal": parquet_inspection.row_count == csv_inspection.row_count,
            "distinct_ticker_count_equal": parquet_inspection.distinct_ticker_count == csv_inspection.distinct_ticker_count,
            "min_date_equal": parquet_inspection.min_date == csv_inspection.min_date,
            "max_date_equal": parquet_inspection.max_date == csv_inspection.max_date,
            "required_columns_equal": parquet_inspection.required_columns == csv_inspection.required_columns,
            "missing_columns_equal": parquet_inspection.missing_columns == csv_inspection.missing_columns,
            "rejected_rows_equal": parquet_inspection.rejected_rows == csv_inspection.rejected_rows,
            "rejection_reasons_equal": parquet_inspection.rejection_reasons == csv_inspection.rejection_reasons,
        },
        "notes": {
            "parquet_path": str(parquet_resolved.path),
            "csv_path": str(csv_resolved.path),
        },
    }

    if ticker_error is not None:
        report["referenced_ticker_parity"] = {
            "error": ticker_error,
            "referenced_ticker_count": 0,
        }
    else:
        report["referenced_ticker_parity"] = _build_referenced_ticker_parity(
            parquet_resolved.path,
            csv_resolved.path,
            referenced_tickers,
        )
    return report


def build_markdown_report(report: dict[str, Any]) -> str:
    parquet = report["parquet"]
    csv_report = report["csv"]
    parity = report["parity"]
    referenced = report.get("referenced_ticker_parity", {})

    lines = [
        "# Price Dataset Parity",
        "",
        "## Full Dataset",
        f"- Parquet rows={parquet['row_count']}, tickers={parquet['distinct_ticker_count']}, "
        f"coverage={parquet['min_date']} -> {parquet['max_date']}, rejected={parquet['rejected_rows']}",
        f"- CSV rows={csv_report['row_count']}, tickers={csv_report['distinct_ticker_count']}, "
        f"coverage={csv_report['min_date']} -> {csv_report['max_date']}, rejected={csv_report['rejected_rows']}",
        "",
        "## Parity Checks",
    ]
    for key, value in sorted(parity.items()):
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## Referenced Ticker Parity"])
    if "error" in referenced:
        lines.append(f"- skipped: {referenced['error']}")
    else:
        lines.append(
            f"- referenced_ticker_count={referenced['referenced_ticker_count']}, "
            f"parquet_loaded={referenced['parquet_loaded_ticker_count']}, "
            f"csv_loaded={referenced['csv_loaded_ticker_count']}, "
            f"mismatch_count={referenced['mismatch_count']}"
        )
        for mismatch in referenced.get("mismatches", [])[:10]:
            lines.append(
                f"- {mismatch['ticker']}: parquet_days={mismatch['parquet_day_count']} csv_days={mismatch['csv_day_count']} "
                f"points_equal={mismatch['points_equal']}"
            )

    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    report = build_parity_report(repo_root, args.parquet_file, args.csv_file)

    json_output = Path(args.json_output)
    markdown_output = Path(args.markdown_output)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    markdown_output.write_text(build_markdown_report(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
