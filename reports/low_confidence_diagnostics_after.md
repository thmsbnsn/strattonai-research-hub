# Low-Confidence Diagnostics

## Category Summary
- Capital Expenditure: low=183, moderate=46, high=36, low_ratio=69.06%, causes=['older_recency_mix', 'weak_edge', 'sparse_exact_coverage']
- Earnings: low=67, moderate=28, high=0, low_ratio=70.53%, causes=['small_sample_size', 'older_recency_mix', 'sparse_exact_coverage']
- Legal/Regulatory: low=209, moderate=26, high=0, low_ratio=88.94%, causes=['older_recency_mix', 'sparse_exact_coverage', 'weak_edge']
- Macro Event: low=102, moderate=42, high=21, low_ratio=61.82%, causes=['older_recency_mix', 'sparse_exact_coverage', 'small_sample_size']
- Partnership: low=184, moderate=47, high=44, low_ratio=66.91%, causes=['older_recency_mix', 'weak_edge', 'sparse_exact_coverage']
- Product Launch: low=185, moderate=36, high=44, low_ratio=69.81%, causes=['older_recency_mix', 'sparse_exact_coverage', 'weak_edge']
- Regulatory Approval: low=51, moderate=24, high=0, low_ratio=68.00%, causes=['older_recency_mix', 'small_sample_size', 'sparse_exact_coverage']
- Supply Disruption: low=95, moderate=10, high=0, low_ratio=90.48%, causes=['small_sample_size', 'sparse_exact_coverage', 'older_recency_mix']

## Top Low-Confidence Slices
- related::Legal/Regulatory::GOOGL::Sector Peer: low=55/55, sample=25, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- related::Legal/Regulatory::META::Sector Peer: low=45/45, sample=25, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- related::Partnership::MSFT::Customer: low=36/45, sample=14, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'weak_edge', 'older_recency_mix']
- related::Capital Expenditure::ORCL::Sector Peer: low=36/60, sample=18, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'weak_edge', 'older_recency_mix']
- related::Capital Expenditure::AMZN::Competitor: low=27/45, sample=18, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'weak_edge', 'older_recency_mix']
- related::Partnership::TSM::Supplier: low=27/45, sample=10, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'weak_edge', 'older_recency_mix']
- primary::Legal/Regulatory::AAPL: low=24/30, sample=6, fallback_ratio=0.00%, causes=['thin_sample_depth', 'weak_avg_return', 'older_recency_mix']
- related::Product Launch::GOOGL::Competitor: low=21/35, sample=17, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'weak_edge', 'older_recency_mix']
- related::Partnership::GOOGL::Customer: low=20/25, sample=14, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'weak_edge']
- primary::Partnership::NVDA: low=18/30, sample=6, fallback_ratio=0.00%, causes=['thin_sample_depth', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- related::Capital Expenditure::GOOGL::Competitor: low=18/30, sample=18, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'weak_edge', 'older_recency_mix']
- related::Product Launch::TSM::Supplier: low=18/30, sample=10, fallback_ratio=100.00%, causes=['sparse_exact_coverage', 'weak_edge', 'older_recency_mix']

## Efficient Upgrade Candidates
- related::Regulatory Approval::AMGN::Sector Peer: linked_gap_size=None, low=10, sample=4, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Supply Disruption::RIVN::Competitor: linked_gap_size=None, low=10, sample=4, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Regulatory Approval::LLY::Sector Peer: linked_gap_size=None, low=5, sample=4, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Regulatory Approval::NVO::Sector Peer: linked_gap_size=None, low=5, sample=4, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Supply Disruption::AMD::Competitor: linked_gap_size=None, low=5, sample=4, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Supply Disruption::AMGN::Sector Peer: linked_gap_size=None, low=5, sample=4, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Supply Disruption::AVGO::Sector Peer: linked_gap_size=None, low=5, sample=4, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Supply Disruption::GOOGL::Sector Peer: linked_gap_size=None, low=5, sample=4, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Supply Disruption::META::Sector Peer: linked_gap_size=None, low=5, sample=4, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Supply Disruption::NVO::Competitor: linked_gap_size=None, low=5, sample=4, note=One more exact example would likely reduce fallback reliance on this slice.

## Focus Slices
- primary::Macro Event::AAPL: low=10/10, sample=2, causes=['small_sample_size', 'weak_edge', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- primary::Macro Event::NVDA: low=15/15, sample=3, causes=['small_sample_size', 'older_recency_mix'], note=This slice remains low-confidence for mixed reasons.
- related::Product Launch::GOOGL::Competitor: low=21/35, sample=17, causes=['sparse_exact_coverage', 'weak_edge', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Product Launch::TSM::Supplier: low=18/30, sample=10, causes=['sparse_exact_coverage', 'weak_edge', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Product Launch::MSFT::Customer: low=15/25, sample=7, causes=['sparse_exact_coverage', 'thin_sample_depth', 'weak_edge', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Product Launch::AMD::Competitor: low=15/25, sample=17, causes=['sparse_exact_coverage', 'weak_edge', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Capital Expenditure::ORCL::Sector Peer: low=36/60, sample=18, causes=['sparse_exact_coverage', 'weak_edge', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Capital Expenditure::AMZN::Competitor: low=27/45, sample=18, causes=['sparse_exact_coverage', 'weak_edge', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Capital Expenditure::GOOGL::Competitor: low=18/30, sample=18, causes=['sparse_exact_coverage', 'weak_edge', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Legal/Regulatory::GOOGL::Sector Peer: low=55/55, sample=25, causes=['sparse_exact_coverage', 'weak_edge', 'weak_win_rate', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Legal/Regulatory::META::Sector Peer: low=45/45, sample=25, causes=['sparse_exact_coverage', 'weak_edge', 'weak_win_rate', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Partnership::TSM::Supplier: low=27/45, sample=10, causes=['sparse_exact_coverage', 'weak_edge', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Partnership::MSFT::Customer: low=36/45, sample=14, causes=['sparse_exact_coverage', 'weak_edge', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
- related::Partnership::AVGO::Sector Peer: low=18/45, sample=10, causes=['sparse_exact_coverage', 'weak_edge', 'older_recency_mix'], note=Depth alone is unlikely to help without stronger historical edge quality.
