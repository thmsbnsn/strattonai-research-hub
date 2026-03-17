"""Report deterministic Partnership-category evidence gaps and priorities."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .trading_repository import TradingRepository


@dataclass(frozen=True, slots=True)
class PartnershipPriority:
    ticker: str
    current_sample_size: int
    event_count: int
    related_event_count: int
    graph_strength: float
    priority_score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Partnership evidence-gap priorities.")
    parser.add_argument("--min-sample", type=int, default=5)
    parser.add_argument("--top-n", type=int, default=20)
    return parser.parse_args()


def _query_partnership_priorities(repository: TradingRepository, min_sample: int, top_n: int) -> list[PartnershipPriority]:
    with repository.connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                select ticker, timestamp::date
                from public.events
                where category = 'Partnership'
                order by timestamp desc
                """
            )
            event_rows = cursor.fetchall()
            cursor.execute(
                """
                select primary_ticker, coalesce(sum(sample_size), 0)
                from public.event_study_statistics
                where event_category = 'Partnership'
                  and study_target_type = 'primary'
                group by primary_ticker
                """
            )
            sample_rows = cursor.fetchall()
            cursor.execute(
                """
                select coalesce(source_ticker, primary_ticker), count(*)
                from public.related_companies rc
                left join public.events e on e.id = rc.event_id
                group by coalesce(source_ticker, primary_ticker)
                """
            )
            related_rows = cursor.fetchall()
            cursor.execute(
                """
                select source_ticker, target_ticker, strength
                from public.company_relationship_graph
                """
            )
            graph_rows = cursor.fetchall()

    event_counts = Counter(str(row[0]).upper() for row in event_rows if row[0])
    sample_sizes = {str(row[0]).upper(): int(row[1] or 0) for row in sample_rows if row[0]}
    related_counts = {str(row[0]).upper(): int(row[1] or 0) for row in related_rows if row[0]}
    graph_strengths: dict[str, float] = defaultdict(float)
    for source_ticker, target_ticker, strength in graph_rows:
        if float(strength or 0) <= 0.7:
            continue
        graph_strengths[str(source_ticker).upper()] = max(graph_strengths[str(source_ticker).upper()], float(strength))
        graph_strengths[str(target_ticker).upper()] = max(graph_strengths[str(target_ticker).upper()], float(strength))

    priorities: list[PartnershipPriority] = []
    for ticker, event_count in event_counts.items():
        sample_size = sample_sizes.get(ticker, 0)
        if sample_size >= min_sample:
            continue
        graph_strength = graph_strengths.get(ticker, 0.0)
        related_event_count = related_counts.get(ticker, 0)
        priority_score = round((graph_strength * 100.0) + (related_event_count * 2.0) + max(min_sample - sample_size, 0), 6)
        priorities.append(
            PartnershipPriority(
                ticker=ticker,
                current_sample_size=sample_size,
                event_count=event_count,
                related_event_count=related_event_count,
                graph_strength=graph_strength,
                priority_score=priority_score,
            )
        )

    priorities.sort(key=lambda item: (-item.priority_score, item.current_sample_size, item.ticker))
    return priorities[:top_n]


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    repository = TradingRepository(repo_root)
    priorities = _query_partnership_priorities(repository, args.min_sample, args.top_n)
    report_dir = repo_root / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "partnership_backfill_priorities.json"
    md_path = report_dir / "partnership_backfill_priorities.md"
    payload = {"priorities": [priority.to_dict() for priority in priorities]}
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = [
        "# Partnership Backfill Priorities",
        "",
        "| Ticker | Sample Size | Partnership Events | Related Event Count | Graph Strength | Priority Score |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for priority in priorities:
        lines.append(
            f"| {priority.ticker} | {priority.current_sample_size} | {priority.event_count} | {priority.related_event_count} | {priority.graph_strength:.2f} | {priority.priority_score:.2f} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
