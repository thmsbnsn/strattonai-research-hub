from __future__ import annotations

import argparse
import logging
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from statistics import median
from uuid import NAMESPACE_URL, uuid5

from .compute_forward_returns import compute_close_to_close_forward_return
from .event_study_models import (
    EventStudyAggregate,
    EventStudyComputationResult,
    ForwardReturnObservation,
    PriceSeries,
    STANDARD_HORIZONS,
    StudyEvent,
    StudyTargetType,
)
from .price_dataset import collect_study_tickers, describe_resolution, load_resolved_price_series
from .write_event_studies_to_supabase import EventStudySupabaseWriter


LOGGER = logging.getLogger("research.event_study_engine")
STUDY_NAMESPACE = uuid5(NAMESPACE_URL, "strattonai/event-study-statistics")
HORIZON_LABELS = {1: "1D", 3: "3D", 5: "5D", 10: "10D", 20: "20D"}


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format="%(levelname)s %(message)s")


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Compute deterministic forward-return event studies.")
    parser.add_argument(
        "--price-file",
        default=None,
        help="Optional explicit price dataset path (.parquet, .csv, or .json). Defaults resolve to Parquet first.",
    )
    parser.add_argument(
        "--bootstrap-schema",
        action="store_true",
        help="Apply the event-study statistics migration before computing studies.",
    )
    parser.add_argument(
        "--schema-file",
        default=str(repo_root / "supabase" / "sql" / "006_add_event_study_statistics.sql"),
        help="SQL file to apply when --bootstrap-schema is set.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Compute studies without writing to Supabase.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")
    return parser.parse_args()


