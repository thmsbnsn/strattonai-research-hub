# Targeted Backfill Plan

## Ranked Targets
- #1 Unknown / TTM / category (gap_size=40, source=market-events, planner_score=923.2)
  Why: Unknown remains weak in the audit and this slice is repeatedly used by current signals. TTM has 0 price rows, appears as primary 287 times and related 0 times.
  Needed: desired sample 40 from current 0
- #2 Capital Expenditure / ORCL / Sector Peer (gap_size=1, source=sec-filings, planner_score=217.99)
  Why: Capital Expenditure remains weak in the audit and this slice is repeatedly used by current signals. Capital Expenditure related slice for ORCL / Sector Peer has sample 7, missing horizons [], fallback usage 65, signal usage 65.
  Needed: desired sample 8 from current 7
- #3 Legal/Regulatory / GOOGL / Sector Peer (gap_size=1, source=sec-filings, planner_score=217.18)
  Why: Legal/Regulatory remains weak in the audit and this slice is repeatedly used by current signals. Legal/Regulatory related slice for GOOGL / Sector Peer has sample 5, missing horizons [], fallback usage 60, signal usage 60.
  Needed: desired sample 6 from current 5
- #4 Partnership / TSM / Supplier (gap_size=1, source=sec-filings, planner_score=192.65)
  Why: Partnership remains weak in the audit and this slice is repeatedly used by current signals. Partnership related slice for TSM / Supplier has sample 7, missing horizons [], fallback usage 55, signal usage 55.
  Needed: desired sample 8 from current 7
- #5 Partnership / MSFT / Customer (gap_size=1, source=sec-filings, planner_score=192.17)
  Why: Partnership remains weak in the audit and this slice is repeatedly used by current signals. Partnership related slice for MSFT / Customer has sample 7, missing horizons [], fallback usage 55, signal usage 55.
  Needed: desired sample 8 from current 7
- #6 Partnership / AVGO / Sector Peer (gap_size=1, source=sec-filings, planner_score=189.13)
  Why: Partnership remains weak in the audit and this slice is repeatedly used by current signals. Partnership related slice for AVGO / Sector Peer has sample 7, missing horizons [], fallback usage 55, signal usage 55.
  Needed: desired sample 8 from current 7
- #7 Legal/Regulatory / META / Sector Peer (gap_size=1, source=sec-filings, planner_score=186.64)
  Why: Legal/Regulatory remains weak in the audit and this slice is repeatedly used by current signals. Legal/Regulatory related slice for META / Sector Peer has sample 6, missing horizons [], fallback usage 50, signal usage 50.
  Needed: desired sample 7 from current 6
- #8 Capital Expenditure / AMZN / Competitor (gap_size=1, source=sec-filings, planner_score=176.06)
  Why: Capital Expenditure remains weak in the audit and this slice is repeatedly used by current signals. Capital Expenditure related slice for AMZN / Competitor has sample 24, missing horizons [], fallback usage 50, signal usage 50.
  Needed: desired sample 25 from current 24
- #9 Product Launch / GOOGL / Competitor (gap_size=1, source=market-events, planner_score=175.9)
  Why: Product Launch remains weak in the audit and this slice is repeatedly used by current signals. Product Launch related slice for GOOGL / Competitor has sample 56, missing horizons [], fallback usage 45, signal usage 45.
  Needed: desired sample 57 from current 56
- #10 Product Launch / TSM / Supplier (gap_size=1, source=market-events, planner_score=165.97)
  Why: Product Launch remains weak in the audit and this slice is repeatedly used by current signals. Product Launch related slice for TSM / Supplier has sample 4, missing horizons [], fallback usage 40, signal usage 40.
  Needed: desired sample 5 from current 4
- #11 Product Launch / AMD / Competitor (gap_size=1, source=market-events, planner_score=150.66)
  Why: Product Launch remains weak in the audit and this slice is repeatedly used by current signals. Product Launch related slice for AMD / Competitor has sample 4, missing horizons [], fallback usage 35, signal usage 35.
  Needed: desired sample 5 from current 4
- #12 Capital Expenditure / GOOGL / Competitor (gap_size=1, source=sec-filings, planner_score=132.37)
  Why: Capital Expenditure remains weak in the audit and this slice is repeatedly used by current signals. Capital Expenditure related slice for GOOGL / Competitor has sample 22, missing horizons [], fallback usage 35, signal usage 35.
  Needed: desired sample 23 from current 22

## Collection Groups
- market-events::Product Launch: 3 targets, total gap size 3. Collect this set together because all items share Product Launch and are best sourced through market-events.
- market-events::Unknown: 1 targets, total gap size 40. Collect this set together because all items share Unknown and are best sourced through market-events.
- sec-filings::Capital Expenditure: 3 targets, total gap size 3. Collect this set together because all items share Capital Expenditure and are best sourced through sec-filings.
- sec-filings::Legal/Regulatory: 2 targets, total gap size 2. Collect this set together because all items share Legal/Regulatory and are best sourced through sec-filings.
- sec-filings::Partnership: 3 targets, total gap size 3. Collect this set together because all items share Partnership and are best sourced through sec-filings.
