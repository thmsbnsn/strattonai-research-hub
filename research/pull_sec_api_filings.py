from __future__ import annotations

import argparse
import json
import logging
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import requests

from .trading_repository import TradingRepository


LOGGER = logging.getLogger("research.pull_sec_api_filings")
QUERY_URL = "https://api.sec-api.io"
DEFAULT_FORMS = ("8-K", "10-Q", "10-K")
DEFAULT_EXCLUDED_TICKERS = {"TTM"}


@dataclass(frozen=True, slots=True)
class PulledFiling:
    accession_number: str
    form_type: str
    filing_date: str
    company_name: str
    ticker: str
    headline: str
    summary: str | None
    extracted_tags: list[str]
    related_tickers: list[dict[str, Any]]
    metadata: dict[str, Any]

    def to_ingestion_payload(self) -> dict[str, Any]:
        return asdict(self)


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format="%(levelname)s %(message)s")


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent.parent
    data_root = repo_root.parent / "data" / "events" / "secApi"
    parser = argparse.ArgumentParser(description="Pull useful SEC filings via sec-api.io into a local reusable dataset.")
    parser.add_argument("--start-date", default="2025-01-01")
    parser.add_argument("--end-date", default=date.today().isoformat())
    parser.add_argument("--ticker", action="append", default=[], help="Optional ticker override. Repeatable.")
    parser.add_argument("--exclude-ticker", action="append", default=[], help="Optional ticker exclusions. Repeatable.")
    parser.add_argument("--form-type", action="append", default=[], help="Optional SEC form types. Repeatable.")
    parser.add_argument("--limit-per-ticker", type=int, default=5)
    parser.add_argument("--page-size", type=int, default=50)
    parser.add_argument("--download-text", action="store_true", help="Download raw .txt filing documents when linkToTxt is present.")
    parser.add_argument(
        "--output",
        default=str(data_root / f"sec_api_filings_{date.today().isoformat()}.json"),
        help="Normalized JSON output for the existing sec-filings ingestion path.",
    )
    parser.add_argument(
        "--metadata-output",
        default=str(data_root / f"sec_api_filings_metadata_{date.today().isoformat()}.json"),
        help="Raw metadata output path.",
    )
    parser.add_argument(
        "--raw-dir",
        default=str(data_root / "raw"),
        help="Directory where raw filing text files will be stored when --download-text is enabled.",
    )
    parser.add_argument(
        "--report-output",
        default=str(repo_root / "reports" / "sec_api_pull.json"),
        help="Summary report JSON path.",
    )
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def _load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _normalize_tickers(values: list[str]) -> list[str]:
    return sorted({value.strip().upper() for value in values if value and value.strip()})


def _resolve_target_tickers(repo_root: Path, ticker_overrides: list[str], excluded: set[str]) -> list[str]:
    if ticker_overrides:
        return [ticker for ticker in _normalize_tickers(ticker_overrides) if ticker not in excluded]
    repository = TradingRepository(repo_root)
    return [ticker for ticker in repository.distinct_event_tickers() if ticker not in excluded]


def _build_query(ticker: str, form_types: tuple[str, ...], start_date: str, end_date: str) -> str:
    forms = " OR ".join(f'formType:"{form_type}"' for form_type in form_types)
    return f"ticker:{ticker} AND ({forms}) AND filedAt:[{start_date} TO {end_date}]"


