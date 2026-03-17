from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import threading
from dataclasses import asdict, dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from .local_ai_config import active_retrieval_mode, load_local_ai_config, semantic_runtime_ready
from .local_ai_context import (
    LocalAIContextRepository,
    build_context_citations,
    build_context_prompt,
    build_deterministic_fallback_answer,
    build_grounding_notes,
)
from .trading_repository import TradingRepository
from .ollama_client import OllamaClient
from .alpaca_client import get_account, get_orders, get_positions, load_alpaca_config
from .health_check import run_health_check
from .market_regime import get_current_regime
from .order_preview import build_order_preview
from .penny_stock_signals import build_penny_stock_candidates
from .portfolio_constructor import allocate_and_simulate, construct_portfolio
from .portfolio_metrics import compute_portfolio_metrics
from .risk_engine import assess_portfolio_risk
from .semantic_retrieval import SemanticRetriever
from supabase.scripts.apply_and_verify_migrations import verify_expected_artifacts
from .trade_simulator import simulate_trade
from .trading_loop import run_trading_loop
from .transaction_costs import compute_round_trip_cost


LOGGER = logging.getLogger("research.local_ai_gateway")


@dataclass
class BackgroundJob:
    job_id: str
    status: str = "running"
    result: dict[str, Any] | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"job_id": self.job_id, "status": self.status, "result": self.result, "error": self.error}


def build_system_prompt(*, grounding_prompt: str, trading_mode: str) -> str:
    return (
        "You are the StrattonAI local research assistant.\n"
        "Base your answer only on the structured research context provided below.\n"
        "Do not fabricate facts, prices, catalysts, or sample sizes.\n"
        "When evidence is weak or missing, say so plainly.\n"
        "Do not present anything as trade execution advice. Treat paper and live modes as research context only.\n"
        f"Current trading mode: {trading_mode}.\n\n"
        "Structured research context:\n"
        f"{grounding_prompt}"
    )


def success_response(data: Any) -> dict[str, Any]:
    return {"success": True, "data": data, "error": None}


def error_response(message: str, data: Any = None) -> dict[str, Any]:
    return {"success": False, "data": data, "error": message}


def _summarize_thesis(ticker: str, profile: dict[str, Any], signals: list[dict[str, Any]], events: list[dict[str, Any]]) -> str:
    if not signals:
        return f"{ticker} currently has no scored signal edge. Treat it as watchlist-only until the event-study base deepens."

    best_signal = signals[0]
    company_name = profile.get("name") or ticker
    direction = "constructive" if float(best_signal.get("avg_return", 0.0) or 0.0) >= 0 else "defensive"
    catalyst = best_signal.get("event_category") or "event-driven"
    event_context = events[0]["category"] if events else catalyst
    return (
        f"{company_name} is showing a {direction} deterministic setup. "
        f"The strongest current edge is {catalyst} on a {best_signal.get('horizon', '5D')} horizon "
        f"with score {float(best_signal.get('score', 0.0) or 0.0):.1f}, supported by {event_context} context."
    )


def _build_risk_flags(
    *,
    ticker: str,
    latest_price_rows: int,
    signals: list[dict[str, Any]],
    studies: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
) -> list[str]:
    flags: list[str] = []
    if latest_price_rows < 60:
        flags.append(f"{ticker} has thin daily price coverage.")
    if not signals:
        flags.append("No active scored signals are available.")
    if signals and all((signal.get("confidence_band") or "Low") == "Low" for signal in signals[:3]):
        flags.append("Current signal stack is low-confidence heavy.")
    if studies and max(int(study.get("sample_size", 0) or 0) for study in studies[:6]) < 10:
        flags.append("Event-study evidence depth is still thin for the top slices.")
    if relationships and max(float(edge.get("strength", 0.0) or 0.0) for edge in relationships[:6]) < 0.5:
        flags.append("Relationship graph support is weak for this name.")
    return flags


