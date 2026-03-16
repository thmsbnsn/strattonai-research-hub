from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable
from uuid import NAMESPACE_URL, uuid5

from .signal_models import SignalConfidenceBand, SignalEvent, SignalOriginType, SignalRelatedCompany, SignalScore, SignalStudyStatistic


SIGNAL_NAMESPACE = uuid5(NAMESPACE_URL, "strattonai/signal-scores")
STANDARD_SIGNAL_HORIZONS = ("1D", "3D", "5D", "10D", "20D")
ZERO = Decimal("0")
ONE_HUNDRED = Decimal("100")

CLASSIFIER_MULTIPLIERS = {
    "High": Decimal("1.00"),
    "Moderate": Decimal("0.93"),
    "Low": Decimal("0.85"),
}

ORIGIN_MULTIPLIERS = {
    "primary": Decimal("1.00"),
    "explicit": Decimal("0.97"),
    "inferred": Decimal("0.88"),
}


def quantize_score(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def build_signal_key(
    event_id: str,
    target_type: str,
    target_ticker: str,
    relationship_type: str | None,
    horizon: str,
) -> str:
    return "||".join(
        [
            event_id,
            target_type,
            target_ticker,
            relationship_type or "ANY",
            horizon,
        ]
    )


def _absolute(value: Decimal) -> Decimal:
    return value.copy_abs()


def _consistency_rate(avg_return: Decimal, median_return: Decimal, win_rate: Decimal) -> Decimal:
    directional_bias = avg_return + median_return
    if directional_bias < ZERO:
        return ONE_HUNDRED - win_rate
    return win_rate


def _recency_multiplier(timestamp: datetime, now: datetime | None = None) -> Decimal:
    reference = now or datetime.now(UTC)
    age_days = max((reference.date() - timestamp.astimezone(UTC).date()).days, 0)

    if age_days <= 2:
        return Decimal("1.00")
    if age_days <= 5:
        return Decimal("0.96")
    if age_days <= 10:
        return Decimal("0.92")
    return Decimal("0.88")


def _build_components(
    event: SignalEvent,
    study: SignalStudyStatistic,
    origin_type: SignalOriginType,
    now: datetime | None = None,
) -> dict[str, Decimal]:
    consistency_rate = _consistency_rate(study.avg_return, study.median_return, study.win_rate)
    return {
        "avg_component": min(_absolute(study.avg_return) * Decimal("12"), Decimal("30")),
        "median_component": min(_absolute(study.median_return) * Decimal("10"), Decimal("20")),
        "consistency_component": max(consistency_rate - Decimal("50"), ZERO) * Decimal("0.6"),
        "sample_component": min(Decimal(study.sample_size), Decimal("20")) * Decimal("1.5"),
        "classifier_multiplier": CLASSIFIER_MULTIPLIERS[event.classifier_confidence],
        "origin_multiplier": ORIGIN_MULTIPLIERS[origin_type],
        "recency_multiplier": _recency_multiplier(event.timestamp, now=now),
        "consistency_rate": consistency_rate,
    }


def determine_confidence_band(
    score: Decimal,
    sample_size: int,
    avg_return: Decimal,
    median_return: Decimal,
    consistency_rate: Decimal,
    classifier_confidence: str,
) -> SignalConfidenceBand:
    if (
        sample_size >= 10
        and consistency_rate >= Decimal("60")
        and _absolute(avg_return) >= Decimal("2.0")
        and _absolute(median_return) >= Decimal("1.0")
        and score >= Decimal("60")
        and classifier_confidence in {"High", "Moderate"}
    ):
        return "High"

    if (
        sample_size >= 5
        and consistency_rate >= Decimal("55")
        and _absolute(avg_return) >= Decimal("1.0")
        and score >= Decimal("35")
    ):
        return "Moderate"

    return "Low"


def compute_signal_score(
    event: SignalEvent,
    study: SignalStudyStatistic,
    target_ticker: str,
    target_type: str,
    relationship_type: str | None,
    origin_type: SignalOriginType,
    now: datetime | None = None,
) -> SignalScore:
    components = _build_components(event, study, origin_type, now=now)
    base_score = (
        components["avg_component"]
        + components["median_component"]
        + components["consistency_component"]
        + components["sample_component"]
    )
    score = min(
        base_score
        * components["classifier_multiplier"]
        * components["origin_multiplier"]
        * components["recency_multiplier"],
        ONE_HUNDRED,
    )
    quantized_score = quantize_score(score)
    confidence_band = determine_confidence_band(
        score=quantized_score,
        sample_size=study.sample_size,
        avg_return=study.avg_return,
        median_return=study.median_return,
        consistency_rate=components["consistency_rate"],
        classifier_confidence=event.classifier_confidence,
    )
    signal_key = build_signal_key(
        event_id=event.id,
        target_type=target_type,
        target_ticker=target_ticker,
        relationship_type=relationship_type,
        horizon=study.horizon,
    )
    direction = "bullish" if (study.avg_return + study.median_return) >= ZERO else "bearish"
    evidence_summary = (
        f"{study.horizon} {target_type} signal is {direction}: "
        f"avg {study.avg_return}% / median {study.median_return}% / "
        f"consistency {components['consistency_rate']}% / sample {study.sample_size}."
    )
    rationale = {
        "event": {
            "ticker": event.ticker,
            "category": event.category,
            "timestamp": event.timestamp.isoformat(),
            "headline": event.headline,
            "sentiment": event.sentiment,
        },
        "classification": event.classifier_rationale,
        "study": {
            "study_key": study.study_key,
            "study_target_type": study.study_target_type,
            "event_category": study.event_category,
            "primary_ticker": study.primary_ticker,
            "related_ticker": study.related_ticker,
            "relationship_type": study.relationship_type,
            "horizon": study.horizon,
            "notes": study.notes,
        },
        "scoring": {
            "direction": direction,
            "confidence_band": confidence_band,
            "components": {key: str(value) for key, value in components.items()},
            "base_score": str(quantize_score(base_score)),
            "final_score": str(quantized_score),
        },
    }

    return SignalScore(
        id=str(uuid5(SIGNAL_NAMESPACE, signal_key)),
        signal_key=signal_key,
        source_study_key=study.study_key,
        event_id=event.id,
        event_category=event.category,
        primary_ticker=event.ticker,
        target_ticker=target_ticker,
        target_type=target_type,  # type: ignore[arg-type]
        relationship_type=relationship_type,
        horizon=study.horizon,
        score=quantized_score,
        confidence_band=confidence_band,
        evidence_summary=evidence_summary,
        rationale=rationale,
        sample_size=study.sample_size,
        avg_return=study.avg_return,
        median_return=study.median_return,
        win_rate=study.win_rate,
        origin_type=origin_type,
    )


def index_studies(studies: Iterable[SignalStudyStatistic]) -> dict[tuple[str, str, str | None, str | None, str | None, str], SignalStudyStatistic]:
    indexed: dict[tuple[str, str, str | None, str | None, str | None, str], SignalStudyStatistic] = {}
    for study in studies:
        indexed[
            (
                study.study_target_type,
                study.event_category,
                study.primary_ticker,
                study.related_ticker,
                study.relationship_type,
                study.horizon,
            )
        ] = study
    return indexed


def resolve_primary_study(
    event: SignalEvent,
    horizon: str,
    indexed_studies: dict[tuple[str, str, str | None, str | None, str | None, str], SignalStudyStatistic],
) -> SignalStudyStatistic | None:
    return indexed_studies.get(("primary", event.category, event.ticker, None, None, horizon)) or indexed_studies.get(
        ("category_summary", event.category, None, None, None, horizon)
    )


def resolve_related_study(
    event: SignalEvent,
    related_company: SignalRelatedCompany,
    horizon: str,
    indexed_studies: dict[tuple[str, str, str | None, str | None, str | None, str], SignalStudyStatistic],
) -> SignalStudyStatistic | None:
    return indexed_studies.get(
        (
            "related",
            event.category,
            None,
            related_company.target_ticker,
            related_company.relationship_type,
            horizon,
        )
    ) or indexed_studies.get(
        (
            "relationship",
            event.category,
            None,
            None,
            related_company.relationship_type,
            horizon,
        )
    )


def score_event_signals(
    event: SignalEvent,
    indexed_studies: dict[tuple[str, str, str | None, str | None, str | None, str], SignalStudyStatistic],
    now: datetime | None = None,
) -> list[SignalScore]:
    signals: list[SignalScore] = []

    for horizon in STANDARD_SIGNAL_HORIZONS:
        primary_study = resolve_primary_study(event, horizon, indexed_studies)
        if primary_study is not None:
            signals.append(
                compute_signal_score(
                    event=event,
                    study=primary_study,
                    target_ticker=event.ticker,
                    target_type="primary",
                    relationship_type=None,
                    origin_type="primary",
                    now=now,
                )
            )

        for related_company in event.related_companies:
            related_study = resolve_related_study(event, related_company, horizon, indexed_studies)
            if related_study is None:
                continue

            signals.append(
                compute_signal_score(
                    event=event,
                    study=related_study,
                    target_ticker=related_company.target_ticker,
                    target_type="related",
                    relationship_type=related_company.relationship_type,
                    origin_type=related_company.origin_type,
                    now=now,
                )
            )

    return signals
