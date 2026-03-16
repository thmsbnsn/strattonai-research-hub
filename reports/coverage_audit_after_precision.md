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
- Legal/Regulatory: high=0, moderate=26, low=209, high_ratio=0.00%, gap_score=42.16
- Supply Disruption: high=0, moderate=10, low=95, high_ratio=0.00%, gap_score=37.2
- Earnings: high=0, moderate=28, low=67, high_ratio=0.00%, gap_score=36.88
- Regulatory Approval: high=0, moderate=24, low=51, high_ratio=0.00%, gap_score=36.04

## Top Gap Candidates
- #1 Need 1 more Capital Expenditure examples for ORCL related slices (gap_score=188.68)
  Recommendation: Target Capital Expenditure examples that attach ORCL as a Sector Peer related company.
  Rationale: Capital Expenditure related slice for ORCL / Sector Peer has sample 12, missing horizons [], fallback usage 60, signal usage 60.
- #2 Need 1 more Legal/Regulatory examples for GOOGL related slices (gap_score=174.89)
  Recommendation: Target Legal/Regulatory examples that attach GOOGL as a Sector Peer related company.
  Rationale: Legal/Regulatory related slice for GOOGL / Sector Peer has sample 11, missing horizons [], fallback usage 55, signal usage 55.
- #3 Need 1 more Partnership examples for TSM related slices (gap_score=146.99)
  Recommendation: Target Partnership examples that attach TSM as a Supplier related company.
  Rationale: Partnership related slice for TSM / Supplier has sample 9, missing horizons [], fallback usage 45, signal usage 45.
- #4 Need 1 more Capital Expenditure examples for AMZN related slices (gap_score=146.43)
  Recommendation: Target Capital Expenditure examples that attach AMZN as a Competitor related company.
  Rationale: Capital Expenditure related slice for AMZN / Competitor has sample 9, missing horizons [], fallback usage 45, signal usage 45.
- #5 Need 1 more Partnership examples for MSFT related slices (gap_score=146.03)
  Recommendation: Target Partnership examples that attach MSFT as a Customer related company.
  Rationale: Partnership related slice for MSFT / Customer has sample 9, missing horizons [], fallback usage 45, signal usage 45.
- #6 Need 1 more Legal/Regulatory examples for META related slices (gap_score=145.39)
  Recommendation: Target Legal/Regulatory examples that attach META as a Sector Peer related company.
  Rationale: Legal/Regulatory related slice for META / Sector Peer has sample 9, missing horizons [], fallback usage 45, signal usage 45.
- #7 Need 1 more Partnership examples for AVGO related slices (gap_score=144.59)
  Recommendation: Target Partnership examples that attach AVGO as a Sector Peer related company.
  Rationale: Partnership related slice for AVGO / Sector Peer has sample 9, missing horizons [], fallback usage 45, signal usage 45.
- #8 Need 1 more Product Launch examples for GOOGL related slices (gap_score=118.45)
  Recommendation: Target Product Launch examples that attach GOOGL as a Competitor related company.
  Rationale: Product Launch related slice for GOOGL / Competitor has sample 7, missing horizons [], fallback usage 35, signal usage 35.
- #9 Need 1 more Product Launch examples for TSM related slices (gap_score=104.1)
  Recommendation: Target Product Launch examples that attach TSM as a Supplier related company.
  Rationale: Product Launch related slice for TSM / Supplier has sample 6, missing horizons [], fallback usage 30, signal usage 30.
- #10 Need 1 more Capital Expenditure examples for GOOGL related slices (gap_score=102.18)
  Recommendation: Target Capital Expenditure examples that attach GOOGL as a Competitor related company.
  Rationale: Capital Expenditure related slice for GOOGL / Competitor has sample 6, missing horizons [], fallback usage 30, signal usage 30.
