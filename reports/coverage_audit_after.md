# Coverage Audit

## Event Coverage
- Capital Expenditure: 12 events
- Earnings: 6 events
- Legal/Regulatory: 13 events
- Macro Event: 6 events
- Partnership: 12 events
- Product Launch: 11 events
- Regulatory Approval: 5 events
- Supply Disruption: 5 events

## Source Coverage
- historical_backfill: 30 events
- historical_backfill_wave2: 8 events
- manual_seed: 5 events
- sec_filing: 27 events

## Weak Signal Categories
- Legal/Regulatory: high=0, moderate=6, low=204, high_ratio=0.00%, gap_score=41.96
- Partnership: high=12, moderate=82, low=156, high_ratio=4.80%, gap_score=37.84
- Supply Disruption: high=0, moderate=10, low=95, high_ratio=0.00%, gap_score=37.2
- Earnings: high=0, moderate=28, low=67, high_ratio=0.00%, gap_score=36.88
- Regulatory Approval: high=0, moderate=24, low=51, high_ratio=0.00%, gap_score=36.04

## Top Gap Candidates
- #1 Need 1 more Capital Expenditure examples for ORCL related slices (gap_score=173.93)
  Recommendation: Target Capital Expenditure examples that attach ORCL as a Sector Peer related company.
  Rationale: Capital Expenditure related slice for ORCL / Sector Peer has sample 11, missing horizons [], fallback usage 55, signal usage 55.
- #2 Need 1 more Legal/Regulatory examples for GOOGL related slices (gap_score=160.14)
  Recommendation: Target Legal/Regulatory examples that attach GOOGL as a Sector Peer related company.
  Rationale: Legal/Regulatory related slice for GOOGL / Sector Peer has sample 10, missing horizons [], fallback usage 50, signal usage 50.
- #3 Need 1 more Partnership examples for TSM related slices (gap_score=132.24)
  Recommendation: Target Partnership examples that attach TSM as a Supplier related company.
  Rationale: Partnership related slice for TSM / Supplier has sample 8, missing horizons [], fallback usage 40, signal usage 40.
- #4 Need 1 more Capital Expenditure examples for AMZN related slices (gap_score=131.68)
  Recommendation: Target Capital Expenditure examples that attach AMZN as a Competitor related company.
  Rationale: Capital Expenditure related slice for AMZN / Competitor has sample 8, missing horizons [], fallback usage 40, signal usage 40.
- #5 Need 1 more Partnership examples for MSFT related slices (gap_score=131.28)
  Recommendation: Target Partnership examples that attach MSFT as a Customer related company.
  Rationale: Partnership related slice for MSFT / Customer has sample 8, missing horizons [], fallback usage 40, signal usage 40.
- #6 Need 1 more Legal/Regulatory examples for META related slices (gap_score=130.64)
  Recommendation: Target Legal/Regulatory examples that attach META as a Sector Peer related company.
  Rationale: Legal/Regulatory related slice for META / Sector Peer has sample 8, missing horizons [], fallback usage 40, signal usage 40.
- #7 Need 1 more Partnership examples for AVGO related slices (gap_score=129.84)
  Recommendation: Target Partnership examples that attach AVGO as a Sector Peer related company.
  Rationale: Partnership related slice for AVGO / Sector Peer has sample 8, missing horizons [], fallback usage 40, signal usage 40.
- #8 Need 1 more Product Launch examples for GOOGL related slices (gap_score=103.7)
  Recommendation: Target Product Launch examples that attach GOOGL as a Competitor related company.
  Rationale: Product Launch related slice for GOOGL / Competitor has sample 6, missing horizons [], fallback usage 30, signal usage 30.
- #9 Need 1 more Product Launch examples for TSM related slices (gap_score=89.35)
  Recommendation: Target Product Launch examples that attach TSM as a Supplier related company.
  Rationale: Product Launch related slice for TSM / Supplier has sample 5, missing horizons [], fallback usage 25, signal usage 25.
- #10 Need 1 more Capital Expenditure examples for GOOGL related slices (gap_score=87.43)
  Recommendation: Target Capital Expenditure examples that attach GOOGL as a Competitor related company.
  Rationale: Capital Expenditure related slice for GOOGL / Competitor has sample 5, missing horizons [], fallback usage 25, signal usage 25.
