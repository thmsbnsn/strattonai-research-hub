from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .map_financial_news_to_event import get_financial_news_company_mapping_decision, resolve_financial_news_company_ticker


CANONICAL_FILENAMES = (
    "financial_news_events.csv",
    "financial_news_events.json",
    "financial_news_events.xlsx",
)
KEY_FIELDS = ("Date", "Headline", "Source", "Market_Event", "Related_Company")


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent.parent.parent
    parser = argparse.ArgumentParser(description="Inspect the local financial-news dataset and write a deterministic summary report.")
    parser.add_argument(
        "--input-dir",
        default=str(repo_root / "data" / "events" / "financialNews"),
        help="Directory containing the financial-news dataset files.",
    )
    parser.add_argument(
        "--json-output",
        default=str(repo_root / "ui" / "reports" / "financial_news_dataset_inspection.json"),
        help="JSON output path for the inspection report.",
    )
    parser.add_argument(
        "--markdown-output",
        default=str(repo_root / "ui" / "reports" / "financial_news_dataset_inspection.md"),
        help="Markdown output path for the inspection report.",
    )
    return parser.parse_args()


def resolve_canonical_file(input_dir: Path) -> tuple[Path, list[dict[str, Any]]]:
    alternate_files: list[dict[str, Any]] = []
    for filename in CANONICAL_FILENAMES:
        file_path = input_dir / filename
        if file_path.exists():
            alternate_files.append(
                {
                    "path": str(file_path),
                    "name": file_path.name,
                    "size_bytes": file_path.stat().st_size,
                }
            )

    if not alternate_files:
        raise FileNotFoundError(f"No supported financial-news files found under {input_dir}")

    canonical = next((item for item in alternate_files if item["name"].endswith(".csv")), alternate_files[0])
    return Path(canonical["path"]), alternate_files


def inspect_financial_news_dataset(input_dir: Path) -> dict[str, Any]:
    canonical_file, alternate_files = resolve_canonical_file(input_dir)
    with canonical_file.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [dict(row) for row in reader]
        columns = list(reader.fieldnames or [])

    dates = sorted(row["Date"] for row in rows if (row.get("Date") or "").strip())
    duplicate_counter = Counter(tuple((row.get(field) or "").strip() for field in KEY_FIELDS) for row in rows)
    company_counts = Counter((row.get("Related_Company") or "").strip() for row in rows if (row.get("Related_Company") or "").strip())
    market_event_counts = Counter((row.get("Market_Event") or "").strip() for row in rows if (row.get("Market_Event") or "").strip())

    company_mapping_decisions = {
        company_name: get_financial_news_company_mapping_decision(company_name)
        for company_name in sorted(company_counts)
    }
    company_mapping = {
        company_name: resolve_financial_news_company_ticker(company_name)
        for company_name in sorted(company_counts)
    }
    unmapped_companies = {
        company_name: {
            "row_count": count,
            "reason": company_mapping_decisions[company_name].notes if company_mapping_decisions.get(company_name) is not None else "No deterministic company mapping has been configured for this name.",
        }
        for company_name, count in company_counts.items()
        if company_mapping.get(company_name) is None
    }
    mapped_companies = {
        company_name: {
            "ticker": ticker,
            "strategy": company_mapping_decisions[company_name].strategy if company_mapping_decisions.get(company_name) is not None else "configured_mapping",
            "notes": company_mapping_decisions[company_name].notes if company_mapping_decisions.get(company_name) is not None else "Deterministic company mapping configured.",
        }
        for company_name, ticker in company_mapping.items()
        if ticker is not None
    }

    return {
        "input_dir": str(input_dir),
        "canonical_file": str(canonical_file),
        "alternate_representations": alternate_files,
        "row_count": len(rows),
        "columns": columns,
        "date_range": {
            "min": dates[0] if dates else None,
            "max": dates[-1] if dates else None,
        },
        "headline_field": "Headline",
        "company_field": "Related_Company",
        "duplicate_rate": round(
            (sum(count - 1 for count in duplicate_counter.values() if count > 1) / len(rows)),
            6,
        )
        if rows
        else 0.0,
        "duplicate_rows": sum(count - 1 for count in duplicate_counter.values() if count > 1),
        "missing_key_fields": {
            "Date": sum(1 for row in rows if not (row.get("Date") or "").strip()),
            "Headline": sum(1 for row in rows if not (row.get("Headline") or "").strip()),
            "Source": sum(1 for row in rows if not (row.get("Source") or "").strip()),
            "Market_Event": sum(1 for row in rows if not (row.get("Market_Event") or "").strip()),
            "Related_Company": sum(1 for row in rows if not (row.get("Related_Company") or "").strip()),
        },
        "market_event_counts": dict(sorted(market_event_counts.items())),
        "related_company_counts": dict(sorted(company_counts.items())),
        "mapped_company_tickers": mapped_companies,
        "unmapped_companies": dict(sorted(unmapped_companies.items())),
    }


def build_markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Financial News Dataset Inspection",
        "",
        f"- Canonical source: `{report['canonical_file']}`",
        f"- Row count: {report['row_count']}",
        f"- Date range: {report['date_range']['min']} -> {report['date_range']['max']}",
        f"- Duplicate rows: {report['duplicate_rows']} ({report['duplicate_rate']:.2%})",
        "",
        "## Columns",
    ]
    for column in report["columns"]:
        lines.append(f"- {column}")

    lines.extend(["", "## Missing Key Fields"])
    for field_name, count in report["missing_key_fields"].items():
        lines.append(f"- {field_name}: {count}")

    lines.extend(["", "## Company Mapping"])
    for company_name, item in report["mapped_company_tickers"].items():
        lines.append(f"- {company_name}: {item['ticker']} ({item['strategy']})")
    for company_name, item in report["unmapped_companies"].items():
        lines.append(f"- UNMAPPED {company_name}: {item['row_count']} rows. Reason: {item['reason']}")

    lines.extend(["", "## Alternate Representations"])
    for item in report["alternate_representations"]:
        lines.append(f"- {item['name']}: {item['size_bytes']} bytes")

    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    report = inspect_financial_news_dataset(Path(args.input_dir))

    json_output = Path(args.json_output)
    markdown_output = Path(args.markdown_output)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    markdown_output.write_text(build_markdown_report(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
