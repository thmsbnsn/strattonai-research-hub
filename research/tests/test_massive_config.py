from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from research.massive_config import DEFAULT_MASSIVE_BASE_URL, load_massive_config


class MassiveConfigTests(unittest.TestCase):
    def test_config_loads_from_env_file_without_logging_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            env_path = repo_root / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "// comment line",
                        "MASSIVE_API_KEY=test_api_key",
                        "MASSIVE_ACCESS_KEY_ID=test_access_key",
                        "MASSIVE_SECRET_ACCESS_KEY=test_secret",
                        "MASSIVE_S3_ENDPOINT=https://files.massive.com",
                        "MASSIVE_BUCKET=flatfiles",
                    ]
                ),
                encoding="utf-8",
            )

            config = load_massive_config(repo_root)

        self.assertEqual(config.api_key, "test_api_key")
        self.assertEqual(config.base_url, DEFAULT_MASSIVE_BASE_URL)
        self.assertTrue(config.safe_summary()["has_api_key"])
        self.assertEqual(config.safe_summary()["bucket"], "flatfiles")

    def test_missing_api_key_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / ".env").write_text("", encoding="utf-8")

            with self.assertRaises(ValueError):
                load_massive_config(repo_root)


if __name__ == "__main__":
    unittest.main()
