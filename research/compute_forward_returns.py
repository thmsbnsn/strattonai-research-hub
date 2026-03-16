from __future__ import annotations

from bisect import bisect_left
from datetime import datetime
from decimal import Decimal

from .event_study_models import PriceSeries


def align_event_to_trading_index(series: PriceSeries, event_timestamp: datetime) -> int | None:
    trading_dates = [point.date for point in series.prices]
    event_date = event_timestamp.date()
    index = bisect_left(trading_dates, event_date)
    if index >= len(trading_dates):
        return None
    return index


def compute_close_to_close_forward_return(
    series: PriceSeries,
    event_timestamp: datetime,
    horizon_days: int,
) -> tuple[Decimal, int, int] | None:
    start_index = align_event_to_trading_index(series, event_timestamp)
    if start_index is None:
        return None

    end_index = start_index + horizon_days
    if end_index >= len(series.prices):
        return None

    start_close = series.prices[start_index].close
    end_close = series.prices[end_index].close
    if start_close == Decimal("0"):
        return None

    forward_return = ((end_close / start_close) - Decimal("1")) * Decimal("100")
    return forward_return, start_index, end_index