def _build_live_readiness(repo_root: Path, ticker: str, signals: list[dict[str, Any]], studies: list[dict[str, Any]]) -> dict[str, Any]:
    migration_status = verify_expected_artifacts(repo_root)[0]
    config = load_alpaca_config(repo_root)
    repository = TradingRepository(repo_root)
    paper_trades = repository.load_paper_trades(statuses=["simulated", "open", "Simulated", "Open"])
    paper_trade_validated = any(trade.ticker == ticker for trade in paper_trades)

    account_status = "offline"
    broker_verified = False
    try:
        account = get_account(repo_root=repo_root)
        account_status = str(account.get("status") or account.get("account_status") or "unknown")
        broker_verified = bool(account_status and account_status.upper() in {"ACTIVE", "ACCOUNT_UPDATED", "APPROVAL_PENDING"})
    except Exception:
        broker_verified = False

    signal_depth = max((int(signal.get("sample_size", 0) or 0) for signal in signals[:5]), default=0)
    study_depth = max((int(study.get("sample_size", 0) or 0) for study in studies[:8]), default=0)
    risk_flags_assessed = bool(signals or studies)
    hard_blockers: list[str] = []
    if not config.live_confirmed or config.mode != "live":
        hard_blockers.append("Live mode is not explicitly confirmed in .env.")
    if not all(migration_status.values()):
        hard_blockers.append("Required Supabase trader migrations are not fully verified.")
    if not broker_verified:
        hard_blockers.append("Broker connection is not verified.")
    if signal_depth < 10 and study_depth < 10:
        hard_blockers.append("Evidence depth is too thin for live deployment.")

    return {
        "mode": config.mode,
        "liveConfirmed": config.live_confirmed,
        "accountStatus": account_status,
        "brokerVerified": broker_verified,
        "hardBlockers": hard_blockers,
        "items": [
            {"key": "signals_scored", "label": "Research signals scored", "done": bool(signals)},
            {"key": "study_evidence_reviewed", "label": "Event study evidence reviewed", "done": study_depth >= 10},
            {"key": "risk_flags_assessed", "label": "Risk flags assessed", "done": risk_flags_assessed},
            {"key": "paper_trade_validated", "label": "Paper trade validated", "done": paper_trade_validated},
            {"key": "broker_verified", "label": "Broker connection verified", "done": broker_verified},
        ],
    }


def build_company_briefing_payload(repo_root: Path, ticker: str, trading_mode: str) -> dict[str, Any]:
    normalized_ticker = ticker.strip().upper()
    repository = TradingRepository(repo_root)
    profile_record = repository.load_company_profiles([normalized_ticker]).get(normalized_ticker)
    price_rows = repository.count_daily_price_rows(normalized_ticker)
    latest_price = repository.latest_daily_price(normalized_ticker)
    relationships = repository.load_relationships(normalized_ticker, limit=8)
    events = repository.load_recent_events(normalized_ticker, limit=6)
    studies = repository.load_study_slices(normalized_ticker, limit=18)
    signals = repository.load_signal_scores(ticker=normalized_ticker)[:6]

    profile = {
        "ticker": normalized_ticker,
        "name": profile_record.name if profile_record else normalized_ticker,
        "sector": profile_record.sector if profile_record else None,
        "industry": profile_record.industry if profile_record else None,
        "marketCap": profile_record.market_cap_text if profile_record else None,
        "marketCapValue": profile_record.market_cap_value if profile_record else None,
    }
    relationship_rows = [
        {
            "sourceTicker": edge.source_ticker,
            "sourceName": edge.source_name,
            "targetTicker": edge.target_ticker,
            "targetName": edge.target_name,
            "relationshipType": edge.relationship_type,
            "strength": edge.strength,
            "counterpartyTicker": edge.target_ticker if edge.source_ticker == normalized_ticker else edge.source_ticker,
            "counterpartyName": edge.target_name if edge.source_ticker == normalized_ticker else edge.source_name,
        }
        for edge in relationships
    ]
    event_rows = [
        {
            "id": event.id,
            "ticker": event.ticker,
            "category": event.category,
            "headline": event.headline,
            "sentiment": event.sentiment or "neutral",
            "timestamp": event.timestamp.isoformat(),
        }
        for event in events
    ]
    study_rows = [
        {
            "studyKey": study.study_key,
            "studyTargetType": study.study_target_type,
            "eventCategory": study.event_category,
            "primaryTicker": study.primary_ticker,
            "relatedTicker": study.related_ticker,
            "relationshipType": study.relationship_type,
            "horizon": study.horizon,
            "avgReturn": study.avg_return,
            "medianReturn": study.median_return,
            "winRate": study.win_rate,
            "sampleSize": study.sample_size,
            "notes": study.notes,
            "metadata": study.metadata,
        }
        for study in studies
    ]
    signal_rows = [
        {
            "id": signal["id"],
            "signalKey": signal["signal_key"],
            "eventCategory": signal["event_category"],
            "primaryTicker": signal["primary_ticker"],
            "targetTicker": signal["target_ticker"],
            "targetType": signal["target_type"],
            "relationshipType": signal["relationship_type"],
            "horizon": signal["horizon"],
            "score": signal["score"],
            "confidenceBand": signal["confidence_band"],
            "evidenceSummary": signal["evidence_summary"],
            "sampleSize": signal["sample_size"],
            "avgReturn": signal["avg_return"],
            "medianReturn": signal["median_return"],
            "winRate": signal["win_rate"],
            "originType": signal["origin_type"],
            "rationale": signal["rationale"],
            "metadata": signal["metadata"],
        }
        for signal in signals
    ]

    category_counts: dict[str, int] = {}
    for event in event_rows:
        category_counts[event["category"]] = category_counts.get(event["category"], 0) + 1

    top_signal = signal_rows[0] if signal_rows else None
    risk_flags = _build_risk_flags(
        ticker=normalized_ticker,
        latest_price_rows=price_rows,
        signals=signal_rows,
        studies=study_rows,
        relationships=relationship_rows,
    )
    readiness = _build_live_readiness(repo_root, normalized_ticker, signal_rows, study_rows)
    thesis_summary = _summarize_thesis(normalized_ticker, profile, signal_rows, event_rows)
    evidence_summary = (
        f"{len(signal_rows)} active signal(s), {len(study_rows)} study slice(s), "
        f"{len(event_rows)} recent event(s), and {len(relationship_rows)} relationship edge(s)."
    )

    return {
        "ticker": normalized_ticker,
        "tradingMode": trading_mode,
        "profile": profile,
        "latestPrice": {
            "close": float(latest_price.close) if latest_price else None,
            "tradeDate": latest_price.trade_date.isoformat() if latest_price else None,
            "rowCount": price_rows,
        },
        "topSignals": signal_rows,
        "recentEvents": event_rows,
        "relationships": relationship_rows,
        "studySlices": study_rows,
        "eventCategoryCounts": category_counts,
        "thesisSummary": thesis_summary,
        "evidenceSummary": evidence_summary,
        "riskFlags": risk_flags,
        "readiness": readiness,
        "outlook": {
            "signalCount": len(signal_rows),
            "strongestSignal": top_signal,
            "relatedCompanyCount": len(relationship_rows),
            "latestEventCategory": event_rows[0]["category"] if event_rows else None,
        },
    }


