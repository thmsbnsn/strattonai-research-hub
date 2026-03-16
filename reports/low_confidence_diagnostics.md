# Low-Confidence Diagnostics

## Category Summary
- Capital Expenditure: low=239, moderate=26, high=20, low_ratio=83.86%, causes=['older_recency_mix', 'weak_edge', 'sparse_exact_coverage']
- Earnings: low=75, moderate=19, high=1, low_ratio=78.95%, causes=['weak_edge', 'older_recency_mix', 'sparse_exact_coverage']
- Legal/Regulatory: low=237, moderate=14, high=9, low_ratio=91.15%, causes=['older_recency_mix', 'sparse_exact_coverage', 'relationship_sparsity']
- Macro Event: low=117, moderate=24, high=24, low_ratio=70.91%, causes=['older_recency_mix', 'sparse_exact_coverage', 'relationship_sparsity']
- Partnership: low=185, moderate=78, high=57, low_ratio=57.81%, causes=['older_recency_mix', 'sparse_exact_coverage', 'relationship_sparsity']
- Product Launch: low=292, moderate=11, high=12, low_ratio=92.70%, causes=['older_recency_mix', 'sparse_exact_coverage', 'relationship_sparsity']
- Regulatory Approval: low=63, moderate=6, high=6, low_ratio=84.00%, causes=['older_recency_mix', 'small_sample_size', 'sparse_exact_coverage']
- Supply Disruption: low=51, moderate=35, high=19, low_ratio=48.57%, causes=['older_recency_mix', 'sparse_exact_coverage', 'relationship_sparsity']

## Top Low-Confidence Slices
- related::Legal/Regulatory::GOOGL::Sector Peer: low=60/60, sample=43, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_avg_return', 'older_recency_mix']
- related::Capital Expenditure::ORCL::Sector Peer: low=52/65, sample=47.75, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- related::Legal/Regulatory::META::Sector Peer: low=50/50, sample=43, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_avg_return', 'older_recency_mix']
- related::Product Launch::GOOGL::Competitor: low=45/45, sample=162.8, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- related::Product Launch::TSM::Supplier: low=40/40, sample=104.2, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- related::Capital Expenditure::AMZN::Competitor: low=40/50, sample=72.25, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- primary::Partnership::NVDA: low=35/35, sample=4.6, fallback_ratio=0.00%, causes=['small_sample_size', 'weak_avg_return', 'older_recency_mix']
- related::Product Launch::AMD::Competitor: low=35/35, sample=162.8, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- related::Partnership::TSM::Supplier: low=30/55, sample=9.73, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_avg_return', 'older_recency_mix']
- related::Capital Expenditure::GOOGL::Competitor: low=28/35, sample=72.25, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- related::Product Launch::MSFT::Customer: low=25/25, sample=3.8, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'relationship_sparsity', 'small_sample_size', 'older_recency_mix']
- primary::Legal/Regulatory::AAPL: low=24/30, sample=30.5, fallback_ratio=0.00%, causes=['weak_edge', 'weak_win_rate', 'older_recency_mix']

## Efficient Upgrade Candidates
- related::Partnership::MSFT::Customer: linked_gap_size=1, low=22, sample=13, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Partnership::GOOGL::Customer: linked_gap_size=None, low=12, sample=13, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Regulatory Approval::NVO::Competitor: linked_gap_size=None, low=9, sample=13.33, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Regulatory Approval::AMGN::Competitor: linked_gap_size=None, low=6, sample=13.33, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Regulatory Approval::LLY::Competitor: linked_gap_size=None, low=3, sample=13.33, note=One more exact example would likely reduce fallback reliance on this slice.

## Focus Slices