def _fetch_filings(api_key: str, ticker: str, form_types: tuple[str, ...], start_date: str, end_date: str, limit: int, page_size: int) -> list[dict[str, Any]]:
    filings: list[dict[str, Any]] = []
    offset = 0
    while len(filings) < limit:
        payload = {
            "query": _build_query(ticker, form_types, start_date, end_date),
            "from": str(offset),
            "size": str(min(page_size, limit - len(filings))),
            "sort": [{"filedAt": {"order": "desc"}}],
        }
        response = requests.post(
            QUERY_URL,
            headers={"Authorization": api_key, "Content-Type": "application/json"},
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        response_payload = response.json()
        batch = response_payload.get("filings") or []
        if not batch:
            break
        filings.extend(batch)
        if len(batch) < min(page_size, limit - len(filings) + len(batch)):
            break
        offset += len(batch)
    return filings[:limit]


def _safe_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _extract_tags(filing: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    for item in filing.get("items") or []:
        if not item:
            continue
        text = str(item).strip()
        if ":" in text:
            text = text.split(":", 1)[1].strip()
        if text:
            tags.append(text.lower())
    description = _safe_text(filing.get("description"))
    if description:
        tags.append(description.lower())
    return sorted(dict.fromkeys(tags))


def _normalize_filing(filing: dict[str, Any]) -> PulledFiling:
    accession_number = str(filing.get("accessionNo") or "").strip()
    form_type = str(filing.get("formType") or "").strip()
    filed_at = _safe_text(filing.get("filedAt")) or ""
    filing_date = filed_at[:10]
    company_name = _safe_text(filing.get("companyName")) or ""
    ticker = str(filing.get("ticker") or "").strip().upper()
    items = filing.get("items") or []
    headline = _safe_text(filing.get("description")) or f"{company_name} filed {form_type}"
    summary = "; ".join(str(item).strip() for item in items if str(item).strip()) or headline
    return PulledFiling(
        accession_number=accession_number,
        form_type=form_type,
        filing_date=filing_date,
        company_name=company_name,
        ticker=ticker,
        headline=headline,
        summary=summary,
        extracted_tags=_extract_tags(filing),
        related_tickers=[],
        metadata={
            "source_type": "sec_api",
            "filed_at": filed_at,
            "link_to_txt": filing.get("linkToTxt"),
            "link_to_html": filing.get("linkToHtml"),
            "link_to_filing_details": filing.get("linkToFilingDetails"),
            "entities": filing.get("entities") or [],
            "items": items,
            "data_files": filing.get("dataFiles") or [],
            "document_format_files": filing.get("documentFormatFiles") or [],
            "description": filing.get("description"),
        },
    )


def _download_raw_text(link: str, output_path: Path) -> bool:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(
        link,
        headers={"User-Agent": "StrattonAI/1.0 local research workspace"},
        timeout=60,
    )
    response.raise_for_status()
    output_path.write_bytes(response.content)
    return True


def run_pull(
    *,
    repo_root: Path,
    start_date: str,
    end_date: str,
    tickers: list[str],
    form_types: tuple[str, ...],
    limit_per_ticker: int,
    page_size: int,
    download_text: bool,
    output_path: Path,
    metadata_output_path: Path,
    raw_dir: Path,
    report_output_path: Path,
) -> dict[str, Any]:
    env = _load_env_file(repo_root / ".env")
    api_key = env.get("SEC_API_KEY")
    if not api_key:
        raise RuntimeError("SEC_API_KEY is missing from .env")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_output_path.parent.mkdir(parents=True, exist_ok=True)
    report_output_path.parent.mkdir(parents=True, exist_ok=True)

    normalized_filings: list[PulledFiling] = []
    raw_metadata: list[dict[str, Any]] = []
    raw_downloads = 0
    per_ticker_counts: dict[str, int] = {}

    for ticker in tickers:
        LOGGER.info("Pulling SEC filings for %s", ticker)
        filings = _fetch_filings(api_key, ticker, form_types, start_date, end_date, limit_per_ticker, page_size)
        per_ticker_counts[ticker] = len(filings)
        for filing in filings:
            normalized = _normalize_filing(filing)
            normalized_filings.append(normalized)
            raw_metadata.append(filing)
            if download_text and normalized.metadata.get("link_to_txt"):
                output_file = raw_dir / ticker / f"{normalized.accession_number}.txt"
                try:
                    if _download_raw_text(str(normalized.metadata["link_to_txt"]), output_file):
                        raw_downloads += 1
                except Exception as error:  # pragma: no cover - network path
                    LOGGER.warning("Failed to download raw filing text for %s: %s", normalized.accession_number, error)

    output_payload = {"filings": [filing.to_ingestion_payload() for filing in normalized_filings]}
    output_path.write_text(json.dumps(output_payload, indent=2), encoding="utf-8")
    metadata_output_path.write_text(json.dumps({"filings": raw_metadata}, indent=2), encoding="utf-8")

    report = {
        "startDate": start_date,
        "endDate": end_date,
        "tickers": tickers,
        "formTypes": list(form_types),
        "limitPerTicker": limit_per_ticker,
        "filingsPulled": len(normalized_filings),
        "rawTextDownloads": raw_downloads,
        "perTickerCounts": per_ticker_counts,
        "output": str(output_path),
        "metadataOutput": str(metadata_output_path),
        "rawDir": str(raw_dir),
        "completedAt": datetime.now().isoformat(),
    }
    report_output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)
    repo_root = Path(__file__).resolve().parent.parent
    excluded = DEFAULT_EXCLUDED_TICKERS | {ticker.strip().upper() for ticker in args.exclude_ticker if ticker and ticker.strip()}
    tickers = _resolve_target_tickers(repo_root, args.ticker, excluded)
    form_types = tuple(args.form_type) if args.form_type else DEFAULT_FORMS
    report = run_pull(
        repo_root=repo_root,
        start_date=args.start_date,
        end_date=args.end_date,
        tickers=tickers,
        form_types=form_types,
        limit_per_ticker=args.limit_per_ticker,
        page_size=args.page_size,
        download_text=args.download_text,
        output_path=Path(args.output),
        metadata_output_path=Path(args.metadata_output),
        raw_dir=Path(args.raw_dir),
        report_output_path=Path(args.report_output),
    )
    LOGGER.info("SEC API pull complete. filings=%s raw_downloads=%s", report["filingsPulled"], report["rawTextDownloads"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
