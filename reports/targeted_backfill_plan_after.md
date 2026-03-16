# Targeted Backfill Plan

## Ranked Targets
- #1 Capital Expenditure / ORCL / Sector Peer (gap_size=1, source=sec-filings, planner_score=188.49)
  Why: Capital Expenditure remains weak in the audit and this slice is repeatedly used by current signals. Capital Expenditure related slice for ORCL / Sector Peer has sample 11, missing horizons [], fallback usage 55, signal usage 55.
  Needed: desired sample 12 from current 11
- #2 Legal/Regulatory / GOOGL / Sector Peer (gap_size=1, source=sec-filings, planner_score=187.57)
  Why: Legal/Regulatory remains weak in the audit and this slice is repeatedly used by current signals. Legal/Regulatory related slice for GOOGL / Sector Peer has sample 10, missing horizons [], fallback usage 50, signal usage 50.
  Needed: desired sample 11 from current 10
- #3 Partnership / TSM / Supplier (gap_size=1, source=sec-filings, planner_score=157.86)
  Why: Partnership remains weak in the audit and this slice is repeatedly used by current signals. Partnership related slice for TSM / Supplier has sample 8, missing horizons [], fallback usage 40, signal usage 40.
  Needed: desired sample 9 from current 8
- #4 Partnership / MSFT / Customer (gap_size=1, source=sec-filings, planner_score=157.38)
  Why: Partnership remains weak in the audit and this slice is repeatedly used by current signals. Partnership related slice for MSFT / Customer has sample 8, missing horizons [], fallback usage 40, signal usage 40.
  Needed: desired sample 9 from current 8
- #5 Legal/Regulatory / META / Sector Peer (gap_size=1, source=sec-filings, planner_score=157.03)
  Why: Legal/Regulatory remains weak in the audit and this slice is repeatedly used by current signals. Legal/Regulatory related slice for META / Sector Peer has sample 8, missing horizons [], fallback usage 40, signal usage 40.
  Needed: desired sample 9 from current 8
- #6 Partnership / AVGO / Sector Peer (gap_size=1, source=sec-filings, planner_score=154.34)
  Why: Partnership remains weak in the audit and this slice is repeatedly used by current signals. Partnership related slice for AVGO / Sector Peer has sample 8, missing horizons [], fallback usage 40, signal usage 40.
  Needed: desired sample 9 from current 8
- #7 Capital Expenditure / AMZN / Competitor (gap_size=1, source=sec-filings, planner_score=146.56)
  Why: Capital Expenditure remains weak in the audit and this slice is repeatedly used by current signals. Capital Expenditure related slice for AMZN / Competitor has sample 8, missing horizons [], fallback usage 40, signal usage 40.
  Needed: desired sample 9 from current 8
- #8 Product Launch / GOOGL / Competitor (gap_size=1, source=market-events, planner_score=120.34)
  Why: Product Launch remains weak in the audit and this slice is repeatedly used by current signals. Product Launch related slice for GOOGL / Competitor has sample 6, missing horizons [], fallback usage 30, signal usage 30.
  Needed: desired sample 7 from current 6
- #9 Product Launch / TSM / Supplier (gap_size=1, source=market-events, planner_score=105.91)
  Why: Product Launch remains weak in the audit and this slice is repeatedly used by current signals. Product Launch related slice for TSM / Supplier has sample 5, missing horizons [], fallback usage 25, signal usage 25.
  Needed: desired sample 6 from current 5
- #10 Capital Expenditure / GOOGL / Competitor (gap_size=1, source=sec-filings, planner_score=102.87)
  Why: Capital Expenditure remains weak in the audit and this slice is repeatedly used by current signals. Capital Expenditure related slice for GOOGL / Competitor has sample 5, missing horizons [], fallback usage 25, signal usage 25.
  Needed: desired sample 6 from current 5
- #11 Product Launch / MSFT / Customer (gap_size=1, source=market-events, planner_score=95.18)
  Why: Product Launch remains weak in the audit and this slice is repeatedly used by current signals. Product Launch related slice for MSFT / Customer has sample 4, missing horizons [], fallback usage 20, signal usage 20.
  Needed: desired sample 5 from current 4
- #12 Product Launch / AMD / Competitor (gap_size=1, source=market-events, planner_score=95.1)
  Why: Product Launch remains weak in the audit and this slice is repeatedly used by current signals. Product Launch related slice for AMD / Competitor has sample 4, missing horizons [], fallback usage 20, signal usage 20.
  Needed: desired sample 5 from current 4

## Collection Groups
- market-events::Product Launch: 4 targets, total gap size 4. Collect this set together because all items share Product Launch and are best sourced through market-events.
- sec-filings::Capital Expenditure: 3 targets, total gap size 3. Collect this set together because all items share Capital Expenditure and are best sourced through sec-filings.
- sec-filings::Legal/Regulatory: 2 targets, total gap size 2. Collect this set together because all items share Legal/Regulatory and are best sourced through sec-filings.
- sec-filings::Partnership: 3 targets, total gap size 3. Collect this set together because all items share Partnership and are best sourced through sec-filings.
