from __future__ import annotations

import argparse
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    report = run_coverage_audit(repo_root, args.price_file)
    write_coverage_reports(report, Path(args.json_output), Path(args.markdown_output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
