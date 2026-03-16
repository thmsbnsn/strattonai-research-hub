# Coverage Audit

## Event Coverage
- Capital Expenditure: 169 events
- Earnings: 175 events
- Legal/Regulatory: 190 events
- Macro Event: 971 events
- Partnership: 13 events
- Product Launch: 347 events
- Regulatory Approval: 31 events
- Supply Disruption: 128 events

## Source Coverage
- financial_news_local: 1948 events
- historical_backfill: 30 events
- historical_backfill_wave2: 8 events
- historical_backfill_wave3: 3 events
- manual_seed: 5 events
- sec_filing: 30 events

## Weak Signal Categories
- Product Launch: high=10, moderate=7, low=248, high_ratio=3.77%, gap_score=43.48
- Legal/Regulatory: high=8, moderate=11, low=216, high_ratio=3.40%, gap_score=41.59
- Partnership: high=12, moderate=113, low=150, high_ratio=4.36%, gap_score=37.71
- Earnings: high=1, moderate=19, low=75, high_ratio=1.05%, gap_score=36.94

## Top Gap Candidates
- #1 Need 1 more Capital Expenditure examples for ORCL related slices (gap_score=188.68)
  Recommendation: Target Capital Expenditure examples that attach ORCL as a Sector Peer related company.
  Rationale: Capital Expenditure related slice for ORCL / Sector Peer has sample 6, missing horizons [], fallback usage 60, signal usage 60.
- #2 Need 1 more Legal/Regulatory examples for GOOGL related slices (gap_score=179.39)
  Recommendation: Target Legal/Regulatory examples that attach GOOGL as a Sector Peer related company.
  Rationale: Legal/Regulatory related slice for GOOGL / Sector Peer has sample 4, missing horizons [], fallback usage 55, signal usage 55.
- #3 Need 1 more Partnership examples for TSM related slices (gap_score=146.99)
  Recommendation: Target Partnership examples that attach TSM as a Supplier related company.
  Rationale: Partnership related slice for TSM / Supplier has sample 5, missing horizons [], fallback usage 45, signal usage 45.
- #4 Need 1 more Capital Expenditure examples for AMZN related slices (gap_score=146.43)
  Recommendation: Target Capital Expenditure examples that attach AMZN as a Competitor related company.
  Rationale: Capital Expenditure related slice for AMZN / Competitor has sample 23, missing horizons [], fallback usage 45, signal usage 45.
- #5 Need 1 more Partnership examples for MSFT related slices (gap_score=146.03)
  Recommendation: Target Partnership examples that attach MSFT as a Customer related company.
  Rationale: Partnership related slice for MSFT / Customer has sample 5, missing horizons [], fallback usage 45, signal usage 45.
- #6 Need 1 more Legal/Regulatory examples for META related slices (gap_score=145.39)
  Recommendation: Target Legal/Regulatory examples that attach META as a Sector Peer related company.
  Rationale: Legal/Regulatory related slice for META / Sector Peer has sample 5, missing horizons [], fallback usage 45, signal usage 45.
- #7 Need 1 more Partnership examples for AVGO related slices (gap_score=144.59)
  Recommendation: Target Partnership examples that attach AVGO as a Sector Peer related company.
  Rationale: Partnership related slice for AVGO / Sector Peer has sample 5, missing horizons [], fallback usage 45, signal usage 45.
- #8 Need 1 more Product Launch examples for GOOGL related slices (gap_score=118.45)
  Recommendation: Target Product Launch examples that attach GOOGL as a Competitor related company.
  Rationale: Product Launch related slice for GOOGL / Competitor has sample 54, missing horizons [], fallback usage 35, signal usage 35.
- #9 Need 3 more Product Launch examples for TSM related slices (gap_score=117.6)
  Recommendation: Target Product Launch examples that attach TSM as a Supplier related company.
  Rationale: Product Launch related slice for TSM / Supplier has sample 2, missing horizons [], fallback usage 30, signal usage 30.
- #10 Need 3 more Product Launch examples for AMD related slices (gap_score=102.45)
  Recommendation: Target Product Launch examples that attach AMD as a Competitor related company.
  Rationale: Product Launch related slice for AMD / Competitor has sample 2, missing horizons [], fallback usage 25, signal usage 25.
