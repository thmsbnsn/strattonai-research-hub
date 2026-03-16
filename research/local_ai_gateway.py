from __future__ import annotations

import argparse
import json
import logging
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .local_ai_config import active_retrieval_mode, load_local_ai_config, semantic_runtime_ready
from .local_ai_context import (
    LocalAIContextRepository,
    build_context_citations,
    build_context_prompt,
    build_deterministic_fallback_answer,
    build_grounding_notes,
)
from .ollama_client import OllamaClient
from .semantic_retrieval import SemanticRetriever


LOGGER = logging.getLogger("research.local_ai_gateway")


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


class LocalAIGatewayHandler(BaseHTTPRequestHandler):
    server: "LocalAIGatewayServer"

    def do_OPTIONS(self) -> None:  # pragma: no cover
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:  # pragma: no cover
        if self.path == "/health":
            self._write_json(HTTPStatus.OK, self.server.health_payload())
            return

        self._write_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self) -> None:  # pragma: no cover
        if self.path == "/chat":
            self._handle_chat()
            return

        self._write_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        LOGGER.info("%s - %s", self.address_string(), format % args)

    def _handle_chat(self) -> None:
        payload = self._read_json_body()
        message = str(payload.get("message", "")).strip()
        ticker = str(payload.get("ticker", "")).strip().upper() or None
        trading_mode = str(payload.get("tradingMode", "paper")).strip().lower() or "paper"
        conversation = payload.get("conversation", [])

        if not message:
            self._write_json(HTTPStatus.BAD_REQUEST, {"error": "message is required"})
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
            {
                "answer": answer,
                "grounded": grounded,
                "model": model_name,
                "contextTicker": context.ticker,
                "retrievalMode": retrieval_mode,
                "citations": citations,
                "notes": notes,
            },
        )

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
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")


class LocalAIGatewayServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], handler_class: type[BaseHTTPRequestHandler], repo_root: Path):
        self.config = load_local_ai_config(repo_root)
        self.context_repository = LocalAIContextRepository(repo_root)
        self.ollama_client = OllamaClient(self.config)
        self.semantic_retriever = SemanticRetriever(self.config) if active_retrieval_mode(self.config) == "semantic" else None
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
