# Coverage Audit

## Event Coverage
- Capital Expenditure: 7 events
- Earnings: 6 events
- Legal/Regulatory: 9 events
- Macro Event: 2 events
- Partnership: 7 events
- Product Launch: 7 events
- Regulatory Approval: 5 events
- Supply Disruption: 5 events

## Source Coverage
- historical_backfill: 30 events
- manual_seed: 5 events
- sec_filing: 13 events

## Weak Signal Categories
- Legal/Regulatory: high=0, moderate=0, low=140, high_ratio=0.00%, gap_score=39.4
- Product Launch: high=0, moderate=39, low=96, high_ratio=0.00%, gap_score=38.34
- Partnership: high=0, moderate=20, low=110, high_ratio=0.00%, gap_score=37.2
- Supply Disruption: high=0, moderate=10, low=95, high_ratio=0.00%, gap_score=37.2
- Earnings: high=0, moderate=28, low=67, high_ratio=0.00%, gap_score=36.88
- Macro Event: high=0, moderate=18, low=27, high_ratio=0.00%, gap_score=36.08
- Regulatory Approval: high=0, moderate=24, low=51, high_ratio=0.00%, gap_score=36.04

## Top Gap Candidates
- #1 Need 1 more Legal/Regulatory examples for GOOGL related slices (gap_score=101.14)
  Recommendation: Target Legal/Regulatory examples that attach GOOGL as a Sector Peer related company.
  Rationale: Legal/Regulatory related slice for GOOGL / Sector Peer has sample 6, missing horizons [], fallback usage 30, signal usage 30.
- #2 Need 1 more Capital Expenditure examples for ORCL related slices (gap_score=100.18)
  Recommendation: Target Capital Expenditure examples that attach ORCL as a Sector Peer related company.
  Rationale: Capital Expenditure related slice for ORCL / Sector Peer has sample 6, missing horizons [], fallback usage 30, signal usage 30.
- #3 Need 1 more Legal/Regulatory examples for META related slices (gap_score=86.39)
  Recommendation: Target Legal/Regulatory examples that attach META as a Sector Peer related company.
  Rationale: Legal/Regulatory related slice for META / Sector Peer has sample 5, missing horizons [], fallback usage 25, signal usage 25.
- #4 Need 2 more Regulatory Approval examples for NVO related slices (gap_score=68.05)
  Recommendation: Target Regulatory Approval examples that attach NVO as a Competitor related company.
  Rationale: Regulatory Approval related slice for NVO / Competitor has sample 3, missing horizons [], fallback usage 15, signal usage 15.
- #5 Need 2 more Partnership examples for TSM related slices (gap_score=67.49)
  Recommendation: Target Partnership examples that attach TSM as a Supplier related company.
  Rationale: Partnership related slice for TSM / Supplier has sample 3, missing horizons [], fallback usage 15, signal usage 15.
- #6 Need 2 more Capital Expenditure examples for AMZN related slices (gap_score=66.93)
  Recommendation: Target Capital Expenditure examples that attach AMZN as a Competitor related company.
  Rationale: Capital Expenditure related slice for AMZN / Competitor has sample 3, missing horizons [], fallback usage 15, signal usage 15.
- #7 Need 2 more Capital Expenditure examples for GOOGL related slices (gap_score=66.93)
  Recommendation: Target Capital Expenditure examples that attach GOOGL as a Competitor related company.
  Rationale: Capital Expenditure related slice for GOOGL / Competitor has sample 3, missing horizons [], fallback usage 15, signal usage 15.
- #8 Need 2 more Partnership examples for MSFT related slices (gap_score=66.53)
  Recommendation: Target Partnership examples that attach MSFT as a Customer related company.
  Rationale: Partnership related slice for MSFT / Customer has sample 3, missing horizons [], fallback usage 15, signal usage 15.
- #9 Need 2 more Legal/Regulatory examples for AAPL related slices (gap_score=65.89)
  Recommendation: Target Legal/Regulatory examples that attach AAPL as a Sector Peer related company.
  Rationale: Legal/Regulatory related slice for AAPL / Sector Peer has sample 3, missing horizons [], fallback usage 15, signal usage 15.
