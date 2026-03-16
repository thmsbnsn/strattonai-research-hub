# Coverage Audit

## Event Coverage
- Capital Expenditure: 189 events
- Earnings: 201 events
- Legal/Regulatory: 219 events
- Macro Event: 1117 events
- Partnership: 15 events
- Product Launch: 395 events
- Regulatory Approval: 37 events
- Supply Disruption: 144 events

## Source Coverage
- financial_news_local: 2235 events
- historical_backfill: 30 events
- historical_backfill_wave2: 8 events
- historical_backfill_wave3: 3 events
- historical_backfill_wave4: 2 events
- manual_seed: 5 events
- sec_filing: 34 events

## Weak Signal Categories
- Product Launch: high=12, moderate=11, low=292, high_ratio=3.81%, gap_score=45.23
- Legal/Regulatory: high=9, moderate=14, low=237, high_ratio=3.46%, gap_score=42.41
- Earnings: high=1, moderate=19, low=75, high_ratio=1.05%, gap_score=36.94

## Top Gap Candidates
- #1 Need broader price history for TTM (gap_score=911.0)
  Recommendation: Extend local price history for TTM to at least 40 trading days so its study slices remain usable.
  Rationale: TTM has 0 price rows, appears as primary 287 times and related 0 times.
- #2 Need 1 more Capital Expenditure examples for ORCL related slices (gap_score=203.43)
  Recommendation: Target Capital Expenditure examples that attach ORCL as a Sector Peer related company.
  Rationale: Capital Expenditure related slice for ORCL / Sector Peer has sample 7, missing horizons [], fallback usage 65, signal usage 65.
- #3 Need 1 more Legal/Regulatory examples for GOOGL related slices (gap_score=189.64)
  Recommendation: Target Legal/Regulatory examples that attach GOOGL as a Sector Peer related company.
  Rationale: Legal/Regulatory related slice for GOOGL / Sector Peer has sample 5, missing horizons [], fallback usage 60, signal usage 60.
- #4 Need 1 more Partnership examples for TSM related slices (gap_score=176.49)
  Recommendation: Target Partnership examples that attach TSM as a Supplier related company.
  Rationale: Partnership related slice for TSM / Supplier has sample 7, missing horizons [], fallback usage 55, signal usage 55.
- #5 Need 1 more Partnership examples for MSFT related slices (gap_score=175.53)
  Recommendation: Target Partnership examples that attach MSFT as a Customer related company.
  Rationale: Partnership related slice for MSFT / Customer has sample 7, missing horizons [], fallback usage 55, signal usage 55.
- #6 Need 1 more Partnership examples for AVGO related slices (gap_score=174.09)
  Recommendation: Target Partnership examples that attach AVGO as a Sector Peer related company.
  Rationale: Partnership related slice for AVGO / Sector Peer has sample 7, missing horizons [], fallback usage 55, signal usage 55.
- #7 Need 1 more Capital Expenditure examples for AMZN related slices (gap_score=161.18)
  Recommendation: Target Capital Expenditure examples that attach AMZN as a Competitor related company.
  Rationale: Capital Expenditure related slice for AMZN / Competitor has sample 24, missing horizons [], fallback usage 50, signal usage 50.
- #8 Need 1 more Legal/Regulatory examples for META related slices (gap_score=160.14)
  Recommendation: Target Legal/Regulatory examples that attach META as a Sector Peer related company.
  Rationale: Legal/Regulatory related slice for META / Sector Peer has sample 6, missing horizons [], fallback usage 50, signal usage 50.
- #9 Need 1 more Product Launch examples for GOOGL related slices (gap_score=147.95)
  Recommendation: Target Product Launch examples that attach GOOGL as a Competitor related company.
  Rationale: Product Launch related slice for GOOGL / Competitor has sample 56, missing horizons [], fallback usage 45, signal usage 45.
- #10 Need 1 more Product Launch examples for TSM related slices (gap_score=138.1)
  Recommendation: Target Product Launch examples that attach TSM as a Supplier related company.
  Rationale: Product Launch related slice for TSM / Supplier has sample 4, missing horizons [], fallback usage 40, signal usage 40.
