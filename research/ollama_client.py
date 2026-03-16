from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from .local_ai_config import LocalAIConfig


@dataclass(frozen=True, slots=True)
class OllamaHealth:
    reachable: bool
    model_available: bool
    installed_models: list[str]
    detail: str


class OllamaClient:
    def __init__(self, config: LocalAIConfig):
        self.config = config

    def health(self) -> OllamaHealth:
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.config.ollama_url}/api/tags")
                response.raise_for_status()
                payload = response.json()
        except Exception as error:
            return OllamaHealth(
                reachable=False,
                model_available=False,
                installed_models=[],
                detail=f"Ollama is unreachable: {error}",
            )

        models = [model.get("name", "") for model in payload.get("models", []) if model.get("name")]
        return OllamaHealth(
            reachable=True,
            model_available=self.config.ollama_model in models,
            installed_models=models,
            detail="Ollama is reachable." if self.config.ollama_model in models else f'Model "{self.config.ollama_model}" is not installed in Ollama.',
        )

    def chat(self, *, system_prompt: str, conversation: list[dict[str, str]], user_message: str) -> dict[str, Any]:
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation[-6:])
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": self.config.ollama_model,
            "stream": False,
            "messages": messages,
            "options": {
                "temperature": 0,
                "seed": 42,
            },
        }

        with httpx.Client(timeout=self.config.ollama_timeout_seconds) as client:
            response = client.post(f"{self.config.ollama_url}/api/chat", json=payload)
            response.raise_for_status()
            return response.json()
