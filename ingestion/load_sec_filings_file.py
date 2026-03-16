from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_sec_filings_file(path: str | Path) -> list[dict[str, Any]]:
    source_path = Path(path)

    if not source_path.exists():
        raise FileNotFoundError(f"Input file not found: {source_path}")

    payload = json.loads(source_path.read_text(encoding="utf-8"))

    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict) and isinstance(payload.get("filings"), list):
        records = payload["filings"]
    else:
        raise ValueError("Expected a JSON list or an object with a 'filings' array.")

    if not all(isinstance(record, dict) for record in records):
        raise ValueError("Every SEC filing record must be a JSON object.")

    return records
