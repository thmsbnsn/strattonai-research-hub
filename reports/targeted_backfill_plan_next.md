# Targeted Backfill Plan

## Ranked Targets
- #1 Capital Expenditure / ORCL / Sector Peer (gap_size=1, source=sec-filings, planner_score=203.24)
  Why: Capital Expenditure remains weak in the audit and this slice is repeatedly used by current signals. Capital Expenditure related slice for ORCL / Sector Peer has sample 12, missing horizons [], fallback usage 60, signal usage 60.
  Needed: desired sample 13 from current 12
- #2 Legal/Regulatory / GOOGL / Sector Peer (gap_size=1, source=sec-filings, planner_score=202.37)
  Why: Legal/Regulatory remains weak in the audit and this slice is repeatedly used by current signals. Legal/Regulatory related slice for GOOGL / Sector Peer has sample 11, missing horizons [], fallback usage 55, signal usage 55.
  Needed: desired sample 12 from current 11
- #3 Legal/Regulatory / META / Sector Peer (gap_size=1, source=sec-filings, planner_score=171.83)
  Why: Legal/Regulatory remains weak in the audit and this slice is repeatedly used by current signals. Legal/Regulatory related slice for META / Sector Peer has sample 9, missing horizons [], fallback usage 45, signal usage 45.
  Needed: desired sample 10 from current 9
- #4 Partnership / TSM / Supplier (gap_size=1, source=sec-filings, planner_score=163.15)
  Why: Partnership remains weak in the audit and this slice is repeatedly used by current signals. Partnership related slice for TSM / Supplier has sample 9, missing horizons [], fallback usage 45, signal usage 45.
  Needed: desired sample 10 from current 9
- #5 Partnership / MSFT / Customer (gap_size=1, source=sec-filings, planner_score=162.67)
  Why: Partnership remains weak in the audit and this slice is repeatedly used by current signals. Partnership related slice for MSFT / Customer has sample 9, missing horizons [], fallback usage 45, signal usage 45.
  Needed: desired sample 10 from current 9
- #6 Capital Expenditure / AMZN / Competitor (gap_size=1, source=sec-filings, planner_score=161.31)
  Why: Capital Expenditure remains weak in the audit and this slice is repeatedly used by current signals. Capital Expenditure related slice for AMZN / Competitor has sample 9, missing horizons [], fallback usage 45, signal usage 45.
  Needed: desired sample 10 from current 9
- #7 Partnership / AVGO / Sector Peer (gap_size=1, source=sec-filings, planner_score=159.63)
  Why: Partnership remains weak in the audit and this slice is repeatedly used by current signals. Partnership related slice for AVGO / Sector Peer has sample 9, missing horizons [], fallback usage 45, signal usage 45.
  Needed: desired sample 10 from current 9
- #8 Product Launch / GOOGL / Competitor (gap_size=1, source=market-events, planner_score=135.09)
  Why: Product Launch remains weak in the audit and this slice is repeatedly used by current signals. Product Launch related slice for GOOGL / Competitor has sample 7, missing horizons [], fallback usage 35, signal usage 35.
  Needed: desired sample 8 from current 7
- #9 Product Launch / TSM / Supplier (gap_size=1, source=market-events, planner_score=120.66)
  Why: Product Launch remains weak in the audit and this slice is repeatedly used by current signals. Product Launch related slice for TSM / Supplier has sample 6, missing horizons [], fallback usage 30, signal usage 30.
  Needed: desired sample 7 from current 6
- #10 Capital Expenditure / GOOGL / Competitor (gap_size=1, source=sec-filings, planner_score=117.62)
  Why: Capital Expenditure remains weak in the audit and this slice is repeatedly used by current signals. Capital Expenditure related slice for GOOGL / Competitor has sample 6, missing horizons [], fallback usage 30, signal usage 30.
  Needed: desired sample 7 from current 6
- #11 Product Launch / MSFT / Customer (gap_size=1, source=market-events, planner_score=105.43)
  Why: Product Launch remains weak in the audit and this slice is repeatedly used by current signals. Product Launch related slice for MSFT / Customer has sample 5, missing horizons [], fallback usage 25, signal usage 25.
  Needed: desired sample 6 from current 5
- #12 Product Launch / AMD / Competitor (gap_size=1, source=market-events, planner_score=105.35)
  Why: Product Launch remains weak in the audit and this slice is repeatedly used by current signals. Product Launch related slice for AMD / Competitor has sample 5, missing horizons [], fallback usage 25, signal usage 25.
  Needed: desired sample 6 from current 5

## Collection Groups
- market-events::Product Launch: 4 targets, total gap size 4. Collect this set together because all items share Product Launch and are best sourced through market-events.
- sec-filings::Capital Expenditure: 3 targets, total gap size 3. Collect this set together because all items share Capital Expenditure and are best sourced through sec-filings.
- sec-filings::Legal/Regulatory: 2 targets, total gap size 2. Collect this set together because all items share Legal/Regulatory and are best sourced through sec-filings.
- sec-filings::Partnership: 3 targets, total gap size 3. Collect this set together because all items share Partnership and are best sourced through sec-filings.
