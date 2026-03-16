from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .backfill_plan_models import BackfillPlanGroup, BackfillPlanItem, TargetedBackfillPlan


SEC_FRIENDLY_CATEGORIES = {
    "Capital Expenditure",
    "Earnings",
    "Legal/Regulatory",
    "Partnership",
    "Regulatory Approval",
}
GRAPH_PRIORITY_TICKERS = {
    "NVDA": 1.0,
    "MSFT": 0.98,
    "AAPL": 0.95,
    "GOOGL": 0.93,
    "TSM": 0.92,
    "AMD": 0.9,
    "LLY": 0.9,
    "NVO": 0.87,
    "AMZN": 0.86,
    "ORCL": 0.82,
    "META": 0.8,
    "QCOM": 0.79,
    "AVGO": 0.78,
    "TSLA": 0.78,
    "RIVN": 0.74,
}
CATEGORY_UPLIFT = {
    "Macro Event": 1.0,
    "Legal/Regulatory": 0.95,
    "Product Launch": 0.92,
    "Partnership": 0.88,
    "Earnings": 0.87,
    "Supply Disruption": 0.84,
    "Regulatory Approval": 0.83,
    "Capital Expenditure": 0.8,
}


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Build a targeted backfill plan from coverage audit output.")
    parser.add_argument(
        "--audit-report",
        default=str(repo_root / "reports" / "coverage_audit.json"),
        help="Coverage audit JSON report path.",
    )
    parser.add_argument(
        "--json-output",
        default=str(repo_root / "reports" / "targeted_backfill_plan.json"),
        help="Path for targeted backfill plan JSON.",
    )
    parser.add_argument(
        "--markdown-output",
        default=str(repo_root / "reports" / "targeted_backfill_plan.md"),
        help="Path for targeted backfill plan Markdown.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=12,
        help="Maximum number of plan items to include.",
    )
    return parser.parse_args()


