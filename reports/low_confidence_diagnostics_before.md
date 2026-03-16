# Low-Confidence Diagnostics

## Category Summary
- Capital Expenditure: low=169, moderate=43, high=33, low_ratio=68.98%, causes=['weak_edge', 'older_recency_mix', 'sparse_exact_coverage']
- Earnings: low=67, moderate=28, high=0, low_ratio=70.53%, causes=['small_sample_size', 'older_recency_mix', 'sparse_exact_coverage']
- Legal/Regulatory: low=204, moderate=6, high=0, low_ratio=97.14%, causes=['older_recency_mix', 'sparse_exact_coverage', 'weak_edge']
- Macro Event: low=93, moderate=16, high=16, low_ratio=74.40%, causes=['older_recency_mix', 'sparse_exact_coverage', 'weak_avg_return']
- Partnership: low=156, moderate=82, high=12, low_ratio=62.40%, causes=['older_recency_mix', 'sparse_exact_coverage', 'weak_edge']
- Product Launch: low=150, moderate=55, high=30, low_ratio=63.83%, causes=['older_recency_mix', 'sparse_exact_coverage', 'weak_edge']
- Regulatory Approval: low=51, moderate=24, high=0, low_ratio=68.00%, causes=['older_recency_mix', 'small_sample_size', 'sparse_exact_coverage']
- Supply Disruption: low=95, moderate=10, high=0, low_ratio=90.48%, causes=['small_sample_size', 'sparse_exact_coverage', 'older_recency_mix']

## Top Low-Confidence Slices
- related::Legal/Regulatory::GOOGL::Sector Peer: low=50/50, sample=22, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- related::Legal/Regulatory::META::Sector Peer: low=40/40, sample=22, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- related::Capital Expenditure::ORCL::Sector Peer: low=33/55, sample=17, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'weak_edge', 'older_recency_mix']
- related::Partnership::MSFT::Customer: low=32/40, sample=12, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'weak_edge', 'older_recency_mix']
- primary::Legal/Regulatory::AAPL: low=24/30, sample=6, fallback_ratio=0.00%, causes=['thin_sample_depth', 'weak_avg_return', 'older_recency_mix']
- related::Capital Expenditure::AMZN::Competitor: low=24/40, sample=16, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'weak_edge', 'older_recency_mix']
- related::Partnership::TSM::Supplier: low=24/40, sample=9, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'weak_avg_return', 'older_recency_mix']
- related::Partnership::GOOGL::Customer: low=16/20, sample=12, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'weak_edge', 'older_recency_mix']
- primary::Capital Expenditure::GOOGL: low=15/15, sample=3, fallback_ratio=0.00%, causes=['small_sample_size', 'weak_edge', 'older_recency_mix']
- primary::Macro Event::MSFT: low=15/15, sample=3, fallback_ratio=0.00%, causes=['small_sample_size', 'older_recency_mix']
- primary::Product Launch::NVDA: low=15/15, sample=3, fallback_ratio=0.00%, causes=['small_sample_size', 'weak_win_rate', 'older_recency_mix']
- primary::Regulatory Approval::LLY: low=15/15, sample=3, fallback_ratio=0.00%, causes=['small_sample_size', 'older_recency_mix']

## Efficient Upgrade Candidates
- related::Legal/Regulatory::MSFT::Competitor: linked_gap_size=None, low=10, sample=4, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Regulatory Approval::AMGN::Sector Peer: linked_gap_size=None, low=10, sample=4, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Supply Disruption::RIVN::Competitor: linked_gap_size=None, low=10, sample=4, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Legal/Regulatory::AMZN::Competitor: linked_gap_size=None, low=5, sample=4, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Legal/Regulatory::RIVN::Competitor: linked_gap_size=None, low=5, sample=4, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Regulatory Approval::LLY::Sector Peer: linked_gap_size=None, low=5, sample=4, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Regulatory Approval::NVO::Sector Peer: linked_gap_size=None, low=5, sample=4, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Supply Disruption::AMD::Competitor: linked_gap_size=None, low=5, sample=4, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Supply Disruption::AMGN::Sector Peer: linked_gap_size=None, low=5, sample=4, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Supply Disruption::AVGO::Sector Peer: linked_gap_size=None, low=5, sample=4, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Supply Disruption::GOOGL::Sector Peer: linked_gap_size=None, low=5, sample=4, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Supply Disruption::META::Sector Peer: linked_gap_size=None, low=5, sample=4, note=One more exact example would likely reduce fallback reliance on this slice.

## Focus Slices
- primary::Macro Event::AAPL: low=5/5, sample=1, causes=['small_sample_size', 'weak_edge', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- primary::Macro Event::NVDA: low=10/10, sample=2, causes=['small_sample_size', 'older_recency_mix'], note=This slice remains low-confidence for mixed reasons.
- related::Product Launch::GOOGL::Competitor: low=12/30, sample=15, causes=['sparse_exact_coverage', 'weak_edge', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Product Launch::TSM::Supplier: low=15/25, sample=9, causes=['sparse_exact_coverage', 'weak_edge', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Product Launch::MSFT::Customer: low=12/20, sample=6, causes=['sparse_exact_coverage', 'thin_sample_depth', 'weak_edge', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Product Launch::AMD::Competitor: low=8/20, sample=15, causes=['sparse_exact_coverage', 'weak_edge', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Capital Expenditure::ORCL::Sector Peer: low=33/55, sample=17, causes=['sparse_exact_coverage', 'weak_edge', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Capital Expenditure::AMZN::Competitor: low=24/40, sample=16, causes=['sparse_exact_coverage', 'weak_edge', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Capital Expenditure::GOOGL::Competitor: low=15/25, sample=16, causes=['sparse_exact_coverage', 'weak_edge'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Legal/Regulatory::GOOGL::Sector Peer: low=50/50, sample=22, causes=['sparse_exact_coverage', 'weak_edge', 'weak_win_rate', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Legal/Regulatory::META::Sector Peer: low=40/40, sample=22, causes=['sparse_exact_coverage', 'weak_edge', 'weak_win_rate', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Partnership::TSM::Supplier: low=24/40, sample=9, causes=['sparse_exact_coverage', 'weak_avg_return', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Partnership::MSFT::Customer: low=32/40, sample=12, causes=['sparse_exact_coverage', 'weak_edge', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Partnership::AVGO::Sector Peer: low=8/40, sample=9, causes=['sparse_exact_coverage', 'weak_edge', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