- #11 Need 1 more Product Launch examples for AMD related slices (gap_score=122.95)
  Recommendation: Target Product Launch examples that attach AMD as a Competitor related company.
  Rationale: Product Launch related slice for AMD / Competitor has sample 4, missing horizons [], fallback usage 35, signal usage 35.
- #12 Need 1 more Capital Expenditure examples for GOOGL related slices (gap_score=116.93)
  Recommendation: Target Capital Expenditure examples that attach GOOGL as a Competitor related company.
  Rationale: Capital Expenditure related slice for GOOGL / Competitor has sample 22, missing horizons [], fallback usage 35, signal usage 35.

## Sparse Primary Slices
- Legal/Regulatory / META: sample=1, fallbacks=4, missing_horizons=['10D', '20D'], gap_score=61.32
- Macro Event / TTM: sample=0, fallbacks=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=59.0
- Product Launch / TTM: sample=0, fallbacks=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=58.3
- Earnings / TTM: sample=0, fallbacks=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=57.88
- Regulatory Approval / TTM: sample=0, fallbacks=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=57.6
- Legal/Regulatory / TTM: sample=0, fallbacks=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=57.32
- Supply Disruption / TTM: sample=0, fallbacks=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=56.76
- Capital Expenditure / TTM: sample=0, fallbacks=0, missing_horizons=['1D', '3D', '5D', '10D', '20D'], gap_score=55.64
- Earnings / LLY: sample=1, fallbacks=2, missing_horizons=['20D'], gap_score=53.88
- Supply Disruption / LLY: sample=1, fallbacks=2, missing_horizons=['10D', '20D'], gap_score=51.76

## Sparse Related Slices
- Capital Expenditure / ORCL / Sector Peer: sample=7, fallbacks=65, missing_horizons=[], gap_score=203.43
- Legal/Regulatory / GOOGL / Sector Peer: sample=5, fallbacks=60, missing_horizons=[], gap_score=189.64
- Partnership / TSM / Supplier: sample=7, fallbacks=55, missing_horizons=[], gap_score=176.49
- Partnership / MSFT / Customer: sample=7, fallbacks=55, missing_horizons=[], gap_score=175.53
- Partnership / AVGO / Sector Peer: sample=7, fallbacks=55, missing_horizons=[], gap_score=174.09
- Capital Expenditure / AMZN / Competitor: sample=24, fallbacks=50, missing_horizons=[], gap_score=161.18
- Legal/Regulatory / META / Sector Peer: sample=6, fallbacks=50, missing_horizons=[], gap_score=160.14
- Product Launch / GOOGL / Competitor: sample=56, fallbacks=45, missing_horizons=[], gap_score=147.95
- Product Launch / TSM / Supplier: sample=4, fallbacks=40, missing_horizons=[], gap_score=138.1
- Product Launch / AMD / Competitor: sample=4, fallbacks=35, missing_horizons=[], gap_score=122.95

## Sparse Relationship Slices
- Product Launch / Customer: sample=3, missing_horizons=[], gap_score=45.81
- Regulatory Approval / Sector Peer: sample=1, missing_horizons=[], gap_score=43.2
- Partnership / Partner: sample=2, missing_horizons=[], gap_score=41.92
- Partnership / Competitor: sample=1, missing_horizons=[], gap_score=41.11
- Legal/Regulatory / Supplier: sample=1, missing_horizons=[], gap_score=39.16
- Product Launch / Partner: sample=1, missing_horizons=[], gap_score=35.11
- Macro Event / Supplier: sample=3, missing_horizons=[], gap_score=35.0
- Supply Disruption / Customer: sample=2, missing_horizons=[], gap_score=34.04
- Capital Expenditure / Customer: sample=2, missing_horizons=[], gap_score=33.48
- Regulatory Approval / Regulatory Peer: sample=5, missing_horizons=[], gap_score=16.04

## Missing Price History
- TTM: available_days=0, required_days=40, gap_score=911.0
