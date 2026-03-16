# Precision Evidence Quality Pass Diff

## Mapping Expansion
- Normalized financial-news rows unlocked: 289
- Stored `financial_news_local` rows unlocked: 287

## Total Events
- Events: 2024 -> 2317 (delta +293)

## Category Counts
- Capital Expenditure: 169 -> 189 (delta +20)
- Earnings: 175 -> 201 (delta +26)
- Legal/Regulatory: 190 -> 219 (delta +29)
- Macro Event: 971 -> 1117 (delta +146)
- Partnership: 13 -> 15 (delta +2)
- Product Launch: 347 -> 395 (delta +48)
- Regulatory Approval: 31 -> 37 (delta +6)
- Supply Disruption: 128 -> 144 (delta +16)

## Partnership Depth
- Partnership events: 13 -> 15 (delta +2)

## Event Studies
- Valid observations: 17607 -> 17747 (delta +140)
- Detailed study rows: 1203 -> 1217 (delta +14)

## Signals
- Signal count: 1480 -> 1620 (delta +140)
- Confidence bands before: {'High': 98, 'Moderate': 240, 'Low': 1142}
- Confidence bands after: {'High': 148, 'Moderate': 213, 'Low': 1259}

## Exact Slice Improvements
- Product Launch::GOOGL::Competitor: min sample 54 -> 56 (delta +2)
- Product Launch::TSM::Supplier: min sample 2 -> 4 (delta +2)
- Product Launch::AMD::Competitor: min sample 2 -> 4 (delta +2)
- Partnership::TSM::Supplier: min sample 5 -> 7 (delta +2)
- Partnership::MSFT::Customer: min sample 5 -> 7 (delta +2)
- Partnership::AVGO::Sector Peer: min sample 5 -> 7 (delta +2)
- Legal/Regulatory::GOOGL::Sector Peer: min sample 4 -> 5 (delta +1)
- Legal/Regulatory::META::Sector Peer: min sample 5 -> 6 (delta +1)
- Capital Expenditure::ORCL::Sector Peer: min sample 6 -> 7 (delta +1)
- Capital Expenditure::AMZN::Competitor: min sample 23 -> 24 (delta +1)
- Capital Expenditure::GOOGL::Competitor: min sample 21 -> 22 (delta +1)

## Exact Slice Diagnostic Changes
- related::Capital Expenditure::ORCL::Sector Peer: low 48 -> 52 (delta +4), sample 46.75 -> 47.75, causes ['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix'] -> ['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- related::Legal/Regulatory::GOOGL::Sector Peer: low 55 -> 60 (delta +5), sample 40 -> 43, causes ['sparse_exact_coverage', 'relationship_sparsity', 'weak_avg_return', 'weak_win_rate', 'older_recency_mix'] -> ['sparse_exact_coverage', 'relationship_sparsity', 'weak_avg_return', 'older_recency_mix']
- related::Partnership::TSM::Supplier: low 18 -> 30 (delta +12), sample 8 -> 9.73, causes ['sparse_exact_coverage', 'relationship_sparsity', 'weak_avg_return', 'older_recency_mix'] -> ['sparse_exact_coverage', 'relationship_sparsity', 'weak_avg_return', 'older_recency_mix']
- related::Partnership::MSFT::Customer: low 9 -> 22 (delta +13), sample 12 -> 13, causes ['sparse_exact_coverage', 'relationship_sparsity', 'weak_avg_return', 'older_recency_mix'] -> ['sparse_exact_coverage', 'relationship_sparsity', 'older_recency_mix']
- related::Partnership::AVGO::Sector Peer: low 18 -> 11 (delta -7), sample 8 -> 11, causes ['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix'] -> ['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- related::Legal/Regulatory::META::Sector Peer: low 45 -> 50 (delta +5), sample 40 -> 43, causes ['sparse_exact_coverage', 'relationship_sparsity', 'weak_avg_return', 'weak_win_rate', 'older_recency_mix'] -> ['sparse_exact_coverage', 'relationship_sparsity', 'weak_avg_return', 'older_recency_mix']
- related::Capital Expenditure::AMZN::Competitor: low 36 -> 40 (delta +4), sample 70.25 -> 72.25, causes ['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix'] -> ['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- related::Product Launch::GOOGL::Competitor: low 35 -> 45 (delta +10), sample 158.8 -> 162.8, causes ['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix'] -> ['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- related::Product Launch::TSM::Supplier: low 30 -> 40 (delta +10), sample 102.2 -> 104.2, causes ['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix'] -> ['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- primary::Partnership::NVDA: low 30 -> 35 (delta +5), sample 3.6 -> 4.6, causes ['small_sample_size', 'older_recency_mix'] -> ['small_sample_size', 'weak_avg_return', 'older_recency_mix']

## Remaining Top Weak Slices
- related::Legal/Regulatory::GOOGL::Sector Peer: low=60/60, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_avg_return', 'older_recency_mix']
- related::Capital Expenditure::ORCL::Sector Peer: low=52/65, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- related::Legal/Regulatory::META::Sector Peer: low=50/50, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_avg_return', 'older_recency_mix']
- related::Product Launch::GOOGL::Competitor: low=45/45, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- related::Product Launch::TSM::Supplier: low=40/40, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- related::Capital Expenditure::AMZN::Competitor: low=40/50, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- primary::Partnership::NVDA: low=35/35, causes=['small_sample_size', 'weak_avg_return', 'older_recency_mix']
- related::Product Launch::AMD::Competitor: low=35/35, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
