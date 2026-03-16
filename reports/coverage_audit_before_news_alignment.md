# Coverage Audit

## Event Coverage
- Capital Expenditure: 13 events
- Earnings: 6 events
- Legal/Regulatory: 14 events
- Macro Event: 8 events
- Partnership: 13 events
- Product Launch: 12 events
- Regulatory Approval: 5 events
- Supply Disruption: 5 events

## Source Coverage
- historical_backfill: 30 events
- historical_backfill_wave2: 8 events
- historical_backfill_wave3: 3 events
- manual_seed: 5 events
- sec_filing: 30 events

## Weak Signal Categories
- None

## Top Gap Candidates
- #1 Need 6 more Macro Event examples for AAPL primary studies (gap_score=59.0)
  Recommendation: Add more structured Macro Event history for AAPL so exact primary slices stop relying on category summaries.
  Rationale: Macro Event primary slice for AAPL has sample 0, missing horizons ['1D', '3D', '5D', '10D', '20D'], fallback usage 0, signal usage 0.
- #2 Need 6 more Macro Event examples for MSFT primary studies (gap_score=59.0)
  Recommendation: Add more structured Macro Event history for MSFT so exact primary slices stop relying on category summaries.
  Rationale: Macro Event primary slice for MSFT has sample 0, missing horizons ['1D', '3D', '5D', '10D', '20D'], fallback usage 0, signal usage 0.
- #3 Need 6 more Macro Event examples for NVDA primary studies (gap_score=59.0)
  Recommendation: Add more structured Macro Event history for NVDA so exact primary slices stop relying on category summaries.
  Rationale: Macro Event primary slice for NVDA has sample 0, missing horizons ['1D', '3D', '5D', '10D', '20D'], fallback usage 0, signal usage 0.
- #4 Need 6 more Product Launch examples for AAPL primary studies (gap_score=58.3)
  Recommendation: Add more structured Product Launch history for AAPL so exact primary slices stop relying on category summaries.
  Rationale: Product Launch primary slice for AAPL has sample 0, missing horizons ['1D', '3D', '5D', '10D', '20D'], fallback usage 0, signal usage 0.
- #5 Need 6 more Product Launch examples for LLY primary studies (gap_score=58.3)
  Recommendation: Add more structured Product Launch history for LLY so exact primary slices stop relying on category summaries.
  Rationale: Product Launch primary slice for LLY has sample 0, missing horizons ['1D', '3D', '5D', '10D', '20D'], fallback usage 0, signal usage 0.
- #6 Need 6 more Product Launch examples for MSFT primary studies (gap_score=58.3)
  Recommendation: Add more structured Product Launch history for MSFT so exact primary slices stop relying on category summaries.
  Rationale: Product Launch primary slice for MSFT has sample 0, missing horizons ['1D', '3D', '5D', '10D', '20D'], fallback usage 0, signal usage 0.
- #7 Need 6 more Product Launch examples for NVDA primary studies (gap_score=58.3)
  Recommendation: Add more structured Product Launch history for NVDA so exact primary slices stop relying on category summaries.
  Rationale: Product Launch primary slice for NVDA has sample 0, missing horizons ['1D', '3D', '5D', '10D', '20D'], fallback usage 0, signal usage 0.
- #8 Need 6 more Product Launch examples for QCOM primary studies (gap_score=58.3)
  Recommendation: Add more structured Product Launch history for QCOM so exact primary slices stop relying on category summaries.
  Rationale: Product Launch primary slice for QCOM has sample 0, missing horizons ['1D', '3D', '5D', '10D', '20D'], fallback usage 0, signal usage 0.
- #9 Need 6 more Product Launch examples for TSLA primary studies (gap_score=58.3)
  Recommendation: Add more structured Product Launch history for TSLA so exact primary slices stop relying on category summaries.
  Rationale: Product Launch primary slice for TSLA has sample 0, missing horizons ['1D', '3D', '5D', '10D', '20D'], fallback usage 0, signal usage 0.
- #10 Need 6 more Earnings examples for AAPL primary studies (gap_score=57.88)
  Recommendation: Add more structured Earnings history for AAPL so exact primary slices stop relying on category summaries.
  Rationale: Earnings primary slice for AAPL has sample 0, missing horizons ['1D', '3D', '5D', '10D', '20D'], fallback usage 0, signal usage 0.
- #11 Need 6 more Earnings examples for AMD primary studies (gap_score=57.88)
  Recommendation: Add more structured Earnings history for AMD so exact primary slices stop relying on category summaries.
  Rationale: Earnings primary slice for AMD has sample 0, missing horizons ['1D', '3D', '5D', '10D', '20D'], fallback usage 0, signal usage 0.
- #12 Need 6 more Earnings examples for LLY primary studies (gap_score=57.88)
  Recommendation: Add more structured Earnings history for LLY so exact primary slices stop relying on category summaries.
  Rationale: Earnings primary slice for LLY has sample 0, missing horizons ['1D', '3D', '5D', '10D', '20D'], fallback usage 0, signal usage 0.

## Sparse Primary Slices
- Macro Event / AAPL: sample=0, fallbacks=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=59.0
- Macro Event / MSFT: sample=0, fallbacks=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=59.0
- Macro Event / NVDA: sample=0, fallbacks=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=59.0
- Product Launch / AAPL: sample=0, fallbacks=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=58.3
- Product Launch / LLY: sample=0, fallbacks=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=58.3
- Product Launch / MSFT: sample=0, fallbacks=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=58.3
- Product Launch / NVDA: sample=0, fallbacks=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=58.3
- Product Launch / QCOM: sample=0, fallbacks=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=58.3
- Product Launch / TSLA: sample=0, fallbacks=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=58.3
- Earnings / AAPL: sample=0, fallbacks=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=57.88

## Sparse Related Slices
- Macro Event / TSM / Supplier: sample=0, fallbacks=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=51.0
- Macro Event / GOOGL / Competitor: sample=0, fallbacks=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=50.6
- Product Launch / PANW / Supplier: sample=0, fallbacks=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=50.6
- Product Launch / QCOM / Supplier: sample=0, fallbacks=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=50.6
- Product Launch / TSM / Supplier: sample=0, fallbacks=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=50.6
- Earnings / QCOM / Supplier: sample=0, fallbacks=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=50.36
- Earnings / TSM / Supplier: sample=0, fallbacks=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=50.36
- Product Launch / AMD / Competitor: sample=0, fallbacks=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=50.2
- Product Launch / AMZN / Competitor: sample=0, fallbacks=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=50.2
- Product Launch / GOOGL / Competitor: sample=0, fallbacks=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=50.2

## Sparse Relationship Slices
- Macro Event / Supplier: sample=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=48.0
- Macro Event / Competitor: sample=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=47.65
- Product Launch / Supplier: sample=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=47.65
- Earnings / Supplier: sample=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=47.44
- Product Launch / Competitor: sample=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=47.3
- Legal/Regulatory / Supplier: sample=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=47.16
- Earnings / Competitor: sample=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=47.09
- Regulatory Approval / Competitor: sample=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=46.95
- Supply Disruption / Supplier: sample=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=46.88
- Legal/Regulatory / Competitor: sample=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=46.81

## Missing Price History
- No current price-history gaps detected for referenced tickers.
