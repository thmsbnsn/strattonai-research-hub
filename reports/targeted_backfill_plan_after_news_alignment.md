# Targeted Backfill Plan

## Ranked Targets
- #1 Legal/Regulatory / GOOGL / Sector Peer (gap_size=1, source=sec-filings, planner_score=206.73)
  Why: Legal/Regulatory remains weak in the audit and this slice is repeatedly used by current signals. Legal/Regulatory related slice for GOOGL / Sector Peer has sample 4, missing horizons [], fallback usage 55, signal usage 55.
  Needed: desired sample 5 from current 4
- #2 Capital Expenditure / ORCL / Sector Peer (gap_size=1, source=sec-filings, planner_score=203.24)
  Why: Capital Expenditure remains weak in the audit and this slice is repeatedly used by current signals. Capital Expenditure related slice for ORCL / Sector Peer has sample 6, missing horizons [], fallback usage 60, signal usage 60.
  Needed: desired sample 7 from current 6
- #3 Partnership / TSM / Supplier (gap_size=1, source=sec-filings, planner_score=172.58)
  Why: Partnership remains weak in the audit and this slice is repeatedly used by current signals. Partnership related slice for TSM / Supplier has sample 5, missing horizons [], fallback usage 45, signal usage 45.
  Needed: desired sample 6 from current 5
- #4 Partnership / MSFT / Customer (gap_size=1, source=sec-filings, planner_score=172.1)
  Why: Partnership remains weak in the audit and this slice is repeatedly used by current signals. Partnership related slice for MSFT / Customer has sample 5, missing horizons [], fallback usage 45, signal usage 45.
  Needed: desired sample 6 from current 5
- #5 Legal/Regulatory / META / Sector Peer (gap_size=1, source=sec-filings, planner_score=171.69)
  Why: Legal/Regulatory remains weak in the audit and this slice is repeatedly used by current signals. Legal/Regulatory related slice for META / Sector Peer has sample 5, missing horizons [], fallback usage 45, signal usage 45.
  Needed: desired sample 6 from current 5
- #6 Partnership / AVGO / Sector Peer (gap_size=1, source=sec-filings, planner_score=169.06)
  Why: Partnership remains weak in the audit and this slice is repeatedly used by current signals. Partnership related slice for AVGO / Sector Peer has sample 5, missing horizons [], fallback usage 45, signal usage 45.
  Needed: desired sample 6 from current 5
- #7 Capital Expenditure / AMZN / Competitor (gap_size=1, source=sec-filings, planner_score=161.31)
  Why: Capital Expenditure remains weak in the audit and this slice is repeatedly used by current signals. Capital Expenditure related slice for AMZN / Competitor has sample 23, missing horizons [], fallback usage 45, signal usage 45.
  Needed: desired sample 24 from current 23
- #8 Product Launch / GOOGL / Competitor (gap_size=1, source=market-events, planner_score=145.96)
  Why: Product Launch remains weak in the audit and this slice is repeatedly used by current signals. Product Launch related slice for GOOGL / Competitor has sample 54, missing horizons [], fallback usage 35, signal usage 35.
  Needed: desired sample 55 from current 54
- #9 Product Launch / TSM / Supplier (gap_size=3, source=market-events, planner_score=145.03)
  Why: Product Launch remains weak in the audit and this slice is repeatedly used by current signals. Product Launch related slice for TSM / Supplier has sample 2, missing horizons [], fallback usage 30, signal usage 30.
  Needed: desired sample 5 from current 2
- #10 Product Launch / MSFT / Customer (gap_size=3, source=market-events, planner_score=129.8)
  Why: Product Launch remains weak in the audit and this slice is repeatedly used by current signals. Product Launch related slice for MSFT / Customer has sample 2, missing horizons [], fallback usage 25, signal usage 25.
  Needed: desired sample 5 from current 2
- #11 Product Launch / AMD / Competitor (gap_size=3, source=market-events, planner_score=129.72)
  Why: Product Launch remains weak in the audit and this slice is repeatedly used by current signals. Product Launch related slice for AMD / Competitor has sample 2, missing horizons [], fallback usage 25, signal usage 25.
  Needed: desired sample 5 from current 2
- #12 Capital Expenditure / GOOGL / Competitor (gap_size=1, source=sec-filings, planner_score=117.62)
  Why: Capital Expenditure remains weak in the audit and this slice is repeatedly used by current signals. Capital Expenditure related slice for GOOGL / Competitor has sample 21, missing horizons [], fallback usage 30, signal usage 30.
  Needed: desired sample 22 from current 21

## Collection Groups
- market-events::Product Launch: 4 targets, total gap size 10. Collect this set together because all items share Product Launch and are best sourced through market-events.
- sec-filings::Capital Expenditure: 3 targets, total gap size 3. Collect this set together because all items share Capital Expenditure and are best sourced through sec-filings.
- sec-filings::Legal/Regulatory: 2 targets, total gap size 2. Collect this set together because all items share Legal/Regulatory and are best sourced through sec-filings.
- sec-filings::Partnership: 3 targets, total gap size 3. Collect this set together because all items share Partnership and are best sourced through sec-filings.
