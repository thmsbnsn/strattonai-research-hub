from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ALLOWED_REVIEW_STATUSES = {"approved_for_ingestion", "pending_review", "pending_research", "needs_more_research", "rejected"}
SEC_FORM_TYPES = ("8-K", "10-Q", "10-K", "6-K", "20-F")


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description="Convert an n8n targeted-research review bundle into source-specific ingestion bundles."
    )
    parser.add_argument(
        "--input",
        default=str(repo_root / "ingestion" / "templates" / "n8n_targeted_research_template.json"),
        help="Path to the completed n8n review bundle JSON.",
    )
    parser.add_argument(
        "--market-output",
        default=str(repo_root / "ingestion" / "generated" / "n8n_market_events_review_bundle.json"),
        help="Output path for approved market-event examples.",
    )
    parser.add_argument(
        "--sec-output",
        default=str(repo_root / "ingestion" / "generated" / "n8n_sec_filings_review_bundle.json"),
        help="Output path for approved SEC-style examples.",
    )
    parser.add_argument(
        "--report-output",
        default=str(repo_root / "reports" / "n8n_handoff_summary.json"),
        help="Output path for the conversion summary report.",
    )
    parser.add_argument(
        "--include-pending-review",
        action="store_true",
        help="Also export examples from slices still marked pending_review if the example itself is ready_for_ingestion=true.",
    )
    return parser.parse_args()


