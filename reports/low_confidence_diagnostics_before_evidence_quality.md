# Low-Confidence Diagnostics

## Category Summary
- Capital Expenditure: low=222, moderate=25, high=18, low_ratio=83.77%, causes=['older_recency_mix', 'weak_edge', 'sparse_exact_coverage']
- Earnings: low=75, moderate=19, high=1, low_ratio=78.95%, causes=['weak_edge', 'older_recency_mix', 'sparse_exact_coverage']
- Legal/Regulatory: low=216, moderate=11, high=8, low_ratio=91.91%, causes=['older_recency_mix', 'sparse_exact_coverage', 'relationship_sparsity']
- Macro Event: low=117, moderate=24, high=24, low_ratio=70.91%, causes=['older_recency_mix', 'sparse_exact_coverage', 'relationship_sparsity']
- Partnership: low=150, moderate=113, high=12, low_ratio=54.55%, causes=['older_recency_mix', 'small_sample_size', 'sparse_exact_coverage']
- Product Launch: low=248, moderate=7, high=10, low_ratio=93.58%, causes=['older_recency_mix', 'sparse_exact_coverage', 'relationship_sparsity']
- Regulatory Approval: low=63, moderate=6, high=6, low_ratio=84.00%, causes=['older_recency_mix', 'small_sample_size', 'sparse_exact_coverage']
- Supply Disruption: low=51, moderate=35, high=19, low_ratio=48.57%, causes=['older_recency_mix', 'sparse_exact_coverage', 'relationship_sparsity']

## Top Low-Confidence Slices
- related::Legal/Regulatory::GOOGL::Sector Peer: low=55/55, sample=40, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_avg_return', 'weak_win_rate', 'older_recency_mix']
- related::Capital Expenditure::ORCL::Sector Peer: low=48/60, sample=46.75, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- related::Legal/Regulatory::META::Sector Peer: low=45/45, sample=40, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_avg_return', 'weak_win_rate', 'older_recency_mix']
- related::Capital Expenditure::AMZN::Competitor: low=36/45, sample=70.25, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- related::Product Launch::GOOGL::Competitor: low=35/35, sample=158.8, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- primary::Partnership::NVDA: low=30/30, sample=3.6, fallback_ratio=0.00%, causes=['small_sample_size', 'older_recency_mix']
- related::Product Launch::TSM::Supplier: low=30/30, sample=102.2, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- related::Product Launch::AMD::Competitor: low=25/25, sample=158.8, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- related::Product Launch::MSFT::Customer: low=25/25, sample=3.8, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'relationship_sparsity', 'small_sample_size', 'older_recency_mix']
- primary::Legal/Regulatory::AAPL: low=24/30, sample=30.5, fallback_ratio=0.00%, causes=['weak_edge', 'weak_win_rate', 'older_recency_mix']
- related::Capital Expenditure::GOOGL::Competitor: low=24/30, sample=70.25, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- primary::Capital Expenditure::MSFT: low=20/25, sample=21.5, fallback_ratio=0.00%, causes=['weak_edge', 'older_recency_mix']

## Efficient Upgrade Candidates
- related::Regulatory Approval::NVO::Competitor: linked_gap_size=None, low=9, sample=13.33, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Regulatory Approval::AMGN::Competitor: linked_gap_size=None, low=6, sample=13.33, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Regulatory Approval::LLY::Competitor: linked_gap_size=None, low=3, sample=13.33, note=One more exact example would likely reduce fallback reliance on this slice.

## Focus Slices
- related::Product Launch::GOOGL::Competitor: low=35/35, sample=158.8, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Product Launch::TSM::Supplier: low=30/30, sample=102.2, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Product Launch::AMD::Competitor: low=25/25, sample=158.8, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Partnership::TSM::Supplier: low=18/45, sample=8, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_avg_return', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Partnership::MSFT::Customer: low=9/45, sample=12, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_avg_return', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Partnership::AVGO::Sector Peer: low=18/45, sample=8, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Legal/Regulatory::GOOGL::Sector Peer: low=55/55, sample=40, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_avg_return', 'weak_win_rate', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Legal/Regulatory::META::Sector Peer: low=45/45, sample=40, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_avg_return', 'weak_win_rate', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Capital Expenditure::ORCL::Sector Peer: low=48/60, sample=46.75, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Capital Expenditure::AMZN::Competitor: low=36/45, sample=70.25, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Capital Expenditure::GOOGL::Competitor: low=24/30, sample=70.25, causes=['sparse_exact_coverage', 'relationship_sparsity', 'weak_edge', 'weak_win_rate', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