def quantize_percent(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def build_price_map(series_list: list[PriceSeries]) -> dict[str, PriceSeries]:
    return {series.ticker: series for series in series_list}


def compute_event_study_observations(
    events: list[StudyEvent],
    price_map: dict[str, PriceSeries],
) -> tuple[list[ForwardReturnObservation], dict[str, int]]:
    observations: list[ForwardReturnObservation] = []
    stats = {"missing_primary_series": 0, "missing_related_series": 0, "missing_horizon": 0}

    for event in events:
        primary_series = price_map.get(event.ticker)
        if primary_series is None:
            stats["missing_primary_series"] += 1
        else:
            for horizon_days in STANDARD_HORIZONS:
                result = compute_close_to_close_forward_return(primary_series, event.timestamp, horizon_days)
                if result is None:
                    stats["missing_horizon"] += 1
                    continue
                forward_return, start_index, end_index = result
                observations.append(
                    ForwardReturnObservation(
                        event_id=event.id,
                        study_target_type="primary",
                        event_category=event.category,
                        horizon=HORIZON_LABELS[horizon_days],
                        forward_return=quantize_percent(forward_return),
                        aligned_trade_date=primary_series.prices[start_index].date,
                        exit_trade_date=primary_series.prices[end_index].date,
                        primary_ticker=event.ticker,
                    )
                )

        for related_company in event.related_companies:
            related_series = price_map.get(related_company.target_ticker)
            if related_series is None:
                stats["missing_related_series"] += 1
                continue

            for horizon_days in STANDARD_HORIZONS:
                result = compute_close_to_close_forward_return(related_series, event.timestamp, horizon_days)
                if result is None:
                    stats["missing_horizon"] += 1
                    continue
                forward_return, start_index, end_index = result
                observations.append(
                    ForwardReturnObservation(
                        event_id=event.id,
                        study_target_type="related",
                        event_category=event.category,
                        horizon=HORIZON_LABELS[horizon_days],
                        forward_return=quantize_percent(forward_return),
                        aligned_trade_date=related_series.prices[start_index].date,
                        exit_trade_date=related_series.prices[end_index].date,
                        primary_ticker=event.ticker,
                        related_ticker=related_company.target_ticker,
                        relationship_type=related_company.relationship_type,
                    )
                )

    return observations, stats


def build_study_key(
    study_target_type: StudyTargetType,
    event_category: str,
    horizon: str,
    primary_ticker: str | None = None,
    related_ticker: str | None = None,
    relationship_type: str | None = None,
) -> str:
    return "||".join(
        [
            study_target_type,
            event_category,
            primary_ticker or "ANY",
            related_ticker or "ANY",
            relationship_type or "ANY",
            horizon,
        ]
    )


def aggregate_observations(observations: list[ForwardReturnObservation]) -> list[EventStudyAggregate]:
    grouped: dict[tuple[StudyTargetType, str, str, str | None, str | None, str | None], list[ForwardReturnObservation]] = defaultdict(list)

    for observation in observations:
        grouped[
            (
                observation.study_target_type,
                observation.event_category,
                observation.horizon,
                observation.primary_ticker,
                observation.related_ticker,
                observation.relationship_type,
            )
        ].append(observation)

        if observation.study_target_type == "primary":
            grouped[("category_summary", observation.event_category, observation.horizon, None, None, None)].append(
                observation
            )

        if observation.study_target_type == "related" and observation.relationship_type is not None:
            grouped[("relationship", observation.event_category, observation.horizon, None, None, observation.relationship_type)].append(
                observation
            )

    aggregates: list[EventStudyAggregate] = []
    for (study_target_type, event_category, horizon, primary_ticker, related_ticker, relationship_type), group in sorted(grouped.items()):
        returns = [float(observation.forward_return) for observation in group]
        if not returns:
            continue

        study_key = build_study_key(
            study_target_type=study_target_type,
            event_category=event_category,
            primary_ticker=primary_ticker,
            related_ticker=related_ticker,
            relationship_type=relationship_type,
            horizon=horizon,
        )
        avg_return = quantize_percent(Decimal(str(sum(returns) / len(returns))))
        median_return = quantize_percent(Decimal(str(median(returns))))
        win_rate = quantize_percent(Decimal(str((sum(1 for value in returns if value > 0) / len(returns)) * 100)))

        notes_map = {
            "category_summary": "Primary ticker forward-return summary by event category.",
            "primary": "Primary ticker forward-return summary for a single ticker within an event category.",
            "relationship": "Related ticker forward-return summary aggregated by relationship type.",
            "related": "Related ticker forward-return summary for a single ticker within an event category.",
        }
        metadata = {
            "observation_count": len(group),
            "event_ids": sorted({observation.event_id for observation in group}),
            "aligned_trade_dates": sorted({observation.aligned_trade_date.isoformat() for observation in group}),
            "exit_trade_dates": sorted({observation.exit_trade_date.isoformat() for observation in group}),
        }

        aggregates.append(
            EventStudyAggregate(
                id=str(uuid5(STUDY_NAMESPACE, study_key)),
                study_key=study_key,
                study_target_type=study_target_type,
                event_category=event_category,
                horizon=horizon,
                primary_ticker=primary_ticker,
                related_ticker=related_ticker,
                relationship_type=relationship_type,
                sample_size=len(group),
                avg_return=avg_return,
                median_return=median_return,
                win_rate=win_rate,
                notes=notes_map[study_target_type],
                metadata=metadata,
            )
        )

    return aggregates


def run_event_study_computation(events: list[StudyEvent], price_map: dict[str, PriceSeries]) -> EventStudyComputationResult:
    observations, _stats = compute_event_study_observations(events, price_map)
    aggregates = aggregate_observations(observations)
    return EventStudyComputationResult(observations=tuple(observations), aggregates=tuple(aggregates))


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)

    repo_root = Path(__file__).resolve().parent.parent
    writer = EventStudySupabaseWriter(repo_root)

    if args.bootstrap_schema:
        writer.apply_sql_file(Path(args.schema_file))

    events = writer.load_study_events()
    tickers = collect_study_tickers(events)
    price_series, resolved_price_dataset = load_resolved_price_series(repo_root, args.price_file, tickers=tickers)
    LOGGER.info("Using price dataset %s", describe_resolution(resolved_price_dataset))
    price_map = build_price_map(price_series)
    observations, stats = compute_event_study_observations(events, price_map)
    aggregates = aggregate_observations(observations)

    LOGGER.info(
        "Computed %s observation(s) across %s aggregate study row(s). Missing primary series=%s missing related series=%s missing horizon=%s",
        len(observations),
        len(aggregates),
        stats["missing_primary_series"],
        stats["missing_related_series"],
        stats["missing_horizon"],
    )

    if args.dry_run:
        LOGGER.info("Dry run complete. No database writes were performed.")
        return 0

    detail_count = writer.upsert_event_study_aggregates(aggregates)
    summary_count = writer.upsert_ui_summary_rows(aggregates)
    live_count = writer.count_matching_studies(aggregates)
    LOGGER.info(
        "Upserted %s detailed study row(s), %s UI summary row(s), verified %s matching detailed row(s).",
        detail_count,
        summary_count,
        live_count,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