- #10 Need 2 more Partnership examples for AVGO related slices (gap_score=65.09)
  Recommendation: Target Partnership examples that attach AVGO as a Sector Peer related company.
  Rationale: Partnership related slice for AVGO / Sector Peer has sample 3, missing horizons [], fallback usage 15, signal usage 15.
- #11 Need 3 more Product Launch examples for QCOM related slices (gap_score=58.6)
  Recommendation: Target Product Launch examples that attach QCOM as a Supplier related company.
  Rationale: Product Launch related slice for QCOM / Supplier has sample 2, missing horizons [], fallback usage 10, signal usage 10.
- #12 Need 3 more Product Launch examples for TSM related slices (gap_score=58.6)
  Recommendation: Target Product Launch examples that attach TSM as a Supplier related company.
  Rationale: Product Launch related slice for TSM / Supplier has sample 2, missing horizons [], fallback usage 10, signal usage 10.

## Sparse Primary Slices
- Macro Event / MSFT: sample=1, fallbacks=0, missing_horizons=[], gap_score=43.0
- Macro Event / NVDA: sample=1, fallbacks=0, missing_horizons=[], gap_score=43.0
- Product Launch / AAPL: sample=1, fallbacks=0, missing_horizons=[], gap_score=42.3
- Product Launch / LLY: sample=1, fallbacks=0, missing_horizons=[], gap_score=42.3
- Product Launch / MSFT: sample=1, fallbacks=0, missing_horizons=[], gap_score=42.3
- Product Launch / QCOM: sample=1, fallbacks=0, missing_horizons=[], gap_score=42.3
- Product Launch / TSLA: sample=1, fallbacks=0, missing_horizons=[], gap_score=42.3
- Earnings / AAPL: sample=1, fallbacks=0, missing_horizons=[], gap_score=41.88
- Earnings / AMD: sample=1, fallbacks=0, missing_horizons=[], gap_score=41.88
- Regulatory Approval / AMGN: sample=1, fallbacks=0, missing_horizons=[], gap_score=41.6

## Sparse Related Slices
- Legal/Regulatory / GOOGL / Sector Peer: sample=6, fallbacks=30, missing_horizons=[], gap_score=101.14
- Capital Expenditure / ORCL / Sector Peer: sample=6, fallbacks=30, missing_horizons=[], gap_score=100.18
- Legal/Regulatory / META / Sector Peer: sample=5, fallbacks=25, missing_horizons=[], gap_score=86.39
- Regulatory Approval / NVO / Competitor: sample=3, fallbacks=15, missing_horizons=[], gap_score=68.05
- Partnership / TSM / Supplier: sample=3, fallbacks=15, missing_horizons=[], gap_score=67.49
- Capital Expenditure / AMZN / Competitor: sample=3, fallbacks=15, missing_horizons=[], gap_score=66.93
- Capital Expenditure / GOOGL / Competitor: sample=3, fallbacks=15, missing_horizons=[], gap_score=66.93
- Partnership / MSFT / Customer: sample=3, fallbacks=15, missing_horizons=[], gap_score=66.53
- Legal/Regulatory / AAPL / Sector Peer: sample=3, fallbacks=15, missing_horizons=[], gap_score=65.89
- Partnership / AVGO / Sector Peer: sample=3, fallbacks=15, missing_horizons=[], gap_score=65.09

## Sparse Relationship Slices
- Macro Event / Supplier: sample=1, missing_horizons=[], gap_score=37.0
- Earnings / Supplier: sample=2, missing_horizons=[], gap_score=35.44
- Capital Expenditure / Supplier: sample=1, missing_horizons=[], gap_score=35.32
- Supply Disruption / Supply Chain Dependency: sample=1, missing_horizons=[], gap_score=35.18
- Legal/Regulatory / Supplier: sample=2, missing_horizons=[], gap_score=35.16
- Product Launch / Partner: sample=1, missing_horizons=[], gap_score=35.11
- Legal/Regulatory / Regulatory Peer: sample=1, missing_horizons=[], gap_score=34.9
- Legal/Regulatory / Competitor: sample=2, missing_horizons=[], gap_score=34.81
- Supply Disruption / Customer: sample=2, missing_horizons=[], gap_score=34.04
- Product Launch / Sector Peer: sample=2, missing_horizons=[], gap_score=33.55

## Missing Price History
- No current price-history gaps detected for referenced tickers.
