from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .build_targeted_backfill_plan import build_targeted_backfill_plan, load_coverage_audit


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Export starter backfill templates from the latest targeted plan.")
    parser.add_argument(
        "--audit-report",
        default=str(repo_root / "reports" / "coverage_audit.json"),
        help="Coverage audit JSON report path.",
    )
    parser.add_argument(
        "--market-template",
        default=str(repo_root / "ingestion" / "templates" / "targeted_market_events_template.json"),
        help="Output path for the market-event template.",
    )
    parser.add_argument(
        "--sec-template",
        default=str(repo_root / "ingestion" / "templates" / "targeted_sec_filings_template.json"),
        help="Output path for the SEC-filings template.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=12,
        help="Maximum number of plan items to consider.",
    )
    return parser.parse_args()


def _market_template_record(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "template_only": True,
        "source_name": "historical_backfill",
        "source_record_id": f"replace-with-real-id-{item['priority_rank']}",
        "headline": "<insert real historical market event headline>",
        "primary_ticker": item.get("primary_ticker") or "<insert primary ticker>",
        "event_type": item["event_category"],
        "sentiment": "<positive|negative|neutral>",
        "occurred_at": "<YYYY-MM-DDTHH:MM:SSZ>",
        "related_companies": [
            {
                "ticker": item.get("related_ticker") or "<insert related ticker>",
                "name": "<insert related company name>",
                "relationship": item.get("relationship_type") or "Related",
                "strength": 0.75,
                "notes": "Replace with a real historical related-company attachment supported by the source."
            }
        ],
        "metadata": {
            "template_source_gap_key": item["source_gap_key"],
            "notes_to_research": item["why_it_matters"],
            "example_guidance": item["suggested_historical_examples_needed"],
        },
    }


def _sec_template_record(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "template_only": True,
        "accession_number": f"replace-with-real-accession-{item['priority_rank']}",
        "form_type": "8-K",
        "filing_date": "<YYYY-MM-DD>",
        "company_name": "<insert filing company name>",
        "ticker": item.get("primary_ticker") or "<insert primary ticker>",
        "headline": "<insert real filing headline>",
        "summary": "<insert real filing summary>",
        "extracted_tags": [item["event_category"], item.get("relationship_type") or item["target_type"]],
        "related_tickers": [
            {
                "ticker": item.get("related_ticker") or "<insert related ticker>",
                "name": "<insert related company name>",
                "relationship": item.get("relationship_type") or "Related",
                "strength": 0.7
            }
        ],
        "metadata": {
            "template_source_gap_key": item["source_gap_key"],
            "notes_to_research": item["why_it_matters"],
            "example_guidance": item["suggested_historical_examples_needed"],
            "expected_related_ticker": item.get("related_ticker"),
        },
    }


def build_backfill_templates(plan_dict: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    market_items = [item for item in plan_dict["plan_items"] if item["suggested_source_type"] == "market-events"]
    sec_items = [item for item in plan_dict["plan_items"] if item["suggested_source_type"] == "sec-filings"]

    market_template = {
        "template_metadata": {
            "purpose": "Fill the highest-priority market-event backfill gaps with real historical records.",
            "generated_from_plan": True,
            "count": len(market_items),
        },
        "events": [_market_template_record(item) for item in market_items],
    }
    sec_template = {
        "template_metadata": {
            "purpose": "Fill the highest-priority SEC-style backfill gaps with real historical filings.",
            "generated_from_plan": True,
            "count": len(sec_items),
        },
        "filings": [_sec_template_record(item) for item in sec_items],
    }
    return market_template, sec_template


def write_templates(market_template: dict[str, Any], sec_template: dict[str, Any], market_output: Path, sec_output: Path) -> None:
    market_output.parent.mkdir(parents=True, exist_ok=True)
    sec_output.parent.mkdir(parents=True, exist_ok=True)
    market_output.write_text(json.dumps(market_template, indent=2), encoding="utf-8")
    sec_output.write_text(json.dumps(sec_template, indent=2), encoding="utf-8")


def main() -> int:
    args = parse_args()
    audit_report = load_coverage_audit(args.audit_report)
    plan = build_targeted_backfill_plan(audit_report, limit=args.limit)
    market_template, sec_template = build_backfill_templates(plan.to_dict())
    write_templates(market_template, sec_template, Path(args.market_template), Path(args.sec_template))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