def load_coverage_audit(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    payload["_source_report_path"] = str(Path(path))
    return payload


def choose_source_type(event_category: str, target_type: str, relationship_type: str | None) -> str:
    if event_category in SEC_FRIENDLY_CATEGORIES:
        return "sec-filings" if target_type in {"related", "category"} or relationship_type not in {"Supplier", "Competitor"} else "market-events"
    return "market-events"


def _ticker_importance(*tickers: str | None) -> float:
    values = [GRAPH_PRIORITY_TICKERS.get(ticker or "", 0.65) for ticker in tickers if ticker]
    return max(values) if values else 0.65


def _normalize_gap_size(current_sample_size: int, desired_min_sample_size: int) -> int:
    return max(desired_min_sample_size - current_sample_size, 1)


def _extract_item_from_candidate(candidate: dict[str, Any], weak_categories: dict[str, dict[str, Any]]) -> BackfillPlanItem:
    event_category = candidate.get("event_category") or "Unknown"
    target_type = candidate.get("target_type") or "category"
    relationship_type = candidate.get("relationship_type")
    related_ticker = candidate.get("ticker")
    current_sample_size = max(int(candidate.get("required_additional_examples", 1)) * -1, 0)
    # Recover current sample size from the narrative if available. Fall back to zero.
    rationale = str(candidate.get("rationale") or "")
    current_sample_size = 0
    if "sample " in rationale:
        try:
            current_sample_size = int(rationale.split("sample ", 1)[1].split(",", 1)[0])
        except (ValueError, IndexError):
            current_sample_size = 0

    desired_min_sample_size = current_sample_size + int(candidate.get("required_additional_examples", 1))
    gap_size = _normalize_gap_size(current_sample_size, desired_min_sample_size)

    weak_category = weak_categories.get(event_category, {})
    source_type = choose_source_type(event_category, target_type, relationship_type)
    planner_score = round(
        float(candidate.get("gap_score", 0))
        + CATEGORY_UPLIFT.get(event_category, 0.7) * 10
        + _ticker_importance(related_ticker) * 8
        + float(weak_category.get("gap_score", 0)) * 0.25,
        2,
    )
    why_it_matters = (
        f"{event_category} remains weak in the audit and this slice is repeatedly used by current signals. "
        f"{candidate.get('rationale', '')}"
    ).strip()
    example_prompts = [
        f"Find a real historical {event_category} example involving {related_ticker or 'the target company'}."
    ]
    if relationship_type:
        example_prompts.append(
            f"Prefer examples where the related-company path is explicitly {relationship_type}."
        )
    if weak_category:
        example_prompts.append(
            f"This category currently has {weak_category.get('high', 0)} high-confidence signals and "
            f"{weak_category.get('low', 0)} low-confidence signals."
        )

    return BackfillPlanItem(
        priority_rank=0,
        event_category=event_category,
        primary_ticker=None,
        related_ticker=related_ticker,
        relationship_type=relationship_type,
        target_type=target_type,
        current_sample_size=current_sample_size,
        desired_min_sample_size=desired_min_sample_size,
        gap_size=gap_size,
        why_it_matters=why_it_matters,
        suggested_source_type=source_type,
        suggested_historical_examples_needed=example_prompts,
        planner_score=planner_score,
        source_gap_key=str(candidate.get("candidate_key") or candidate.get("gap_key") or event_category),
        notes={
            "audit_gap_score": candidate.get("gap_score", 0),
            "required_additional_examples": candidate.get("required_additional_examples", gap_size),
        },
    )


def _build_macro_category_item(weak_category: dict[str, Any]) -> BackfillPlanItem:
    event_category = weak_category["event_category"]
    gap_size = max(5 - int(weak_category.get("high", 0)), 3)
    planner_score = round(float(weak_category.get("gap_score", 0)) + CATEGORY_UPLIFT.get(event_category, 0.7) * 14, 2)
    return BackfillPlanItem(
        priority_rank=0,
        event_category=event_category,
        primary_ticker="MSFT",
        related_ticker="GOOGL",
        relationship_type="Sector Peer",
        target_type="category",
        current_sample_size=2,
        desired_min_sample_size=2 + gap_size,
        gap_size=gap_size,
        why_it_matters=(
            f"{event_category} is the thinnest category in the audit and still has no high-confidence signals. "
            "A small number of well-chosen macro examples can materially improve category and peer-path depth."
        ),
        suggested_source_type="market-events",
        suggested_historical_examples_needed=[
            "Find real macro-driven tech-sector reactions where MSFT or NVDA is the primary ticker.",
            "Include sector-peer attachments such as GOOGL or AMZN when the macro shock clearly affects them.",
        ],
        planner_score=planner_score,
        source_gap_key=f"category::{event_category}",
        notes={"audit_gap_score": weak_category.get("gap_score", 0), "special_focus": "category_balance"},
    )


def build_targeted_backfill_plan(audit_report: dict[str, Any], limit: int = 12) -> TargetedBackfillPlan:
    top_candidates = audit_report.get("top_gap_candidates", [])
    weak_categories_list = audit_report.get("weak_signal_categories", [])
    weak_categories = {item["event_category"]: item for item in weak_categories_list if "event_category" in item}

    items: list[BackfillPlanItem] = []
    for candidate in top_candidates:
        items.append(_extract_item_from_candidate(candidate, weak_categories))

    if "Macro Event" in weak_categories and not any(item.event_category == "Macro Event" for item in items):
        items.append(_build_macro_category_item(weak_categories["Macro Event"]))

    items.sort(key=lambda item: (-item.planner_score, item.source_gap_key))
    ranked_items: list[BackfillPlanItem] = []
    for index, item in enumerate(items[:limit], start=1):
        ranked_items.append(
            BackfillPlanItem(
                priority_rank=index,
                event_category=item.event_category,
                primary_ticker=item.primary_ticker,
                related_ticker=item.related_ticker,
                relationship_type=item.relationship_type,
                target_type=item.target_type,
                current_sample_size=item.current_sample_size,
                desired_min_sample_size=item.desired_min_sample_size,
                gap_size=item.gap_size,
                why_it_matters=item.why_it_matters,
                suggested_source_type=item.suggested_source_type,
                suggested_historical_examples_needed=item.suggested_historical_examples_needed,
                planner_score=item.planner_score,
                source_gap_key=item.source_gap_key,
                notes=item.notes,
            )
        )

    grouped: dict[tuple[str, str], list[BackfillPlanItem]] = defaultdict(list)
    for item in ranked_items:
        grouped[(item.suggested_source_type, item.event_category)].append(item)

    groups = [
        BackfillPlanGroup(
            group_key=f"{source_type}::{event_category}",
            source_type=source_type,
            event_category=event_category,
            plan_item_keys=[item.source_gap_key for item in group_items],
            total_gap_size=sum(item.gap_size for item in group_items),
            rationale=(
                f"Collect this set together because all items share {event_category} and are best sourced through {source_type}."
            ),
        )
        for (source_type, event_category), group_items in sorted(grouped.items())
    ]

    return TargetedBackfillPlan(
        generated_from_report=str(audit_report.get("_source_report_path", "coverage_audit.json")),
        plan_items=tuple(ranked_items),
        groups=tuple(groups),
        notes={
            "input_top_gap_candidates": len(top_candidates),
            "included_macro_category_item": "Macro Event" in weak_categories,
        },
    )


def build_markdown_plan(plan: TargetedBackfillPlan) -> str:
    lines = ["# Targeted Backfill Plan", "", "## Ranked Targets"]
    for item in plan.plan_items:
        target_label = item.related_ticker or item.primary_ticker or "category-level target"
        lines.append(
            f"- #{item.priority_rank} {item.event_category} / {target_label} / {item.relationship_type or item.target_type} "
            f"(gap_size={item.gap_size}, source={item.suggested_source_type}, planner_score={item.planner_score})"
        )
        lines.append(f"  Why: {item.why_it_matters}")
        lines.append(f"  Needed: desired sample {item.desired_min_sample_size} from current {item.current_sample_size}")

    lines.extend(["", "## Collection Groups"])
    for group in plan.groups:
        lines.append(
            f"- {group.group_key}: {len(group.plan_item_keys)} targets, total gap size {group.total_gap_size}. {group.rationale}"
        )

    return "\n".join(lines) + "\n"


def write_targeted_backfill_plan(plan: TargetedBackfillPlan, json_output: Path, markdown_output: Path) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(plan.to_dict(), indent=2), encoding="utf-8")
    markdown_output.write_text(build_markdown_plan(plan), encoding="utf-8")


def main() -> int:
    args = parse_args()
    audit_report = load_coverage_audit(args.audit_report)
    plan = build_targeted_backfill_plan(audit_report, limit=args.limit)
    write_targeted_backfill_plan(plan, Path(args.json_output), Path(args.markdown_output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