- #11 Need 1 more Product Launch examples for AMD related slices (gap_score=78.7)
  Recommendation: Target Product Launch examples that attach AMD as a Competitor related company.
  Rationale: Product Launch related slice for AMD / Competitor has sample 4, missing horizons [], fallback usage 20, signal usage 20.
- #12 Need 1 more Product Launch examples for MSFT related slices (gap_score=78.14)
  Recommendation: Target Product Launch examples that attach MSFT as a Customer related company.
  Rationale: Product Launch related slice for MSFT / Customer has sample 4, missing horizons [], fallback usage 20, signal usage 20.

## Sparse Primary Slices
- Macro Event / AAPL: sample=1, fallbacks=0, missing_horizons=[], gap_score=43.0
- Product Launch / LLY: sample=1, fallbacks=0, missing_horizons=[], gap_score=42.3
- Product Launch / TSLA: sample=1, fallbacks=0, missing_horizons=[], gap_score=42.3
- Macro Event / NVDA: sample=2, fallbacks=0, missing_horizons=[], gap_score=42.0
- Earnings / AAPL: sample=1, fallbacks=0, missing_horizons=[], gap_score=41.88
- Earnings / AMD: sample=1, fallbacks=0, missing_horizons=[], gap_score=41.88
- Regulatory Approval / AMGN: sample=1, fallbacks=0, missing_horizons=[], gap_score=41.6
- Regulatory Approval / NVO: sample=1, fallbacks=0, missing_horizons=[], gap_score=41.6
- Legal/Regulatory / AMZN: sample=1, fallbacks=0, missing_horizons=[], gap_score=41.32
- Legal/Regulatory / GOOGL: sample=1, fallbacks=0, missing_horizons=[], gap_score=41.32

## Sparse Related Slices
- Capital Expenditure / ORCL / Sector Peer: sample=11, fallbacks=55, missing_horizons=[], gap_score=173.93
- Legal/Regulatory / GOOGL / Sector Peer: sample=10, fallbacks=50, missing_horizons=[], gap_score=160.14
- Partnership / TSM / Supplier: sample=8, fallbacks=40, missing_horizons=[], gap_score=132.24
- Capital Expenditure / AMZN / Competitor: sample=8, fallbacks=40, missing_horizons=[], gap_score=131.68
- Partnership / MSFT / Customer: sample=8, fallbacks=40, missing_horizons=[], gap_score=131.28
- Legal/Regulatory / META / Sector Peer: sample=8, fallbacks=40, missing_horizons=[], gap_score=130.64
- Partnership / AVGO / Sector Peer: sample=8, fallbacks=40, missing_horizons=[], gap_score=129.84
- Product Launch / GOOGL / Competitor: sample=6, fallbacks=30, missing_horizons=[], gap_score=103.7
- Product Launch / TSM / Supplier: sample=5, fallbacks=25, missing_horizons=[], gap_score=89.35
- Capital Expenditure / GOOGL / Competitor: sample=5, fallbacks=25, missing_horizons=[], gap_score=87.43

## Sparse Relationship Slices
- Macro Event / Competitor: sample=1, missing_horizons=[], gap_score=36.65
- Macro Event / Supplier: sample=2, missing_horizons=[], gap_score=36.0
- Earnings / Supplier: sample=2, missing_horizons=[], gap_score=35.44
- Supply Disruption / Supply Chain Dependency: sample=1, missing_horizons=[], gap_score=35.18
- Legal/Regulatory / Supplier: sample=2, missing_horizons=[], gap_score=35.16
- Product Launch / Partner: sample=1, missing_horizons=[], gap_score=35.11
- Legal/Regulatory / Regulatory Peer: sample=1, missing_horizons=[], gap_score=34.9
- Capital Expenditure / Supplier: sample=2, missing_horizons=[], gap_score=34.32
- Supply Disruption / Customer: sample=2, missing_horizons=[], gap_score=34.04
- Capital Expenditure / Customer: sample=2, missing_horizons=[], gap_score=33.48

## Missing Price History
- No current price-history gaps detected for referenced tickers.
