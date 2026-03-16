from __future__ import annotations

import unittest

from research.local_ai_models import LocalAIContext
from research.semantic_retrieval import build_semantic_candidates, build_semantic_prompt


class SemanticRetrievalTests(unittest.TestCase):
    def test_candidates_cover_multiple_structured_sources(self) -> None:
        context = LocalAIContext(
            ticker="NVDA",
            company_name="NVIDIA Corporation",
            profile={"sector": "Technology", "industry": "Semiconductors"},
            latest_price={"ticker": "NVDA", "close": 132.45, "trade_date": "2026-03-16", "volume": 1200},
            signals=[
                {
                    "event_category": "Product Launch",
                    "horizon": "5D",
                    "score": 84.2,
                    "confidence_band": "High",
                    "sample_size": 18,
                    "avg_return": 2.4,
                    "median_return": 2.0,
                    "win_rate": 67,
                    "target_ticker": "NVDA",
                    "primary_ticker": "NVDA",
                    "evidence_summary": "Launches have historically outperformed.",
                }
            ],
            events=[
                {
                    "ticker": "NVDA",
                    "category": "Product Launch",
                    "sentiment": "positive",
                    "timestamp": "2026-03-15T14:30:00+00:00",
                    "headline": "NVIDIA launches a new AI training platform",
                }
            ],
            relationships=[
                {
                    "source_ticker": "NVDA",
                    "source_name": "NVIDIA",
                    "target_ticker": "TSM",
                    "target_name": "Taiwan Semiconductor",
                    "relationship_type": "Supplier",
                    "strength": 0.95,
                }
            ],
            studies=[
                {
                    "event_category": "Product Launch",
                    "horizon": "5D",
                    "study_target_type": "primary",
                    "avg_return": 1.8,
                    "median_return": 1.3,
                    "win_rate": 61,
                    "sample_size": 14,
                    "primary_ticker": "NVDA",
                    "related_ticker": None,
                    "relationship_type": None,
                }
            ],
            insights=[
                {
                    "title": "AI chip launches tend to strengthen suppliers",
                    "summary": "Supplier peers often rally alongside AI launch cycles.",
                    "confidence": "High",
                    "event_count": 12,
                }
            ],
        )

        candidates = build_semantic_candidates(context)
        candidate_kinds = {candidate.kind for candidate in candidates}

        self.assertTrue({"profile", "price", "signal", "event", "relationship", "study", "insight"}.issubset(candidate_kinds))

    def test_semantic_prompt_uses_selected_candidates(self) -> None:
        context = LocalAIContext(ticker="AAPL", company_name="Apple Inc.", notes=["No daily price rows are currently available for AAPL."])
        candidates = [
            candidate
            for candidate in build_semantic_candidates(
                LocalAIContext(
                    ticker="AAPL",
                    company_name="Apple Inc.",
                    signals=[
                        {
                            "event_category": "Legal/Regulatory",
                            "horizon": "10D",
                            "score": 62.0,
                            "confidence_band": "Moderate",
                            "sample_size": 9,
                            "avg_return": -1.2,
                            "median_return": -0.7,
                            "win_rate": 44,
                            "target_ticker": "AAPL",
                            "primary_ticker": "AAPL",
                            "evidence_summary": "Regulatory pressure has been mixed.",
                        }
                    ],
                )
            )
            if candidate.kind == "signal"
        ]

        prompt = build_semantic_prompt(
            context=context,
            query="Show the current risk case for AAPL",
            selected_candidates=candidates,
        )

        self.assertIn("User request: Show the current risk case for AAPL", prompt)
        self.assertIn("Most relevant structured context:", prompt)
        self.assertIn("Legal/Regulatory", prompt)


if __name__ == "__main__":
    unittest.main()
