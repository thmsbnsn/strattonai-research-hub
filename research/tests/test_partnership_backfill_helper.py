from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research.partnership_backfill_helper import _query_partnership_priorities


class _FakeRepository:
    def __init__(self, _root: Path):
        pass

    def connect(self):
        class _Cursor:
            def __init__(self):
                self.calls = 0

            def execute(self, sql, params=None):
                self.calls += 1

            def fetchall(self):
                datasets = [
                    [("MSFT", "2026-03-10"), ("TSM", "2026-03-09")],
                    [("MSFT", 2), ("TSM", 0)],
                    [("MSFT", 10), ("TSM", 15)],
                    [("MSFT", "NVDA", 0.8), ("TSM", "AMD", 0.9)],
                ]
                index = min(self.calls - 1, len(datasets) - 1)
                return datasets[index]

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        class _Connection:
            def cursor(self):
                return _Cursor()

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        return _Connection()


class PartnershipBackfillHelperTests(unittest.TestCase):
    def test_priorities_are_ranked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            priorities = _query_partnership_priorities(_FakeRepository(Path(temp_dir)), 5, 20)
        self.assertGreater(len(priorities), 0)
        self.assertEqual(priorities[0].ticker, "TSM")


if __name__ == "__main__":
    unittest.main()