class LocalAIGatewayHandler(BaseHTTPRequestHandler):
    server: "LocalAIGatewayServer"

    def do_OPTIONS(self) -> None:  # pragma: no cover
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:  # pragma: no cover
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        if parsed.path == "/health":
            self._write_json(HTTPStatus.OK, success_response(self.server.health_payload()))
            return
        if parsed.path == "/health/migrations":
            self._write_json(HTTPStatus.OK, success_response(self.server.migration_health_payload()))
            return
        if parsed.path == "/health/full":
            checks, overall = run_health_check(self.server.repo_root)
            self._write_json(
                HTTPStatus.OK,
                success_response({"overall": overall, "checks": [check.to_dict() for check in checks]}),
            )
            return
        if parsed.path == "/research/company-briefing":
            ticker = str(query.get("ticker", [""])[0] or "").strip().upper()
            trading_mode = str(query.get("tradingMode", ["paper"])[0] or "paper").strip().lower()
            if not ticker:
                self._write_json(HTTPStatus.BAD_REQUEST, error_response("ticker is required"))
                return
            try:
                payload = build_company_briefing_payload(self.server.repo_root, ticker, trading_mode)
                self._write_json(HTTPStatus.OK, success_response(payload))
            except Exception as error:
                LOGGER.exception("Company briefing lookup failed.")
                self._write_json(HTTPStatus.INTERNAL_SERVER_ERROR, error_response(str(error)))
            return

        if parsed.path == "/portfolio/metrics":
            try:
                metrics = compute_portfolio_metrics(repo_root=self.server.repo_root)
                self._write_json(HTTPStatus.OK, success_response(metrics.to_dict()))
            except Exception as error:
                LOGGER.exception("Portfolio metrics failed.")
                self._write_json(HTTPStatus.INTERNAL_SERVER_ERROR, error_response(str(error)))
            return

        if parsed.path == "/market/regime":
            try:
                as_of = query.get("asOf", [None])[0]
                regime = get_current_regime(as_of, repo_root=self.server.repo_root, persist=True)
                self._write_json(HTTPStatus.OK, success_response(regime.to_dict()))
            except Exception as error:
                LOGGER.exception("Market regime lookup failed.")
                self._write_json(HTTPStatus.INTERNAL_SERVER_ERROR, error_response(str(error)))
            return

        if parsed.path == "/alpaca/account":
            try:
                account = get_account(repo_root=self.server.repo_root)
                config = load_alpaca_config(self.server.repo_root)
                self._write_json(
                    HTTPStatus.OK,
                    success_response(
                        {
                            "portfolio_value": account.get("portfolio_value") or account.get("equity"),
                            "buying_power": account.get("buying_power"),
                            "cash": account.get("cash"),
                            "equity": account.get("equity"),
                            "currency": account.get("currency"),
                            "account_status": account.get("status"),
                            "mode": config.mode,
                        }
                    ),
                )
            except Exception as error:
                LOGGER.exception("Alpaca account lookup failed.")
                self._write_json(HTTPStatus.INTERNAL_SERVER_ERROR, error_response(str(error)))
            return

        if parsed.path == "/alpaca/positions":
            try:
                positions = [
                    {
                        "ticker": position.get("symbol"),
                        "qty": position.get("qty"),
                        "market_value": position.get("market_value"),
                        "avg_entry_price": position.get("avg_entry_price"),
                        "unrealized_pl": position.get("unrealized_pl"),
                        "unrealized_plpc": position.get("unrealized_plpc"),
                        "current_price": position.get("current_price"),
                        "side": position.get("side"),
                    }
                    for position in get_positions(repo_root=self.server.repo_root)
                ]
                self._write_json(HTTPStatus.OK, success_response(positions))
            except Exception as error:
                LOGGER.exception("Alpaca positions lookup failed.")
                self._write_json(HTTPStatus.INTERNAL_SERVER_ERROR, error_response(str(error)))
            return

        if parsed.path == "/alpaca/orders":
            try:
                status = str(query.get("status", ["all"])[0] or "all")
                orders = [
                    {
                        "order_id": order.get("id"),
                        "ticker": order.get("symbol"),
                        "qty": order.get("qty"),
                        "side": order.get("side"),
                        "order_type": order.get("type"),
                        "status": order.get("status"),
                        "submitted_at": order.get("submitted_at"),
                        "filled_at": order.get("filled_at"),
                        "filled_avg_price": order.get("filled_avg_price"),
                    }
                    for order in get_orders(status=status, repo_root=self.server.repo_root)
                ]
                self._write_json(HTTPStatus.OK, success_response(orders))
            except Exception as error:
                LOGGER.exception("Alpaca order lookup failed.")
                self._write_json(HTTPStatus.INTERNAL_SERVER_ERROR, error_response(str(error)))
            return

        if parsed.path in {"/penny-stock/candidates", "/trading/penny-candidates"}:
            try:
                capital = float(query.get("capital", ["15"])[0] or 15.0)
                top_n = int(query.get("topN", ["10"])[0] or 10)
                candidates = build_penny_stock_candidates(capital, repo_root=self.server.repo_root, top_n=top_n)
                self._write_json(
                    HTTPStatus.OK,
                    success_response([candidate.to_dict() for candidate in candidates]),
                )
            except Exception as error:
                LOGGER.exception("Penny-stock candidates lookup failed.")
                self._write_json(HTTPStatus.INTERNAL_SERVER_ERROR, error_response(str(error)))
            return

        if parsed.path == "/research/fill-gaps/status":
            payload = self.server.latest_fill_gap_status()
            self._write_json(HTTPStatus.OK, success_response(payload))
            return
        if parsed.path == "/research/refresh-market-proxies/status":
            payload = self.server.latest_refresh_status()
            self._write_json(HTTPStatus.OK, success_response(payload))
            return

        if parsed.path == "/research/price-coverage":
            repository = TradingRepository(self.server.repo_root)
            rows = [
                {
                    "ticker": ticker,
                    "row_count": repository.count_daily_price_rows(ticker),
                }
                for ticker in repository.distinct_event_tickers()
            ]
            self._write_json(HTTPStatus.OK, success_response(rows))
            return

        if parsed.path == "/risk/gate-log":
            repository = TradingRepository(self.server.repo_root)
            rows = [
                {
                    "id": trade.id,
                    "ticker": trade.ticker,
                    "entryDate": trade.entry_date.isoformat(),
                    "hardBlocks": ((trade.metadata or {}).get("risk_gate") or {}).get("hardBlocks", []),
                }
                for trade in repository.load_paper_trades(statuses=["risk-blocked", "Risk-Blocked"])[:20]
            ]
            self._write_json(HTTPStatus.OK, success_response(rows))
            return

        if parsed.path.startswith("/trading/loop-status/"):
            job_id = parsed.path.rsplit("/", 1)[-1]
            job = self.server.loop_jobs.get(job_id)
            if job is None:
                self._write_json(HTTPStatus.NOT_FOUND, error_response("Loop job not found"))
                return
            self._write_json(HTTPStatus.OK, success_response(job.to_dict()))
            return

        if parsed.path == "/trading/loop-history":
            self._write_json(HTTPStatus.OK, success_response(self.server.load_loop_history()))
            return

        self._write_json(HTTPStatus.NOT_FOUND, error_response("Not found"))

    def do_POST(self) -> None:  # pragma: no cover
        parsed = urlparse(self.path)
        if parsed.path == "/chat":
            self._handle_chat()
            return
        if parsed.path == "/portfolio/construct":
            self._handle_portfolio_construct()
            return
        if parsed.path == "/risk/assess":
            self._handle_risk_assess()
            return
        if parsed.path == "/costs/estimate":
            self._handle_cost_estimate()
            return
        if parsed.path == "/trade/simulate":
            self._handle_trade_simulate()
            return
        if parsed.path == "/trading/preview-order":
            self._handle_order_preview()
            return
        if parsed.path == "/trading/run-loop":
            self._handle_trading_loop()
            return
        if parsed.path == "/research/fill-gaps":
            self._handle_fill_gaps()
            return
        if parsed.path == "/research/refresh-market-proxies":
            self._handle_refresh_market_proxies()
            return

        self._write_json(HTTPStatus.NOT_FOUND, error_response("Not found"))

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        LOGGER.info("%s - %s", self.address_string(), format % args)

    def _handle_chat(self) -> None:
        payload = self._read_json_body()
        message = str(payload.get("message", "")).strip()
        ticker = str(payload.get("ticker", "")).strip().upper() or None
        trading_mode = str(payload.get("tradingMode", "paper")).strip().lower() or "paper"
        conversation = payload.get("conversation", [])

        if not message:
            self._write_json(HTTPStatus.BAD_REQUEST, error_response("message is required"))
            return

        safe_conversation = [
            {"role": str(turn.get("role", "user")), "content": str(turn.get("content", "")).strip()}
            for turn in conversation
            if isinstance(turn, dict) and str(turn.get("content", "")).strip()
        ]

        context = self.server.context_repository.fetch_context(ticker)
        notes = build_grounding_notes(context)
        grounding_prompt = build_context_prompt(context)
        citations = [citation.to_dict() for citation in build_context_citations(context)]
        retrieval_mode = "structured"
        if self.server.semantic_retriever is not None:
            try:
                semantic_grounding = self.server.semantic_retriever.ground(message, context)
                grounding_prompt = semantic_grounding.prompt
                citations = [citation.to_dict() for citation in semantic_grounding.citations]
                notes.extend(semantic_grounding.notes)
                retrieval_mode = "semantic"
            except Exception as error:
                LOGGER.exception("Semantic retrieval failed; falling back to structured grounding.")
                notes.append(f"Semantic retrieval fallback activated: {error}")

        ollama_health = self.server.ollama_client.health()

        answer: str
        model_name: str
        grounded = True

        if ollama_health.reachable and ollama_health.model_available:
            try:
                response = self.server.ollama_client.chat(
                    system_prompt=build_system_prompt(
                        grounding_prompt=grounding_prompt or "No structured context available.",
                        trading_mode=trading_mode,
                    ),
                    conversation=safe_conversation,
                    user_message=message,
                )
                answer = response.get("message", {}).get("content", "").strip() or build_deterministic_fallback_answer(
                    message,
                    context,
                    trading_mode,
                )
                model_name = self.server.config.ollama_model
            except Exception as error:
                LOGGER.exception("Ollama chat failed; falling back to deterministic answer.")
                answer = build_deterministic_fallback_answer(message, context, trading_mode)
                model_name = "deterministic-fallback"
                grounded = False
                notes.append(f"Ollama fallback activated: {error}")
        else:
            answer = build_deterministic_fallback_answer(message, context, trading_mode)
            model_name = "deterministic-fallback"
            grounded = False
            notes.append(ollama_health.detail)

        self._write_json(
            HTTPStatus.OK,
            success_response(
                {
                "answer": answer,
                "grounded": grounded,
                "model": model_name,
                "contextTicker": context.ticker,
                "retrievalMode": retrieval_mode,
                "citations": citations,
                "notes": notes,
                }
            ),
        )

    def _handle_portfolio_construct(self) -> None:
        payload = self._read_json_body()
        method = str(payload.get("method", "")).strip()
        capital = float(payload.get("capital", 0.0) or 0.0)
        signal_keys = payload.get("signalKeys", [])

        if not method or capital <= 0:
            self._write_json(HTTPStatus.BAD_REQUEST, error_response("method and capital are required"))
            return
        try:
            if bool(payload.get("simulate", False)):
                simulation = allocate_and_simulate(
                    method,
                    capital,
                    signal_keys=signal_keys if isinstance(signal_keys, list) else [],
                    dry_run=bool(payload.get("dryRun", True)),
                    repo_root=self.server.repo_root,
                )
                self._write_json(HTTPStatus.OK, success_response(simulation.to_dict()))
            else:
                result = construct_portfolio(
                    method,
                    capital,
                    signal_keys=signal_keys if isinstance(signal_keys, list) else None,
                    repo_root=self.server.repo_root,
                    dry_run=bool(payload.get("dryRun", False)),
                )
                self._write_json(HTTPStatus.OK, result)
        except Exception as error:
            LOGGER.exception("Portfolio construction failed.")
            self._write_json(HTTPStatus.INTERNAL_SERVER_ERROR, error_response(str(error)))

    def _handle_risk_assess(self) -> None:
        payload = self._read_json_body()
        try:
            allocations_payload = payload.get("allocations", {})
            if isinstance(allocations_payload, dict) and allocations_payload:
                allocations = {
                    str(ticker).upper(): float(value)
                    for ticker, value in allocations_payload.items()
                    if value is not None
                }
            else:
                repository = TradingRepository(self.server.repo_root)
                allocations = {
                    trade.ticker: float(trade.entry_price * trade.quantity)
                    for trade in repository.load_paper_trades(statuses=["simulated", "open", "Open"])
                }
                if not allocations:
                    self._write_json(HTTPStatus.OK, success_response(assess_portfolio_risk({}, repo_root=self.server.repo_root).to_dict()))
                    return
            report = assess_portfolio_risk(allocations, repo_root=self.server.repo_root)
            self._write_json(HTTPStatus.OK, success_response(report.to_dict()))
        except Exception as error:
            LOGGER.exception("Risk assessment failed.")
            self._write_json(HTTPStatus.INTERNAL_SERVER_ERROR, error_response(str(error)))

    def _handle_cost_estimate(self) -> None:
        payload = self._read_json_body()
        ticker = str(payload.get("ticker", "")).strip().upper()
        shares = float(payload.get("shares", 100.0) or 100.0)
        entry_price = payload.get("entry_price")

        if not ticker:
            self._write_json(HTTPStatus.BAD_REQUEST, error_response("ticker is required"))
            return
        try:
            if entry_price in {None, "", 0, 0.0}:
                latest = TradingRepository(self.server.repo_root).latest_daily_price(ticker)
                if latest is None:
                    raise ValueError(f"No latest daily price is available for {ticker}.")
                entry_price = float(latest.close)
            breakdown = compute_round_trip_cost(
                ticker,
                shares,
                float(entry_price),
                repo_root=self.server.repo_root,
            )
            self._write_json(HTTPStatus.OK, success_response(breakdown.to_dict()))
        except Exception as error:
            LOGGER.exception("Transaction cost estimate failed.")
            self._write_json(HTTPStatus.INTERNAL_SERVER_ERROR, error_response(str(error)))

    def _handle_trade_simulate(self) -> None:
        payload = self._read_json_body()
        signal_key = str(payload.get("signalKey", "")).strip()
        capital = float(payload.get("capitalAllocation", payload.get("capital", 0.0)) or 0.0)
        if not signal_key or capital <= 0:
            self._write_json(HTTPStatus.BAD_REQUEST, error_response("signalKey and capitalAllocation are required"))
            return
        try:
            result = simulate_trade(
                signal_key,
                capital,
                repo_root=self.server.repo_root,
                dry_run=bool(payload.get("dryRun", False)),
                show_costs=bool(payload.get("showCosts", False)),
            )
            status = HTTPStatus.OK if result.get("success", False) else HTTPStatus.CONFLICT
            self._write_json(status, success_response(result) if result.get("success", False) else error_response(result.get("status", "simulation failed"), result))
        except Exception as error:
            LOGGER.exception("Trade simulation failed.")
            self._write_json(HTTPStatus.INTERNAL_SERVER_ERROR, error_response(str(error)))

    def _handle_order_preview(self) -> None:
        payload = self._read_json_body()
        ticker = str(payload.get("ticker", "")).strip().upper()
        side = str(payload.get("side", "buy")).strip().lower()
        qty = float(payload.get("qty", 0.0) or 0.0)
        if not ticker or qty <= 0:
            self._write_json(HTTPStatus.BAD_REQUEST, error_response("ticker and qty are required"))
            return
        try:
            preview = build_order_preview(
                ticker,
                side,
                qty,
                payload.get("accountState") or get_account(repo_root=self.server.repo_root),
                repo_root=self.server.repo_root,
            )
            self._write_json(HTTPStatus.OK, success_response(preview.to_dict()))
        except Exception as error:
            LOGGER.exception("Order preview failed.")
            self._write_json(HTTPStatus.INTERNAL_SERVER_ERROR, error_response(str(error)))

    def _handle_trading_loop(self) -> None:
        payload = self._read_json_body()
        try:
            dry_run = bool(payload.get("dryRun", True))
            mode = str(payload.get("mode", "paper")).strip().lower() or "paper"
            config = load_alpaca_config(self.server.repo_root)
            if not dry_run and not (config.mode == "live" and config.live_confirmed):
                self._write_json(
                    HTTPStatus.CONFLICT,
                    error_response("Live mode not confirmed. Set ALPACA_MODE=live and ALPACA_LIVE_CONFIRMED=true in .env to proceed."),
                )
                return
            if not dry_run and mode == "live":
                verification, _ = verify_expected_artifacts(self.server.repo_root)
                if not all(verification.values()):
                    self._write_json(
                        HTTPStatus.CONFLICT,
                        error_response("Live mode blocked because required Supabase migrations are not fully verified."),
                    )
                    return
                account = get_account(repo_root=self.server.repo_root)
                account_status = str(account.get("status") or account.get("account_status") or "unknown").upper()
                if account_status not in {"ACTIVE", "ACCOUNT_UPDATED", "APPROVAL_PENDING"}:
                    self._write_json(
                        HTTPStatus.CONFLICT,
                        error_response(f"Live mode blocked because Alpaca account status is {account_status}."),
                    )
                    return
            job_id = str(uuid4())
            self.server.loop_jobs[job_id] = BackgroundJob(job_id=job_id)

            def _runner() -> None:
                try:
                    result = run_trading_loop(
                        capital=float(payload.get("capital", 15.0) or 15.0),
                        universe=str(payload.get("universe", "penny")).strip().lower() or "penny",
                        mode=mode,
                        max_positions=int(payload.get("maxPositions", 5) or 5),
                        max_position_pct=float(payload.get("maxPositionPct", 0.25) or 0.25),
                        dry_run=dry_run,
                        repo_root=self.server.repo_root,
                        job_id=job_id,
                    )
                    self.server.loop_jobs[job_id].status = "complete"
                    self.server.loop_jobs[job_id].result = result.get("data")
                except Exception as error:
                    LOGGER.exception("Trading loop background job failed.")
                    self.server.loop_jobs[job_id].status = "error"
                    self.server.loop_jobs[job_id].error = str(error)

            threading.Thread(target=_runner, daemon=True).start()
            self._write_json(
                HTTPStatus.OK,
                success_response(
                    {
                        "job_id": job_id,
                        "dry_run": dry_run,
                        "universe": str(payload.get("universe", "penny")).strip().lower() or "penny",
                        "capital": float(payload.get("capital", 15.0) or 15.0),
                    }
                ),
            )
        except Exception as error:
            LOGGER.exception("Trading loop execution failed.")
            self._write_json(HTTPStatus.INTERNAL_SERVER_ERROR, error_response(str(error)))

    def _handle_fill_gaps(self) -> None:
        payload = self._read_json_body()
        job_id = str(uuid4())
        report_path = self.server.repo_root / "reports" / "study_universe_gap_fill.json"
        command = [
            sys.executable,
            "-m",
            "research.fill_study_universe_gaps",
            "--json-output",
            str(report_path),
        ]
        if bool(payload.get("auto_recompute", True)):
            command.append("--auto-recompute")
        for ticker in payload.get("tickerFilters", []) if isinstance(payload.get("tickerFilters"), list) else []:
            command.extend(["--ticker", str(ticker)])
        process = subprocess.Popen(command, cwd=self.server.repo_root)
        self.server.fill_gap_jobs[job_id] = {"process_id": process.pid, "started_at": datetime.now().isoformat()}
        self._write_json(HTTPStatus.OK, success_response({"job": "started", "job_id": job_id}))

    def _handle_refresh_market_proxies(self) -> None:
        payload = self._read_json_body()
        job_id = str(uuid4())
        report_path = self.server.repo_root / "reports" / "market_proxy_refresh.json"
        command = [
            sys.executable,
            "-m",
            "research.refresh_market_proxies",
            "--json-output",
            str(report_path),
        ]
        if payload.get("price_file"):
            command.extend(["--price-file", str(payload["price_file"])])
        if payload.get("tickers") and isinstance(payload.get("tickers"), list):
            for ticker in payload.get("tickers"):
                command.extend(["--ticker", str(ticker)])
        if payload.get("dry_run"):
            command.append("--dry-run")
        if payload.get("bootstrap_schema"):
            command.append("--bootstrap-schema")
        if payload.get("load_supabase") is False:
            command.append("--no-supabase-load")

        process = subprocess.Popen(command, cwd=self.server.repo_root)
        self.server.refresh_jobs[job_id] = {"process_id": process.pid, "started_at": datetime.now().isoformat()}
        self._write_json(HTTPStatus.OK, success_response({"job": "started", "job_id": job_id}))

    def _read_json_body(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            return {}

        raw_body = self.rfile.read(content_length)
        if not raw_body:
            return {}
        return json.loads(raw_body.decode("utf-8"))

    def _write_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(payload, default=str).encode("utf-8"))

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")


class LocalAIGatewayServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], handler_class: type[BaseHTTPRequestHandler], repo_root: Path):
        self.repo_root = repo_root
        self.config = load_local_ai_config(repo_root)
        self.context_repository = LocalAIContextRepository(repo_root)
        self.ollama_client = OllamaClient(self.config)
        self.semantic_retriever = SemanticRetriever(self.config) if active_retrieval_mode(self.config) == "semantic" else None
        self.loop_jobs: dict[str, BackgroundJob] = {}
        self.fill_gap_jobs: dict[str, dict[str, Any]] = {}
        self.refresh_jobs: dict[str, dict[str, Any]] = {}
        super().__init__(server_address, handler_class)

    def health_payload(self) -> dict[str, Any]:
        ollama_health = self.ollama_client.health()
        retrieval_mode = active_retrieval_mode(self.config)
        semantic_ready = semantic_runtime_ready()
        notes: list[str] = []

        if retrieval_mode == "structured":
            notes.append("Semantic retrieval assets are present, but the runtime is still using structured grounding.")
        else:
            notes.append(f"Semantic retrieval is active on {self.config.semantic_device}.")
        if not ollama_health.model_available:
            notes.append(ollama_health.detail)

        status = "connected" if ollama_health.reachable and ollama_health.model_available else "degraded"

        return {
            "status": status,
            "assistantLabel": "Local Qwen Assistant" if ollama_health.model_available else "Deterministic Research Fallback",
            "model": self.config.ollama_model if ollama_health.model_available else "deterministic-fallback",
            "ollamaReachable": ollama_health.reachable,
            "modelAvailable": ollama_health.model_available,
            "retrievalMode": retrieval_mode,
            "embeddingModelPresent": self.config.bge_model_dir.exists(),
            "rerankerModelPresent": self.config.reranker_model_dir.exists(),
            "semanticRuntimeReady": semantic_ready,
            "notes": notes,
        }

    def migration_health_payload(self) -> dict[str, Any]:
        verification, _ = verify_expected_artifacts(self.repo_root)
        return {
            "migrations_checked": ["009", "010", "011", "012", "013"],
            "tables_verified": verification,
            "all_verified": all(verification.values()),
        }

    def latest_fill_gap_status(self) -> dict[str, Any]:
        report_path = self.repo_root / "reports" / "study_universe_gap_fill.json"
        if not report_path.exists():
            return {"job": "idle", "reportAvailable": False}
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        return {"job": "complete", "reportAvailable": True, "summary": payload}

    def latest_refresh_status(self) -> dict[str, Any]:
        report_path = self.repo_root / "reports" / "market_proxy_refresh.json"
        if not report_path.exists():
            return {"job": "idle", "reportAvailable": False}
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        return {"job": "complete", "reportAvailable": True, "summary": payload}

    def load_loop_history(self) -> list[dict[str, Any]]:
        report_dir = self.repo_root / "reports"
        reports = sorted(report_dir.glob("trading_loop_run_*.json"), reverse=True)[:10]
        history: list[dict[str, Any]] = []
        for report_path in reports:
            try:
                history.append(json.loads(report_path.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                continue
        history.sort(key=lambda item: item.get("timestamp", ""), reverse=True)
        return history


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start the StrattonAI local AI gateway.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    repo_root = Path(__file__).resolve().parent.parent
    server = LocalAIGatewayServer((args.host, args.port), LocalAIGatewayHandler, repo_root)
    LOGGER.info("Local AI gateway listening on http://%s:%s", args.host, args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover
        LOGGER.info("Stopping local AI gateway.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
