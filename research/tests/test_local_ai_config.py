from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from research.local_ai_config import active_retrieval_mode, load_local_ai_config


class LocalAIConfigTests(unittest.TestCase):
    def test_defaults_resolve_repo_local_model_paths(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        config = load_local_ai_config(repo_root, env={})

        self.assertEqual(config.host, "127.0.0.1")
        self.assertEqual(config.port, 8787)
        self.assertEqual(config.ollama_model, "qwen2.5:14b-instruct")
        self.assertEqual(config.bge_model_dir, repo_root / "models" / "huggingface" / "bge-m3")
        self.assertEqual(config.reranker_model_dir, repo_root / "models" / "huggingface" / "bge-reranker-v2-m3")

    def test_retrieval_mode_stays_structured_without_runtime(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        config = load_local_ai_config(repo_root, env={})

        with patch("research.local_ai_config.semantic_runtime_ready", return_value=False):
            self.assertEqual(active_retrieval_mode(config), "structured")

    def test_retrieval_mode_switches_to_semantic_when_runtime_is_ready(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        config = load_local_ai_config(repo_root, env={})

        with patch("research.local_ai_config.semantic_runtime_ready", return_value=True):
            self.assertEqual(active_retrieval_mode(config), "semantic")


if __name__ == "__main__":
    unittest.main()
