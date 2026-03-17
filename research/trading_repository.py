"""Shared deterministic data-access helpers for trader-side research modules."""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

from psycopg.types.json import Jsonb

try:
    from ingestion.write_to_supabase import SupabaseWriter
except ImportError:  # pragma: no cover - script execution fallback
    from write_to_supabase import SupabaseWriter  # type: ignore


@dataclass(frozen=True, slots=True)
class PriceBar:
    ticker: str
    trade_date: date
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    close: Decimal
    volume: int | None
    dividends: Decimal | None = None
    stock_splits: Decimal | None = None


@dataclass(frozen=True, slots=True)
class CompanyProfileRecord:
    ticker: str
    name: str
    sector: str | None
    industry: str | None
    market_cap_text: str | None
    market_cap_value: float | None


@dataclass(frozen=True, slots=True)
class RelationshipRecord:
    source_ticker: str
    source_name: str | None
    target_ticker: str
    target_name: str | None
    relationship_type: str
    strength: float


@dataclass(frozen=True, slots=True)
class EventRecord:
    id: str
    ticker: str
    category: str
    headline: str
    sentiment: str | None
    timestamp: datetime
    metadata: dict[str, Any] | None


@dataclass(frozen=True, slots=True)
class StudySliceRecord:
    study_key: str
    study_target_type: str
    event_category: str
    primary_ticker: str | None
    related_ticker: str | None
    relationship_type: str | None
    horizon: str
    avg_return: float
    median_return: float
    win_rate: float
    sample_size: int
    notes: str | None
    metadata: dict[str, Any]


@dataclass(frozen=True, slots=True)
class PaperTradeRecord:
    id: str
    ticker: str
    direction: str
    signal: str
    entry_price: Decimal
    current_price: Decimal | None
    entry_date: date
    quantity: Decimal
    status: str
    mode: str | None = None
    metadata: dict[str, Any] | None = None
    alpaca_order_id: str | None = None
    exit_price: Decimal | None = None
    exit_date: date | None = None
    realized_pnl: Decimal | None = None
    universe: str | None = None


def _to_date(value: Any) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(str(value))


def _to_decimal(value: Any) -> Decimal | None:
    if value in {None, ""}:
        return None
    return Decimal(str(value))


def _to_int(value: Any) -> int | None:
    if value in {None, ""}:
        return None
    return int(float(value))


def parse_market_cap(value: str | None) -> float | None:
    if not value:
        return None
    cleaned = value.strip().replace("$", "").replace(",", "").upper()
    if not cleaned:
        return None

    multiplier = 1.0
    if cleaned.endswith("T"):
        multiplier = 1_000_000_000_000.0
        cleaned = cleaned[:-1]
    elif cleaned.endswith("B"):
        multiplier = 1_000_000_000.0
        cleaned = cleaned[:-1]
    elif cleaned.endswith("M"):
        multiplier = 1_000_000.0
        cleaned = cleaned[:-1]
    elif cleaned.endswith("K"):
        multiplier = 1_000.0
        cleaned = cleaned[:-1]

    try:
        return float(cleaned) * multiplier
    except ValueError:
        return None