- #11 Need 1 more Capital Expenditure examples for GOOGL related slices (gap_score=102.18)
  Recommendation: Target Capital Expenditure examples that attach GOOGL as a Competitor related company.
  Rationale: Capital Expenditure related slice for GOOGL / Competitor has sample 21, missing horizons [], fallback usage 30, signal usage 30.
- #12 Need 3 more Product Launch examples for MSFT related slices (gap_score=101.89)
  Recommendation: Target Product Launch examples that attach MSFT as a Customer related company.
  Rationale: Product Launch related slice for MSFT / Customer has sample 2, missing horizons [], fallback usage 25, signal usage 25.

## Sparse Primary Slices
- Legal/Regulatory / META: sample=1, fallbacks=4, missing_horizons=['10D', '20D'], gap_score=61.32
- Earnings / LLY: sample=1, fallbacks=2, missing_horizons=['20D'], gap_score=53.88
- Supply Disruption / LLY: sample=1, fallbacks=2, missing_horizons=['10D', '20D'], gap_score=51.76
- Partnership / LLY: sample=1, fallbacks=2, missing_horizons=['10D', '20D'], gap_score=50.92
- Partnership / ORCL: sample=1, fallbacks=2, missing_horizons=['10D', '20D'], gap_score=50.92
- Product Launch / QCOM: sample=1, fallbacks=0, missing_horizons=[], gap_score=50.3
- Partnership / NVDA: sample=3, fallbacks=0, missing_horizons=[], gap_score=49.92
- Regulatory Approval / LLY: sample=1, fallbacks=0, missing_horizons=[], gap_score=49.6
- Product Launch / LLY: sample=1, fallbacks=1, missing_horizons=['20D'], gap_score=47.8
- Regulatory Approval / AMGN: sample=1, fallbacks=1, missing_horizons=['20D'], gap_score=47.1

## Sparse Related Slices
- Capital Expenditure / ORCL / Sector Peer: sample=6, fallbacks=60, missing_horizons=[], gap_score=188.68
- Legal/Regulatory / GOOGL / Sector Peer: sample=4, fallbacks=55, missing_horizons=[], gap_score=179.39
- Partnership / TSM / Supplier: sample=5, fallbacks=45, missing_horizons=[], gap_score=146.99
- Capital Expenditure / AMZN / Competitor: sample=23, fallbacks=45, missing_horizons=[], gap_score=146.43
- Partnership / MSFT / Customer: sample=5, fallbacks=45, missing_horizons=[], gap_score=146.03
- Legal/Regulatory / META / Sector Peer: sample=5, fallbacks=45, missing_horizons=[], gap_score=145.39
- Partnership / AVGO / Sector Peer: sample=5, fallbacks=45, missing_horizons=[], gap_score=144.59
- Product Launch / GOOGL / Competitor: sample=54, fallbacks=35, missing_horizons=[], gap_score=118.45
- Product Launch / TSM / Supplier: sample=2, fallbacks=30, missing_horizons=[], gap_score=117.6
- Product Launch / AMD / Competitor: sample=2, fallbacks=25, missing_horizons=[], gap_score=102.45

## Sparse Relationship Slices
- Partnership / Supplier: sample=5, missing_horizons=[], gap_score=46.46
- Product Launch / Customer: sample=3, missing_horizons=[], gap_score=45.81
- Regulatory Approval / Sector Peer: sample=1, missing_horizons=[], gap_score=43.2
- Partnership / Partner: sample=2, missing_horizons=[], gap_score=41.92
- Partnership / Competitor: sample=1, missing_horizons=[], gap_score=41.11
- Legal/Regulatory / Supplier: sample=1, missing_horizons=[], gap_score=39.16
- Product Launch / Partner: sample=1, missing_horizons=[], gap_score=35.11
- Macro Event / Supplier: sample=3, missing_horizons=[], gap_score=35.0
- Supply Disruption / Customer: sample=2, missing_horizons=[], gap_score=34.04
- Capital Expenditure / Customer: sample=2, missing_horizons=[], gap_score=33.48

## Missing Price History
- No current price-history gaps detected for referenced tickers.