- #11 Need 1 more Product Launch examples for AMD related slices (gap_score=88.95)
  Recommendation: Target Product Launch examples that attach AMD as a Competitor related company.
  Rationale: Product Launch related slice for AMD / Competitor has sample 5, missing horizons [], fallback usage 25, signal usage 25.
- #12 Need 1 more Product Launch examples for MSFT related slices (gap_score=88.39)
  Recommendation: Target Product Launch examples that attach MSFT as a Customer related company.
  Rationale: Product Launch related slice for MSFT / Customer has sample 5, missing horizons [], fallback usage 25, signal usage 25.

## Sparse Primary Slices
- Product Launch / LLY: sample=1, fallbacks=0, missing_horizons=[], gap_score=42.3
- Product Launch / TSLA: sample=1, fallbacks=0, missing_horizons=[], gap_score=42.3
- Macro Event / AAPL: sample=2, fallbacks=0, missing_horizons=[], gap_score=42.0
- Earnings / AAPL: sample=1, fallbacks=0, missing_horizons=[], gap_score=41.88
- Earnings / AMD: sample=1, fallbacks=0, missing_horizons=[], gap_score=41.88
- Regulatory Approval / AMGN: sample=1, fallbacks=0, missing_horizons=[], gap_score=41.6
- Regulatory Approval / NVO: sample=1, fallbacks=0, missing_horizons=[], gap_score=41.6
- Legal/Regulatory / AMZN: sample=1, fallbacks=0, missing_horizons=[], gap_score=41.32
- Legal/Regulatory / GOOGL: sample=1, fallbacks=0, missing_horizons=[], gap_score=41.32
- Product Launch / AAPL: sample=2, fallbacks=0, missing_horizons=[], gap_score=41.3

## Sparse Related Slices
- Capital Expenditure / ORCL / Sector Peer: sample=12, fallbacks=60, missing_horizons=[], gap_score=188.68
- Legal/Regulatory / GOOGL / Sector Peer: sample=11, fallbacks=55, missing_horizons=[], gap_score=174.89
- Partnership / TSM / Supplier: sample=9, fallbacks=45, missing_horizons=[], gap_score=146.99
- Capital Expenditure / AMZN / Competitor: sample=9, fallbacks=45, missing_horizons=[], gap_score=146.43
- Partnership / MSFT / Customer: sample=9, fallbacks=45, missing_horizons=[], gap_score=146.03
- Legal/Regulatory / META / Sector Peer: sample=9, fallbacks=45, missing_horizons=[], gap_score=145.39
- Partnership / AVGO / Sector Peer: sample=9, fallbacks=45, missing_horizons=[], gap_score=144.59
- Product Launch / GOOGL / Competitor: sample=7, fallbacks=35, missing_horizons=[], gap_score=118.45
- Product Launch / TSM / Supplier: sample=6, fallbacks=30, missing_horizons=[], gap_score=104.1
- Capital Expenditure / GOOGL / Competitor: sample=6, fallbacks=30, missing_horizons=[], gap_score=102.18

## Sparse Relationship Slices
- Macro Event / Competitor: sample=1, missing_horizons=[], gap_score=36.65
- Earnings / Supplier: sample=2, missing_horizons=[], gap_score=35.44
- Supply Disruption / Supply Chain Dependency: sample=1, missing_horizons=[], gap_score=35.18
- Legal/Regulatory / Supplier: sample=2, missing_horizons=[], gap_score=35.16
- Product Launch / Partner: sample=1, missing_horizons=[], gap_score=35.11
- Macro Event / Supplier: sample=3, missing_horizons=[], gap_score=35.0
- Legal/Regulatory / Regulatory Peer: sample=1, missing_horizons=[], gap_score=34.9
- Capital Expenditure / Supplier: sample=2, missing_horizons=[], gap_score=34.32
- Supply Disruption / Customer: sample=2, missing_horizons=[], gap_score=34.04
- Capital Expenditure / Customer: sample=2, missing_horizons=[], gap_score=33.48

## Missing Price History
- No current price-history gaps detected for referenced tickers.
