from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research.alpaca_client import get_account, load_alpaca_config, submit_order


class _FakeResponse:
    def __init__(self, payload):
        self.payload = payload
        self.status = 200

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class AlpacaClientTests(unittest.TestCase):
    def test_load_alpaca_config_reads_env_without_exposing_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, patch.dict(
            os.environ,
            {
                "ALPACA_API_KEY": "key",
                "ALPACA_SECRET_KEY": "secret",
                "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
                "ALPACA_MODE": "paper",
            },
            clear=False,
        ), patch("research.alpaca_client.load_ingestion_environment"):
            config = load_alpaca_config(Path(temp_dir))

        self.assertEqual(config.mode, "paper")
        self.assertEqual(config.base_url, "https://paper-api.alpaca.markets")

    def test_submit_order_refuses_unconfirmed_live_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, patch.dict(
            os.environ,
            {
                "ALPACA_API_KEY": "key",
                "ALPACA_SECRET_KEY": "secret",
                "ALPACA_BASE_URL": "https://api.alpaca.markets",
                "ALPACA_MODE": "live",
                "ALPACA_LIVE_CONFIRMED": "false",
            },
            clear=False,
        ), patch("research.alpaca_client.load_ingestion_environment"):
            with self.assertRaises(RuntimeError):
                submit_order("AAPL", 1, "buy", repo_root=Path(temp_dir))

    def test_get_account_uses_http_wrapper(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, patch.dict(
            os.environ,
            {
                "ALPACA_API_KEY": "key",
                "ALPACA_SECRET_KEY": "secret",
                "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
                "ALPACA_MODE": "paper",
            },
            clear=False,
        ), patch("research.alpaca_client.load_ingestion_environment"), patch(
            "research.alpaca_client.urlopen",
            return_value=_FakeResponse({"status": "ACTIVE"}),
        ):
            account = get_account(Path(temp_dir))

        self.assertEqual(account["status"], "ACTIVE")


if __name__ == "__main__":
    unittest.main()
