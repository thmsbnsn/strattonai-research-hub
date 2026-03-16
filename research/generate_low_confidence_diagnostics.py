from __future__ import annotations

import argparse
import json
from pathlib import Path

from .low_confidence_diagnostics import (
    LowConfidenceDiagnosticsRepository,
    build_low_confidence_diagnostics_report,
    write_low_confidence_reports,
)


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Generate deterministic low-confidence diagnostics from stored signals.")
    parser.add_argument(
        "--plan-report",
        default=str(repo_root / "reports" / "targeted_backfill_plan.json"),
        help="Targeted backfill plan JSON path.",
    )
    parser.add_argument(
        "--json-output",
        default=str(repo_root / "reports" / "low_confidence_diagnostics.json"),
        help="Diagnostics JSON output path.",
    )
    parser.add_argument(
        "--markdown-output",
        default=str(repo_root / "reports" / "low_confidence_diagnostics.md"),
        help="Diagnostics Markdown output path.",
    )
    parser.add_argument(
        "--focus-slice-keys",
        nargs="*",
        default=[],
        help="Optional exact slice keys to highlight.",
    )
    return parser.parse_args()


def _load_plan(path: str | Path) -> dict:
    plan_path = Path(path)
    if not plan_path.exists():
        return {}
    return json.loads(plan_path.read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    repository = LowConfidenceDiagnosticsRepository(repo_root)
    signal_records = repository.load_signal_records()
    plan = _load_plan(args.plan_report)
    report = build_low_confidence_diagnostics_report(
        signal_records,
        plan=plan,
        focus_slice_keys=tuple(args.focus_slice_keys),
    )
    write_low_confidence_reports(report, Path(args.json_output), Path(args.markdown_output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
