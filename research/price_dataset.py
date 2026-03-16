from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

try:
    from ingestion.load_price_series_file import PriceDatasetInspection, inspect_price_series_file, load_price_series_file
except ImportError:  # pragma: no cover - script execution fallback
    from load_price_series_file import PriceDatasetInspection, inspect_price_series_file, load_price_series_file  # type: ignore

try:
    from .event_study_models import PriceSeries, StudyEvent
except ImportError:  # pragma: no cover - script execution fallback
    from event_study_models import PriceSeries, StudyEvent  # type: ignore


SUPPORTED_PRICE_FORMATS = {
    ".json": "json",
    ".csv": "csv",
    ".parquet": "parquet",
}


@dataclass(frozen=True, slots=True)
class ResolvedPriceDataset:
    path: Path
    format: str
    resolution_reason: str
    used_sample_fallback: bool = False


def detect_price_format(path: str | Path) -> str:
    file_path = Path(path)
    detected = SUPPORTED_PRICE_FORMATS.get(file_path.suffix.lower())
    if detected is None:
        raise ValueError(
            f"Unsupported price dataset format for '{file_path}'. Expected one of: "
            f"{', '.join(sorted(SUPPORTED_PRICE_FORMATS))}."
        )
    return detected


def resolve_price_dataset_path(
    repo_root: Path,
    explicit_path: str | Path | None = None,
    *,
    allow_sample_fallback: bool = True,
) -> ResolvedPriceDataset:
    if explicit_path is not None:
        resolved = _resolve_explicit_path(repo_root, explicit_path)
        return ResolvedPriceDataset(
            path=resolved,
            format=detect_price_format(resolved),
            resolution_reason="explicit_override",
            used_sample_fallback=False,
        )

    for candidate in _iter_default_candidates(repo_root):
        if candidate.path.exists():
            return candidate

    searched = [
        str(path)
        for path in _candidate_paths(repo_root, "data/prices/all_stock_data_extended.parquet")
        + _candidate_paths(repo_root, "data/prices/all_stock_data.parquet")
        + _candidate_paths(repo_root, "data/prices/all_stock_data_extended.csv")
        + _candidate_paths(repo_root, "data/prices/all_stock_data.csv")
    ]
    if allow_sample_fallback:
        searched.append(str(repo_root / "research" / "sample_extended_price_series.json"))

    raise FileNotFoundError(
        "No supported default price dataset was found. Checked: "
        + ", ".join(searched)
    )


def describe_resolution(result: ResolvedPriceDataset) -> str:
    return (
        f"{result.path} ({result.format}, "
        f"reason={result.resolution_reason}, "
        f"sample_fallback={str(result.used_sample_fallback).lower()})"
    )


def load_resolved_price_series(
    repo_root: Path,
    explicit_path: str | Path | None = None,
    *,
    tickers: set[str] | None = None,
    allow_sample_fallback: bool = True,
) -> tuple[list[PriceSeries], ResolvedPriceDataset]:
    resolved = resolve_price_dataset_path(
        repo_root,
        explicit_path,
        allow_sample_fallback=allow_sample_fallback,
    )
    return load_price_series_file(resolved.path, tickers=tickers), resolved


def inspect_resolved_price_dataset(
    repo_root: Path,
    explicit_path: str | Path | None = None,
    *,
    tickers: set[str] | None = None,
    allow_sample_fallback: bool = True,
) -> tuple[PriceDatasetInspection, ResolvedPriceDataset]:
    resolved = resolve_price_dataset_path(
        repo_root,
        explicit_path,
        allow_sample_fallback=allow_sample_fallback,
    )
    return inspect_price_series_file(resolved.path, tickers=tickers), resolved


def collect_study_tickers(events: list[StudyEvent]) -> set[str]:
    tickers = {event.ticker for event in events}
    for event in events:
        for related_company in event.related_companies:
            tickers.add(related_company.target_ticker)
    return tickers


def _resolve_explicit_path(repo_root: Path, explicit_path: str | Path) -> Path:
    raw_path = Path(explicit_path)
    candidates = []

    if raw_path.is_absolute():
        candidates.append(raw_path)
    else:
        candidates.extend(
            [
                raw_path,
                repo_root / raw_path,
                repo_root.parent / raw_path,
            ]
        )

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    raise FileNotFoundError(
        f"Explicit price dataset not found for '{explicit_path}'. "
        f"Checked: {', '.join(str(candidate) for candidate in candidates)}"
    )


def _iter_default_candidates(repo_root: Path) -> tuple[ResolvedPriceDataset, ...]:
    candidates: list[ResolvedPriceDataset] = []
    for candidate in _candidate_paths(repo_root, "data/prices/all_stock_data_extended.parquet"):
        candidates.append(
            ResolvedPriceDataset(
                path=candidate,
                format="parquet",
                resolution_reason="default_extended_parquet",
                used_sample_fallback=False,
            )
        )
    for candidate in _candidate_paths(repo_root, "data/prices/all_stock_data.parquet"):
        candidates.append(
            ResolvedPriceDataset(
                path=candidate,
                format="parquet",
                resolution_reason="default_parquet",
                used_sample_fallback=False,
            )
        )
    for candidate in _candidate_paths(repo_root, "data/prices/all_stock_data_extended.csv"):
        candidates.append(
            ResolvedPriceDataset(
                path=candidate,
                format="csv",
                resolution_reason="default_extended_csv",
                used_sample_fallback=False,
            )
        )
    for candidate in _candidate_paths(repo_root, "data/prices/all_stock_data.csv"):
        candidates.append(
            ResolvedPriceDataset(
                path=candidate,
                format="csv",
                resolution_reason="default_csv",
                used_sample_fallback=False,
            )
        )

    sample_path = repo_root / "research" / "sample_extended_price_series.json"
    candidates.append(
        ResolvedPriceDataset(
            path=sample_path,
            format="json",
            resolution_reason="sample_json_fallback",
            used_sample_fallback=True,
        )
    )
    return tuple(candidates)


def _candidate_paths(repo_root: Path, relative_path: str) -> list[Path]:
    candidates: list[Path] = []
    seen: set[Path] = set()
    for root in (repo_root, repo_root.parent):
        candidate = (root / relative_path).resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        candidates.append(candidate)
    return candidates
