from __future__ import annotations

import unittest

from research.local_ai_context import (
    build_context_citations,
    build_context_prompt,
    build_deterministic_fallback_answer,
)
from research.local_ai_models import LocalAIContext


class LocalAIContextTests(unittest.TestCase):
    def test_prompt_includes_signal_and_event_sections(self) -> None:
        context = LocalAIContext(
            ticker="NVDA",
            company_name="NVIDIA Corporation",
            signals=[
                {
                    "event_category": "Product Launch",
                    "horizon": "5D",
                    "score": 84.2,
                    "confidence_band": "High",
                    "sample_size": 18,
                    "target_ticker": "NVDA",
                }
            ],
            events=[
                {
                    "ticker": "NVDA",
                    "category": "Product Launch",
                    "headline": "NVIDIA announces next-gen AI training chips",
                }
            ],
        )

        prompt = build_context_prompt(context)

        self.assertIn("Focus ticker: NVDA", prompt)
        self.assertIn("Signals:", prompt)
        self.assertIn("Recent events:", prompt)

    def test_citations_are_built_from_structured_rows(self) -> None:
        context = LocalAIContext(
            ticker="AAPL",
            company_name="Apple Inc.",
            signals=[
                {
                    "event_category": "Legal/Regulatory",
                    "horizon": "3D",
                    "score": 61.3,
                    "confidence_band": "Moderate",
                    "sample_size": 9,
                    "target_ticker": "AAPL",
                    "primary_ticker": "AAPL",
                }
            ],
            events=[
                {
                    "ticker": "AAPL",
                    "category": "Legal/Regulatory",
                    "headline": "Apple loses antitrust case in EU",
                }
            ],
            studies=[
                {
                    "event_category": "Legal/Regulatory",
                    "horizon": "3D",
                    "study_target_type": "primary",
                    "avg_return": -1.4,
                    "win_rate": 0.42,
                    "sample_size": 9,
                    "primary_ticker": "AAPL",
                    "related_ticker": None,
                }
            ],
        )

        citations = build_context_citations(context)

        self.assertEqual(citations[0].kind, "signal")
        self.assertEqual(citations[1].kind, "event")
        self.assertEqual(citations[2].kind, "study")
        self.assertIn("win rate 42%", citations[2].detail)

    def test_deterministic_fallback_prefers_best_signal(self) -> None:
        context = LocalAIContext(
            ticker="TSLA",
            company_name="Tesla, Inc.",
            signals=[
                {
                    "event_category": "Supply Disruption",
                    "horizon": "5D",
                    "score": 54.8,
                    "confidence_band": "Moderate",
                    "sample_size": 11,
                }
            ],
        )

        answer = build_deterministic_fallback_answer("What is the setup?", context, "paper")

        self.assertIn("TSLA", answer)
        self.assertIn("54.8", answer)
        self.assertIn("paper", answer)


if __name__ == "__main__":
    unittest.main()
