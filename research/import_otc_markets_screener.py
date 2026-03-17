from __future__ import annotations

import argparse
import csv
import json
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable


LOGGER = logging.getLogger("research.import_otc_markets_screener")


@dataclass(frozen=True, slots=True)
class OtcScreenerRow:
    symbol: str
    security_name: str
    tier: str
    price: float
    change_pct: float
    volume: float
    sec_type: str
    country: str
    state: str | None = None

    def to_universe_candidate(self) -> dict[str, Any]:
        return {
            "ticker": self.symbol,
            "name": self.security_name,
            "exchange": self.tier,
            "lastPrice": round(self.price, 6),
            "avgVolume": round(self.volume, 6),
            "marketCapEst": None,
            "changePct": round(self.change_pct, 8),
            "source": "otc_markets_screener",
        }


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format="%(levelname)s %(message)s")


def _parse_float(value: str | None) -> float:
    if value is None:
        return 0.0
    text = str(value).strip().replace(",", "")
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def load_otc_screener_csv(path: Path) -> list[OtcScreenerRow]:
    rows: list[OtcScreenerRow] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            symbol = str(raw.get("Symbol", "")).strip().upper()
            if not symbol:
                continue
            sec_type = str(raw.get("Sec Type", "")).strip()
            if sec_type and sec_type.lower() != "common stock":
                continue
            rows.append(
                OtcScreenerRow(
                    symbol=symbol,
                    security_name=str(raw.get("Security Name", "")).strip() or symbol,
                    tier=str(raw.get("Tier", "")).strip() or "OTC",
                    price=_parse_float(raw.get("Price")),
                    change_pct=_parse_float(raw.get("Change %")),
                    volume=_parse_float(raw.get("Vol")),
                    sec_type=sec_type or "Common Stock",
                    country=str(raw.get("Country", "")).strip(),
                    state=(str(raw.get("State", "")).strip() or None),
                )
            )
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main(argv: Iterable[str] | None = None) -> int:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Import OTC Markets Stock Screener CSV into a deterministic universe file.")
    parser.add_argument(
        "--input",
        default=None,
        help="Path to OTC Markets Stock Screener export CSV.",
    )
    parser.add_argument(
        "--universe-output",
        default=str(repo_root / "reports" / "otc_markets_universe.json"),
        help="Where to write the normalized OTC universe file.",
    )
    parser.add_argument(
        "--report-output",
        default=str(repo_root / "reports" / "otc_markets_screener_import.json"),
        help="Where to write the import report JSON.",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)

    configure_logging(args.verbose)

    if not args.input:
        raise SystemExit("--input is required (path to Stock_Screener.csv).")

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        LOGGER.error("Input CSV not found: %s", input_path)
        return 1

    rows = load_otc_screener_csv(input_path)
    candidates = [row.to_universe_candidate() for row in rows]
    tickers = sorted({row.symbol for row in rows})
    tiers = sorted({row.tier for row in rows if row.tier})

    universe_payload = {
        "generatedAt": datetime.now(UTC).isoformat(),
        "source": "otc_markets_screener",
        "inputFile": str(input_path),
        "candidates": candidates,
    }
    write_json(Path(args.universe_output), universe_payload)

    report_payload = {
        "generatedAt": universe_payload["generatedAt"],
        "inputFile": str(input_path),
        "rowsRead": len(rows),
        "tickers": tickers,
        "tiers": tiers,
        "universeFile": str(Path(args.universe_output).resolve()),
    }
    write_json(Path(args.report_output), report_payload)

    LOGGER.info("Imported %s OTC rows into %s", len(rows), args.universe_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

