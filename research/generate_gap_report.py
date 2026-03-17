from __future__ import annotations

import argparse
import json
from pathlib import Path

from .coverage_audit import run_coverage_audit, write_coverage_reports


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Generate deterministic coverage audit reports.")
    parser.add_argument(
        "--price-file",
        default=None,
        help="Optional explicit price dataset path (.parquet, .csv, or .json). Defaults resolve to Parquet first.",
    )
    parser.add_argument(
        "--json-output",
        default=str(repo_root / "reports" / "coverage_audit.json"),
        help="Path for the JSON coverage report.",
    )
    parser.add_argument(
        "--markdown-output",
        default=str(repo_root / "reports" / "coverage_audit.md"),
        help="Path for the Markdown coverage report.",
    )
    parser.add_argument("--compare-previous", action="store_true", help="Write a diff against the prior coverage_audit.json report if present.")
    return parser.parse_args()


def _build_diff(previous: dict, current: dict) -> dict:
    category_gains = {}
    for category, current_count in current.get("event_counts_by_category", {}).items():
        previous_count = previous.get("event_counts_by_category", {}).get(category, 0)
        if current_count > previous_count:
            category_gains[category] = current_count - previous_count

    previous_missing = {item.get("ticker"): item.get("available_days", 0) for item in previous.get("missing_price_history", [])}
    current_missing = {item.get("ticker"): item.get("available_days", 0) for item in current.get("missing_price_history", [])}
    price_improvements = {
        ticker: current_missing.get(ticker, 0) - previous_days
        for ticker, previous_days in previous_missing.items()
        if current_missing.get(ticker, 0) > previous_days
    }

    previous_gaps = {item.get("gap_key") for item in previous.get("top_gap_candidates", [])}
    new_slices = [item for item in current.get("top_gap_candidates", []) if item.get("gap_key") not in previous_gaps]

    return {
        "category_sample_gains": category_gains,
        "signals_confidence_upgrades": [],
        "tickers_with_price_coverage_improved": price_improvements,
        "new_study_slices": new_slices,
    }


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    previous_path = repo_root / "reports" / "coverage_audit.json"
    previous_report = None
    if args.compare_previous and previous_path.exists():
        previous_report = json.loads(previous_path.read_text(encoding="utf-8"))
    report = run_coverage_audit(repo_root, args.price_file)
    write_coverage_reports(report, Path(args.json_output), Path(args.markdown_output))
    if args.compare_previous and previous_report is not None:
        current_report = report.to_dict()
        diff = _build_diff(previous_report, current_report)
        diff_json = repo_root / "reports" / "coverage_audit_diff.json"
        diff_md = repo_root / "reports" / "coverage_audit_diff.md"
        diff_json.write_text(json.dumps(diff, indent=2), encoding="utf-8")
        diff_md.write_text(
            "\n".join(
                [
                    "# Coverage Audit Diff",
                    "",
                    "## Category Sample Gains",
                    *[
                        f"- {category}: +{gain}"
                        for category, gain in sorted(diff["category_sample_gains"].items())
                    ],
                    "",
                    "## Price Coverage Improvements",
                    *[
                        f"- {ticker}: +{gain} available days"
                        for ticker, gain in sorted(diff["tickers_with_price_coverage_improved"].items())
                    ],
                    "",
                    "## New Study Slices",
                    *[
                        f"- {item.get('title') or item.get('gap_key')}"
                        for item in diff["new_study_slices"]
                    ],
                    "",
                ]
            ),
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