def load_review_bundle(path: str | Path) -> dict[str, Any]:
    bundle_path = Path(path)
    payload = json.loads(bundle_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Expected the n8n review bundle to be a JSON object.")
    research_slices = payload.get("research_slices")
    if not isinstance(research_slices, list):
        raise ValueError("Expected the n8n review bundle to contain a 'research_slices' array.")
    for item in research_slices:
        if not isinstance(item, dict):
            raise ValueError("Each research_slices item must be a JSON object.")
    return payload


def _normalize_related_companies(
    example: dict[str, Any],
    slice_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    related_companies = example.get("related_companies")
    normalized: list[dict[str, Any]] = []
    if isinstance(related_companies, list):
        for item in related_companies:
            if not isinstance(item, dict):
                continue
            ticker = str(item.get("ticker") or "").strip().upper()
            if not ticker:
                continue
            normalized.append(
                {
                    "ticker": ticker,
                    "name": item.get("name") or ticker,
                    "relationship": item.get("relationship") or slice_payload.get("relationship_type") or "Related",
                    "strength": item.get("strength", 0.75),
                    "notes": item.get("notes"),
                }
            )

    if normalized:
        return normalized

    related_ticker = str(slice_payload.get("related_ticker") or "").strip().upper()
    if not related_ticker:
        return []

    return [
        {
            "ticker": related_ticker,
            "name": related_ticker,
            "relationship": slice_payload.get("relationship_type") or "Related",
            "strength": 0.75,
            "notes": "Derived from the reviewed slice because the example did not carry an explicit related_companies payload.",
        }
    ]


def _approved_for_handoff(slice_payload: dict[str, Any], example: dict[str, Any], include_pending_review: bool) -> bool:
    if example.get("ready_for_ingestion") is not True:
        return False
    review_status = str(slice_payload.get("review_status") or "").strip()
    if review_status not in ALLOWED_REVIEW_STATUSES:
        return False
    if review_status == "approved_for_ingestion":
        return True
    return include_pending_review and review_status == "pending_review"


def _as_iso_timestamp(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _infer_sec_form_type(example: dict[str, Any]) -> str:
    candidate_text = " ".join(
        str(example.get(field) or "")
        for field in ("source_title", "headline", "evidence_quote", "summary", "source_record_id")
    )
    for form_type in SEC_FORM_TYPES:
        if re.search(rf"(?<![A-Z0-9]){re.escape(form_type)}(?![A-Z0-9])", candidate_text, re.IGNORECASE):
            return form_type
    return "8-K"


def _infer_company_name(example: dict[str, Any], slice_payload: dict[str, Any], form_type: str) -> str:
    source_title = str(example.get("source_title") or "").strip()
    if source_title:
        normalized = re.sub(rf"\s+{re.escape(form_type)}\b.*$", "", source_title, flags=re.IGNORECASE).strip()
        if normalized:
            return normalized
    return str(slice_payload.get("primary_ticker") or example.get("primary_ticker") or "UNKNOWN").strip().upper()


def _build_market_event_record(slice_payload: dict[str, Any], example: dict[str, Any]) -> dict[str, Any]:
    related_companies = _normalize_related_companies(example, slice_payload)
    sentiment = str(example.get("sentiment_hint") or "neutral").strip().lower()
    if sentiment not in {"positive", "negative", "neutral"}:
        sentiment = "neutral"

    return {
        "source_name": example["source_name"],
        "source_record_id": example["source_record_id"],
        "headline": example.get("headline") or example.get("source_title") or "Reviewed historical market event",
        "primary_ticker": str(example.get("primary_ticker") or slice_payload.get("primary_ticker") or "").strip().upper(),
        "event_type": example.get("event_type_hint") or slice_payload.get("event_category"),
        "sentiment": sentiment,
        "occurred_at": _as_iso_timestamp(example.get("occurred_at")) or _as_iso_timestamp(example.get("published_at")),
        "details": example.get("summary"),
        "related_companies": related_companies,
        "metadata": {
            "template_source_gap_key": slice_payload.get("source_gap_key"),
            "n8n_review_status": slice_payload.get("review_status"),
            "n8n_reviewer_notes": slice_payload.get("reviewer_notes"),
            "source_url": example.get("source_url"),
            "source_title": example.get("source_title"),
            "source_publisher": example.get("source_publisher"),
            "published_at": example.get("published_at"),
            "evidence_quote": example.get("evidence_quote"),
            "extraction_notes": example.get("extraction_notes"),
            "relationship_evidence": example.get("relationship_evidence"),
            "duplicate_check_key": example.get("duplicate_check_key"),
        },
    }


def _build_sec_filing_record(slice_payload: dict[str, Any], example: dict[str, Any]) -> dict[str, Any]:
    related_companies = _normalize_related_companies(example, slice_payload)
    filing_date = (_as_iso_timestamp(example.get("occurred_at")) or _as_iso_timestamp(example.get("published_at")) or "")[:10]
    form_type = _infer_sec_form_type(example)
    return {
        "accession_number": example["source_record_id"],
        "form_type": form_type,
        "filing_date": filing_date,
        "company_name": _infer_company_name(example, slice_payload, form_type),
        "ticker": str(example.get("primary_ticker") or slice_payload.get("primary_ticker") or "").strip().upper(),
        "headline": example.get("headline") or example.get("source_title") or "Reviewed SEC filing candidate",
        "summary": example.get("summary"),
        "extracted_tags": [
            slice_payload.get("event_category"),
            slice_payload.get("relationship_type") or slice_payload.get("target_type"),
        ],
        "related_tickers": [
            {
                "ticker": item["ticker"],
                "name": item["name"],
                "relationship": item["relationship"],
                "strength": item.get("strength", 0.7),
            }
            for item in related_companies
        ],
        "metadata": {
            "template_source_gap_key": slice_payload.get("source_gap_key"),
            "n8n_review_status": slice_payload.get("review_status"),
            "n8n_reviewer_notes": slice_payload.get("reviewer_notes"),
            "source_name": example.get("source_name"),
            "source_url": example.get("source_url"),
            "source_title": example.get("source_title"),
            "source_publisher": example.get("source_publisher"),
            "published_at": example.get("published_at"),
            "evidence_quote": example.get("evidence_quote"),
            "extraction_notes": example.get("extraction_notes"),
            "expected_related_ticker": slice_payload.get("related_ticker"),
            "duplicate_check_key": example.get("duplicate_check_key"),
        },
    }


def build_handoff_bundles(
    review_bundle: dict[str, Any],
    *,
    include_pending_review: bool = False,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    market_events: list[dict[str, Any]] = []
    sec_filings: list[dict[str, Any]] = []
    seen_market_keys: set[str] = set()
    seen_sec_keys: set[str] = set()
    skipped_examples: list[dict[str, Any]] = []

    for slice_payload in review_bundle.get("research_slices", []):
        source_type = str(slice_payload.get("suggested_source_type") or "market-events").strip()
        collected_examples = slice_payload.get("collected_examples") or []
        if not isinstance(collected_examples, list):
            skipped_examples.append(
                {
                    "source_gap_key": slice_payload.get("source_gap_key"),
                    "reason": "collected_examples_not_list",
                }
            )
            continue

        for example in collected_examples:
            if not isinstance(example, dict):
                skipped_examples.append(
                    {
                        "source_gap_key": slice_payload.get("source_gap_key"),
                        "reason": "collected_example_not_object",
                    }
                )
                continue
            if not _approved_for_handoff(slice_payload, example, include_pending_review):
                continue

            duplicate_key = str(example.get("duplicate_check_key") or "").strip()
            if source_type == "sec-filings":
                dedupe_key = duplicate_key or f"sec|{example.get('source_name')}|{example.get('source_record_id')}"
                if dedupe_key in seen_sec_keys:
                    continue
                seen_sec_keys.add(dedupe_key)
                sec_filings.append(_build_sec_filing_record(slice_payload, example))
            else:
                dedupe_key = duplicate_key or f"market|{example.get('source_name')}|{example.get('source_record_id')}"
                if dedupe_key in seen_market_keys:
                    continue
                seen_market_keys.add(dedupe_key)
                market_events.append(_build_market_event_record(slice_payload, example))

    market_bundle = {
        "template_metadata": {
            "purpose": "Approved n8n-reviewed market-event examples ready for deterministic ingestion.",
            "generated_from_n8n_review_bundle": True,
            "count": len(market_events),
        },
        "events": market_events,
    }
    sec_bundle = {
        "template_metadata": {
            "purpose": "Approved n8n-reviewed SEC-style examples ready for deterministic ingestion.",
            "generated_from_n8n_review_bundle": True,
            "count": len(sec_filings),
        },
        "filings": sec_filings,
    }
    report = {
        "input_slice_count": len(review_bundle.get("research_slices", [])),
        "market_event_count": len(market_events),
        "sec_filing_count": len(sec_filings),
        "skipped_examples": skipped_examples,
        "include_pending_review": include_pending_review,
    }
    return market_bundle, sec_bundle, report


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    args = parse_args()
    review_bundle = load_review_bundle(args.input)
    market_bundle, sec_bundle, report = build_handoff_bundles(
        review_bundle,
        include_pending_review=args.include_pending_review,
    )
    write_json(args.market_output, market_bundle)
    write_json(args.sec_output, sec_bundle)
    write_json(args.report_output, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
