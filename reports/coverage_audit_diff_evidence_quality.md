# Coverage Audit Diff

## Total Events
- Events: 2024 -> 2317 (delta +293)

## Event Counts By Category
- Capital Expenditure: 169 -> 189 (delta +20)
- Earnings: 175 -> 201 (delta +26)
- Legal/Regulatory: 190 -> 219 (delta +29)
- Macro Event: 971 -> 1117 (delta +146)
- Partnership: 13 -> 15 (delta +2)
- Product Launch: 347 -> 395 (delta +48)
- Regulatory Approval: 31 -> 37 (delta +6)
- Supply Disruption: 128 -> 144 (delta +16)

## Macro Event Depth
- Macro Event count: 971 -> 1117

## Focused Related Slice Improvements
- Product Launch::GOOGL::Competitor: min sample 54 -> 56 (delta +2), horizons 5 -> 5
- Product Launch::TSM::Supplier: min sample 2 -> 4 (delta +2), horizons 5 -> 5
- Product Launch::AMD::Competitor: min sample 2 -> 4 (delta +2), horizons 5 -> 5
- Partnership::TSM::Supplier: min sample 5 -> 7 (delta +2), horizons 5 -> 5
- Partnership::MSFT::Customer: min sample 5 -> 7 (delta +2), horizons 5 -> 5
- Partnership::AVGO::Sector Peer: min sample 5 -> 7 (delta +2), horizons 5 -> 5
- Legal/Regulatory::GOOGL::Sector Peer: min sample 4 -> 5 (delta +1), horizons 5 -> 5
- Legal/Regulatory::META::Sector Peer: min sample 5 -> 6 (delta +1), horizons 5 -> 5
- Capital Expenditure::ORCL::Sector Peer: min sample 6 -> 7 (delta +1), horizons 5 -> 5
- Capital Expenditure::AMZN::Competitor: min sample 23 -> 24 (delta +1), horizons 5 -> 5
- Capital Expenditure::GOOGL::Competitor: min sample 21 -> 22 (delta +1), horizons 5 -> 5

## Event Study Rows
- Detailed rows: 1203 -> 1217 (delta +14)
- UI summary rows: 40 -> 40 (delta +0)

## Signals
- Signal count: 1480 -> 1620 (delta +140)
- Confidence bands: High 98 -> 148, Moderate 240 -> 213, Low 1142 -> 1259

## Remaining Weak Slices
- price::TTM: needs 40 more example(s). TTM has 0 price rows, appears as primary 287 times and related 0 times.
- related::Capital Expenditure::ORCL::Sector Peer: needs 1 more example(s). Capital Expenditure related slice for ORCL / Sector Peer has sample 7, missing horizons [], fallback usage 65, signal usage 65.
- related::Legal/Regulatory::GOOGL::Sector Peer: needs 1 more example(s). Legal/Regulatory related slice for GOOGL / Sector Peer has sample 5, missing horizons [], fallback usage 60, signal usage 60.
- related::Partnership::TSM::Supplier: needs 1 more example(s). Partnership related slice for TSM / Supplier has sample 7, missing horizons [], fallback usage 55, signal usage 55.
- related::Partnership::MSFT::Customer: needs 1 more example(s). Partnership related slice for MSFT / Customer has sample 7, missing horizons [], fallback usage 55, signal usage 55.
- related::Partnership::AVGO::Sector Peer: needs 1 more example(s). Partnership related slice for AVGO / Sector Peer has sample 7, missing horizons [], fallback usage 55, signal usage 55.
- related::Capital Expenditure::AMZN::Competitor: needs 1 more example(s). Capital Expenditure related slice for AMZN / Competitor has sample 24, missing horizons [], fallback usage 50, signal usage 50.
- related::Legal/Regulatory::META::Sector Peer: needs 1 more example(s). Legal/Regulatory related slice for META / Sector Peer has sample 6, missing horizons [], fallback usage 50, signal usage 50.
