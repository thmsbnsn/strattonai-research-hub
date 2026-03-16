# Low-Confidence Diagnostics Diff

## Category Changes
- Capital Expenditure: low 169 -> 183 (delta +14), low_ratio 68.98% -> 69.06%, after_causes=['older_recency_mix', 'weak_edge', 'sparse_exact_coverage']
- Earnings: low 67 -> 67 (delta +0), low_ratio 70.53% -> 70.53%, after_causes=['small_sample_size', 'older_recency_mix', 'sparse_exact_coverage']
- Legal/Regulatory: low 204 -> 209 (delta +5), low_ratio 97.14% -> 88.94%, after_causes=['older_recency_mix', 'sparse_exact_coverage', 'weak_edge']
- Macro Event: low 93 -> 102 (delta +9), low_ratio 74.40% -> 61.82%, after_causes=['older_recency_mix', 'sparse_exact_coverage', 'small_sample_size']
- Partnership: low 156 -> 184 (delta +28), low_ratio 62.40% -> 66.91%, after_causes=['older_recency_mix', 'weak_edge', 'sparse_exact_coverage']
- Product Launch: low 150 -> 185 (delta +35), low_ratio 63.83% -> 69.81%, after_causes=['older_recency_mix', 'sparse_exact_coverage', 'weak_edge']
- Regulatory Approval: low 51 -> 51 (delta +0), low_ratio 68.00% -> 68.00%, after_causes=['older_recency_mix', 'small_sample_size', 'sparse_exact_coverage']
- Supply Disruption: low 95 -> 95 (delta +0), low_ratio 90.48% -> 90.48%, after_causes=['small_sample_size', 'sparse_exact_coverage', 'older_recency_mix']

## Focus Slice Changes
- primary::Macro Event::AAPL: low 5 -> 10, sample 1 -> 2, causes ['small_sample_size', 'weak_edge', 'older_recency_mix'] -> ['small_sample_size', 'weak_edge', 'older_recency_mix']
- primary::Macro Event::NVDA: low 10 -> 15, sample 2 -> 3, causes ['small_sample_size', 'older_recency_mix'] -> ['small_sample_size', 'older_recency_mix']
- related::Capital Expenditure::AMZN::Competitor: low 24 -> 27, sample 16 -> 18, causes ['sparse_exact_coverage', 'weak_edge', 'older_recency_mix'] -> ['sparse_exact_coverage', 'weak_edge', 'older_recency_mix']
- related::Capital Expenditure::GOOGL::Competitor: low 15 -> 18, sample 16 -> 18, causes ['sparse_exact_coverage', 'weak_edge'] -> ['sparse_exact_coverage', 'weak_edge', 'older_recency_mix']
- related::Capital Expenditure::ORCL::Sector Peer: low 33 -> 36, sample 17 -> 18, causes ['sparse_exact_coverage', 'weak_edge', 'older_recency_mix'] -> ['sparse_exact_coverage', 'weak_edge', 'older_recency_mix']
- related::Legal/Regulatory::GOOGL::Sector Peer: low 50 -> 55, sample 22 -> 25, causes ['sparse_exact_coverage', 'weak_edge', 'weak_win_rate', 'older_recency_mix'] -> ['sparse_exact_coverage', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- related::Legal/Regulatory::META::Sector Peer: low 40 -> 45, sample 22 -> 25, causes ['sparse_exact_coverage', 'weak_edge', 'weak_win_rate', 'older_recency_mix'] -> ['sparse_exact_coverage', 'weak_edge', 'weak_win_rate', 'older_recency_mix']
- related::Partnership::AVGO::Sector Peer: low 8 -> 18, sample 9 -> 10, causes ['sparse_exact_coverage', 'weak_edge', 'older_recency_mix'] -> ['sparse_exact_coverage', 'weak_edge', 'older_recency_mix']
- related::Partnership::MSFT::Customer: low 32 -> 36, sample 12 -> 14, causes ['sparse_exact_coverage', 'weak_edge', 'older_recency_mix'] -> ['sparse_exact_coverage', 'weak_edge', 'older_recency_mix']
- related::Partnership::TSM::Supplier: low 24 -> 27, sample 9 -> 10, causes ['sparse_exact_coverage', 'weak_avg_return', 'older_recency_mix'] -> ['sparse_exact_coverage', 'weak_edge', 'older_recency_mix']
- related::Product Launch::AMD::Competitor: low 8 -> 15, sample 15 -> 17, causes ['sparse_exact_coverage', 'weak_edge', 'older_recency_mix'] -> ['sparse_exact_coverage', 'weak_edge', 'older_recency_mix']
- related::Product Launch::GOOGL::Competitor: low 12 -> 21, sample 15 -> 17, causes ['sparse_exact_coverage', 'weak_edge', 'older_recency_mix'] -> ['sparse_exact_coverage', 'weak_edge', 'older_recency_mix']
- related::Product Launch::MSFT::Customer: low 12 -> 15, sample 6 -> 7, causes ['sparse_exact_coverage', 'thin_sample_depth', 'weak_edge', 'older_recency_mix'] -> ['sparse_exact_coverage', 'thin_sample_depth', 'weak_edge', 'older_recency_mix']
- related::Product Launch::TSM::Supplier: low 15 -> 18, sample 9 -> 10, causes ['sparse_exact_coverage', 'weak_edge', 'older_recency_mix'] -> ['sparse_exact_coverage', 'weak_edge', 'older_recency_mix']

## Efficient Upgrade Candidates After
- related::Regulatory Approval::AMGN::Sector Peer: linked_gap_size=None, low=10, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Supply Disruption::RIVN::Competitor: linked_gap_size=None, low=10, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Regulatory Approval::LLY::Sector Peer: linked_gap_size=None, low=5, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Regulatory Approval::NVO::Sector Peer: linked_gap_size=None, low=5, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Supply Disruption::AMD::Competitor: linked_gap_size=None, low=5, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Supply Disruption::AMGN::Sector Peer: linked_gap_size=None, low=5, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Supply Disruption::AVGO::Sector Peer: linked_gap_size=None, low=5, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Supply Disruption::GOOGL::Sector Peer: linked_gap_size=None, low=5, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Supply Disruption::META::Sector Peer: linked_gap_size=None, low=5, note=One more exact example would likely reduce fallback reliance on this slice.
- related::Supply Disruption::NVO::Competitor: linked_gap_size=None, low=5, note=One more exact example would likely reduce fallback reliance on this slice.
