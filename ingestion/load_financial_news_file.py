from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def load_financial_news_file(path: str | Path) -> list[dict[str, Any]]:
    source_path = Path(path)

    if not source_path.exists():
        raise FileNotFoundError(f"Financial news input file not found: {source_path}")

    if source_path.suffix.lower() != ".csv":
        raise ValueError(
            f"Financial news ingestion only supports the canonical CSV source. Received: {source_path.name}"
        )

    with source_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        records = [dict(row) for row in reader]

    if not records:
        raise ValueError(f"Financial news dataset is empty: {source_path}")

    return records