class TradingRepository(SupabaseWriter):
    def __init__(self, repo_root: Path):
        super().__init__(repo_root)

    def load_signal_scores(
        self,
        *,
        signal_keys: Iterable[str] | None = None,
        ticker: str | None = None,
        confidence_bands: Iterable[str] | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []

        signal_key_list = sorted({key for key in (signal_keys or []) if key})
        if signal_key_list:
            clauses.append("signal_key = any(%s)")
            params.append(signal_key_list)

        if ticker:
            clauses.append("(primary_ticker = %s or target_ticker = %s)")
            params.extend([ticker.upper(), ticker.upper()])

        confidence_list = sorted({band for band in (confidence_bands or []) if band})
        if confidence_list:
            clauses.append("confidence_band = any(%s)")
            params.append(confidence_list)

        where_sql = f"where {' and '.join(clauses)}" if clauses else ""
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    select
                      id::text,
                      signal_key,
                      source_study_key,
                      event_id::text,
                      event_category,
                      primary_ticker,
                      target_ticker,
                      target_type,
                      relationship_type,
                      horizon,
                      score,
                      confidence_band,
                      evidence_summary,
                      rationale,
                      metadata,
                      sample_size,
                      avg_return,
                      median_return,
                      win_rate,
                      origin_type
                    from public.signal_scores
                    {where_sql}
                    order by score desc, horizon asc, target_ticker asc
                    """,
                    params,
                )
                rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "signal_key": row[1],
                "source_study_key": row[2],
                "event_id": row[3],
                "event_category": row[4],
                "primary_ticker": row[5],
                "target_ticker": row[6],
                "target_type": row[7],
                "relationship_type": row[8],
                "horizon": row[9],
                "score": float(row[10] or 0),
                "confidence_band": row[11],
                "evidence_summary": row[12],
                "rationale": row[13] or {},
                "metadata": row[14] or {},
                "sample_size": int(row[15] or 0),
                "avg_return": float(row[16] or 0),
                "median_return": float(row[17] or 0),
                "win_rate": float(row[18] or 0),
                "origin_type": row[19],
            }
            for row in rows
        ]

    def load_daily_prices(
        self,
        tickers: Iterable[str],
        *,
        limit_per_ticker: int | None = None,
        min_date: date | None = None,
    ) -> dict[str, list[PriceBar]]:
        normalized = sorted({ticker.upper() for ticker in tickers if ticker})
        if not normalized:
            return {}

        where_clauses = ["ticker = any(%s)"]
        params: list[Any] = [normalized]
        if min_date is not None:
            where_clauses.append("trade_date >= %s")
            params.append(min_date)

        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    select
                      ticker,
                      trade_date,
                      open,
                      high,
                      low,
                      close,
                      volume,
                      dividends,
                      stock_splits
                    from public.daily_prices
                    where {' and '.join(where_clauses)}
                    order by ticker asc, trade_date asc
                    """,
                    params,
                )
                rows = cursor.fetchall()

        grouped: dict[str, list[PriceBar]] = {ticker: [] for ticker in normalized}
        for row in rows:
            grouped[row[0]].append(
                PriceBar(
                    ticker=row[0],
                    trade_date=_to_date(row[1]),
                    open=_to_decimal(row[2]),
                    high=_to_decimal(row[3]),
                    low=_to_decimal(row[4]),
                    close=_to_decimal(row[5]) or Decimal("0"),
                    volume=_to_int(row[6]),
                    dividends=_to_decimal(row[7]),
                    stock_splits=_to_decimal(row[8]),
                )
            )

        if limit_per_ticker is not None:
            return {ticker: bars[-limit_per_ticker:] for ticker, bars in grouped.items()}
        return grouped

    def latest_daily_price(self, ticker: str) -> PriceBar | None:
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select ticker, trade_date, open, high, low, close, volume, dividends, stock_splits
                    from public.daily_prices
                    where ticker = %s
                    order by trade_date desc
                    limit 1
                    """,
                    (ticker.upper(),),
                )
                row = cursor.fetchone()
        if row is None:
            return None
        return PriceBar(
            ticker=row[0],
            trade_date=_to_date(row[1]),
            open=_to_decimal(row[2]),
            high=_to_decimal(row[3]),
            low=_to_decimal(row[4]),
            close=_to_decimal(row[5]) or Decimal("0"),
            volume=_to_int(row[6]),
            dividends=_to_decimal(row[7]),
            stock_splits=_to_decimal(row[8]),
        )

    def count_daily_price_rows(self, ticker: str) -> int:
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("select count(*) from public.daily_prices where ticker = %s", (ticker.upper(),))
                return int(cursor.fetchone()[0] or 0)

    def load_company_profiles(self, tickers: Iterable[str]) -> dict[str, CompanyProfileRecord]:
        normalized = sorted({ticker.upper() for ticker in tickers if ticker})
        if not normalized:
            return {}

        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select ticker, name, sector, industry, market_cap
                    from public.company_profiles
                    where ticker = any(%s)
                    """,
                    (normalized,),
                )
                rows = cursor.fetchall()

        return {
            row[0]: CompanyProfileRecord(
                ticker=row[0],
                name=row[1],
                sector=row[2],
                industry=row[3],
                market_cap_text=row[4],
                market_cap_value=parse_market_cap(row[4]),
            )
            for row in rows
        }

    def load_relationships(self, ticker: str, *, limit: int = 12) -> list[RelationshipRecord]:
        normalized = ticker.upper()
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select
                      source_ticker,
                      source_name,
                      target_ticker,
                      target_name,
                      relationship_type,
                      strength
                    from public.company_relationship_graph
                    where source_ticker = %s or target_ticker = %s
                    order by strength desc, relationship_type asc, source_ticker asc, target_ticker asc
                    limit %s
                    """,
                    (normalized, normalized, limit),
                )
                rows = cursor.fetchall()

        return [
            RelationshipRecord(
                source_ticker=row[0],
                source_name=row[1],
                target_ticker=row[2],
                target_name=row[3],
                relationship_type=row[4],
                strength=float(row[5] or 0.0),
            )
            for row in rows
        ]

    def load_recent_events(self, ticker: str, *, limit: int = 8) -> list[EventRecord]:
        normalized = ticker.upper()
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select
                      id::text,
                      ticker,
                      category,
                      headline,
                      sentiment,
                      timestamp,
                      metadata
                    from public.events
                    where ticker = %s
                    order by timestamp desc
                    limit %s
                    """,
                    (normalized, limit),
                )
                rows = cursor.fetchall()

        return [
            EventRecord(
                id=row[0],
                ticker=row[1],
                category=row[2],
                headline=row[3],
                sentiment=row[4],
                timestamp=row[5],
                metadata=row[6] or {},
            )
            for row in rows
        ]

    def load_study_slices(self, ticker: str, *, limit: int = 24) -> list[StudySliceRecord]:
        normalized = ticker.upper()
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select
                      study_key,
                      study_target_type,
                      event_category,
                      primary_ticker,
                      related_ticker,
                      relationship_type,
                      horizon,
                      avg_return,
                      median_return,
                      win_rate,
                      sample_size,
                      notes,
                      metadata
                    from public.event_study_statistics
                    where primary_ticker = %s or related_ticker = %s
                    order by sample_size desc, abs(avg_return) desc, horizon asc
                    limit %s
                    """,
                    (normalized, normalized, limit),
                )
                rows = cursor.fetchall()

        return [
            StudySliceRecord(
                study_key=row[0],
                study_target_type=row[1],
                event_category=row[2],
                primary_ticker=row[3],
                related_ticker=row[4],
                relationship_type=row[5],
                horizon=row[6],
                avg_return=float(row[7] or 0.0),
                median_return=float(row[8] or 0.0),
                win_rate=float(row[9] or 0.0),
                sample_size=int(row[10] or 0),
                notes=row[11],
                metadata=row[12] or {},
            )
            for row in rows
        ]

    def load_paper_trades(
        self,
        *,
        statuses: Iterable[str] | None = None,
        universe: str | None = None,
    ) -> list[PaperTradeRecord]:
        clauses: list[str] = []
        params: list[Any] = []
        status_values = sorted({status for status in (statuses or []) if status})
        if status_values:
            clauses.append("lower(status) = any(%s)")
            params.append([status.lower() for status in status_values])
        if universe:
            clauses.append("coalesce(universe, 'main') = %s")
            params.append(universe)

        where_sql = f"where {' and '.join(clauses)}" if clauses else ""
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    select
                      id::text,
                      ticker,
                      direction,
                      signal,
                      entry_price,
                      current_price,
                      entry_date,
                      quantity,
                      status,
                      mode,
                      metadata,
                      alpaca_order_id,
                      exit_price,
                      exit_date,
                      realized_pnl,
                      universe
                    from public.paper_trades
                    {where_sql}
                    order by entry_date asc, created_at asc
                    """,
                    params,
                )
                rows = cursor.fetchall()

        return [
            PaperTradeRecord(
                id=row[0],
                ticker=row[1],
                direction=row[2],
                signal=row[3],
                entry_price=_to_decimal(row[4]) or Decimal("0"),
                current_price=_to_decimal(row[5]),
                entry_date=_to_date(row[6]),
                quantity=_to_decimal(row[7]) or Decimal("0"),
                status=str(row[8]),
                mode=row[9],
                metadata=row[10] or {},
                alpaca_order_id=row[11],
                exit_price=_to_decimal(row[12]),
                exit_date=_to_date(row[13]) if row[13] else None,
                realized_pnl=_to_decimal(row[14]),
                universe=row[15],
            )
            for row in rows
        ]

    def upsert_paper_trade(self, trade: dict[str, Any]) -> None:
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into public.paper_trades (
                      id,
                      ticker,
                      direction,
                      signal,
                      entry_price,
                      current_price,
                      entry_date,
                      quantity,
                      status,
                      mode,
                      metadata,
                      alpaca_order_id,
                      exit_price,
                      exit_date,
                      realized_pnl,
                      universe
                    )
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    on conflict (id) do update
                    set
                      ticker = excluded.ticker,
                      direction = excluded.direction,
                      signal = excluded.signal,
                      entry_price = excluded.entry_price,
                      current_price = excluded.current_price,
                      entry_date = excluded.entry_date,
                      quantity = excluded.quantity,
                      status = excluded.status,
                      mode = excluded.mode,
                      metadata = excluded.metadata,
                      alpaca_order_id = excluded.alpaca_order_id,
                      exit_price = excluded.exit_price,
                      exit_date = excluded.exit_date,
                      realized_pnl = excluded.realized_pnl,
                      universe = excluded.universe,
                      updated_at = timezone('utc', now())
                    """,
                    (
                        trade["id"],
                        trade["ticker"],
                        trade["direction"],
                        trade["signal"],
                        trade["entry_price"],
                        trade["current_price"],
                        trade["entry_date"],
                        trade["quantity"],
                        trade["status"],
                        trade.get("mode", "simulated"),
                        Jsonb(trade.get("metadata", {})),
                        trade.get("alpaca_order_id"),
                        trade.get("exit_price"),
                        trade.get("exit_date"),
                        trade.get("realized_pnl"),
                        trade.get("universe", "main"),
                    ),
                )
            connection.commit()

    def upsert_portfolio_allocations(
        self,
        *,
        run_id: str,
        method: str,
        allocations: dict[str, float],
        capital_total: float,
        signal_keys: dict[str, str | None],
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        with self.connect() as connection:
            with connection.cursor() as cursor:
                for ticker, allocation in sorted(allocations.items()):
                    weight = float(allocation) / float(capital_total or 1)
                    row_id = f"{run_id}:{ticker}"
                    cursor.execute(
                        """
                        insert into public.portfolio_allocations (
                          id,
                          run_id,
                          method,
                          ticker,
                          allocation_dollars,
                          weight,
                          signal_key,
                          capital_total
                        )
                        values (%s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s)
                        on conflict (id) do update
                        set
                          run_id = excluded.run_id,
                          method = excluded.method,
                          ticker = excluded.ticker,
                          allocation_dollars = excluded.allocation_dollars,
                          weight = excluded.weight,
                          signal_key = excluded.signal_key,
                          capital_total = excluded.capital_total
                        """,
                        (
                            _uuid_from_text(row_id),
                            run_id,
                            method,
                            ticker,
                            allocation,
                            weight,
                            signal_keys.get(ticker),
                            capital_total,
                        ),
                    )
                    rows.append(
                        {
                            "runId": run_id,
                            "method": method,
                            "ticker": ticker,
                            "allocationDollars": float(allocation),
                            "weight": weight,
                            "signalKey": signal_keys.get(ticker),
                            "capitalTotal": capital_total,
                        }
                    )
            connection.commit()
        return rows

    def upsert_market_regime(self, payload: dict[str, Any]) -> None:
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into public.market_regimes (
                      as_of_date,
                      regime_label,
                      spy_price,
                      sma_200,
                      sma_50,
                      vol_20d,
                      drawdown_from_high
                    )
                    values (%s, %s, %s, %s, %s, %s, %s)
                    on conflict (as_of_date) do update
                    set
                      regime_label = excluded.regime_label,
                      spy_price = excluded.spy_price,
                      sma_200 = excluded.sma_200,
                      sma_50 = excluded.sma_50,
                      vol_20d = excluded.vol_20d,
                      drawdown_from_high = excluded.drawdown_from_high
                    """,
                    (
                        payload["as_of_date"],
                        payload["regime_label"],
                        payload["spy_price"],
                        payload["sma_200"],
                        payload["sma_50"],
                        payload["vol_20d"],
                        payload["drawdown_from_high"],
                    ),
                )
            connection.commit()

    def distinct_event_tickers(self) -> list[str]:
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select distinct ticker
                    from public.events
                    where ticker is not null and ticker <> ''
                    order by ticker asc
                    """
                )
                return [row[0] for row in cursor.fetchall()]


def _uuid_from_text(value: str) -> str:
    from uuid import NAMESPACE_URL, uuid5

    return str(uuid5(NAMESPACE_URL, value))


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect basic trading-side repository state.")
    parser.add_argument("--ticker", default="NVDA")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    repository = TradingRepository(repo_root)
    latest = repository.latest_daily_price(args.ticker.upper())
    payload = {
        "ticker": args.ticker.upper(),
        "latestClose": float(latest.close) if latest else None,
        "latestTradeDate": latest.trade_date.isoformat() if latest else None,
        "dailyPriceRows": repository.count_daily_price_rows(args.ticker.upper()),
    }
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
