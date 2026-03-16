from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path

from ingestion.write_to_supabase import load_ingestion_environment


DEFAULT_AI_GATEWAY_HOST = "127.0.0.1"
DEFAULT_AI_GATEWAY_PORT = 8787
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5:14b-instruct"


@dataclass(frozen=True, slots=True)
class LocalAIConfig:
    host: str
    port: int
    ollama_url: str
    ollama_model: str
    ollama_timeout_seconds: int
    semantic_device: str
    semantic_top_k: int
    semantic_rerank_limit: int
    models_dir: Path
    bge_model_dir: Path
    reranker_model_dir: Path

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def runtime_report(self) -> dict[str, bool | str]:
        return {
            "retrieval_mode": active_retrieval_mode(self),
            "embedding_model_present": self.bge_model_dir.exists(),
            "reranker_model_present": self.reranker_model_dir.exists(),
            "semantic_runtime_ready": semantic_runtime_ready(),
        }


def load_local_ai_config(repo_root: Path, env: dict[str, str] | None = None) -> LocalAIConfig:
    load_ingestion_environment(repo_root)

    merged_env = dict(env or {})

    def get_env(key: str, default: str | None = None) -> str | None:
        if key in merged_env:
            return merged_env[key]
        import os

        return os.environ.get(key, default)

    models_dir = repo_root / "models"
    return LocalAIConfig(
        host=get_env("STRATTONAI_AI_GATEWAY_HOST", DEFAULT_AI_GATEWAY_HOST) or DEFAULT_AI_GATEWAY_HOST,
        port=int(get_env("STRATTONAI_AI_GATEWAY_PORT", str(DEFAULT_AI_GATEWAY_PORT)) or DEFAULT_AI_GATEWAY_PORT),
        ollama_url=(get_env("STRATTONAI_OLLAMA_URL", DEFAULT_OLLAMA_URL) or DEFAULT_OLLAMA_URL).rstrip("/"),
        ollama_model=get_env("STRATTONAI_OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL) or DEFAULT_OLLAMA_MODEL,
        ollama_timeout_seconds=int(get_env("STRATTONAI_OLLAMA_TIMEOUT_SECONDS", "120") or "120"),
        semantic_device=(get_env("STRATTONAI_SEMANTIC_DEVICE", "cpu") or "cpu").lower(),
        semantic_top_k=int(get_env("STRATTONAI_SEMANTIC_TOP_K", "5") or "5"),
        semantic_rerank_limit=int(get_env("STRATTONAI_SEMANTIC_RERANK_LIMIT", "8") or "8"),
        models_dir=models_dir,
        bge_model_dir=models_dir / "huggingface" / "bge-m3",
        reranker_model_dir=models_dir / "huggingface" / "bge-reranker-v2-m3",
    )


def semantic_runtime_ready() -> bool:
    required_modules = ("torch", "transformers")
    return all(importlib.util.find_spec(module_name) is not None for module_name in required_modules)


def active_retrieval_mode(config: LocalAIConfig) -> str:
    if config.bge_model_dir.exists() and config.reranker_model_dir.exists() and semantic_runtime_ready():
        return "semantic"
    return "structured"
