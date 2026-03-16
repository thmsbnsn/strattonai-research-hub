insert into public.events (
  id,
  source_name,
  source_record_id,
  headline,
  ticker,
  category,
  sentiment,
  timestamp,
  historical_analog,
  sample_size,
  avg_return,
  details
)
values
  (
    '11111111-1111-1111-1111-111111111111',
    'seed_sql',
    'nvda-blackwell-ultra-20260313',
    'NVIDIA announces next-gen AI training chips with 2x performance',
    'NVDA',
    'Product Launch',
    'positive',
    '2026-03-13T08:32:00Z',
    '12 similar events detected. Supplier stocks averaged +1.8% return over 5 days.',
    12,
    1.8000,
    'NVIDIA unveiled its Blackwell Ultra architecture at GTC 2026, featuring 2x training performance improvements. The new B300 chips are expected to ship Q3 2026. Major cloud providers have already placed advance orders.'
  ),
  (
    '22222222-2222-2222-2222-222222222222',
    'seed_sql',
    'lly-fda-expanded-approval-20260313',
    'FDA approves Eli Lilly''s new weight loss drug for expanded indications',
    'LLY',
    'Regulatory Approval',
    'positive',
    '2026-03-13T07:15:00Z',
    '8 similar FDA approvals detected. Primary company averaged +3.2% over 3 days.',
    8,
    3.2000,
    'FDA granted expanded approval for tirzepatide for cardiovascular risk reduction in obese patients. This broadens the addressable market significantly.'
  ),
  (
    '33333333-3333-3333-3333-333333333333',
    'seed_sql',
    'tsla-shanghai-halt-20260313',
    'Tesla reports production halt at Shanghai Gigafactory due to supply chain issues',
    'TSLA',
    'Supply Disruption',
    'negative',
    '2026-03-13T06:45:00Z',
    '15 similar disruptions detected. Stock averaged -2.1% over 5 days, competitors +0.5%.',
    15,
    -2.1000,
    null
  ),
  (
    '44444444-4444-4444-4444-444444444444',
    'seed_sql',
    'msft-asia-ai-capex-20260313',
    'Microsoft announces $10B AI infrastructure investment in Southeast Asia',
    'MSFT',
    'Capital Expenditure',
    'positive',
    '2026-03-13T05:20:00Z',
    '6 similar capex announcements. Stock averaged +0.8% over 10 days.',
    6,
    0.8000,
    null
  ),
  (
    '55555555-5555-5555-5555-555555555555',
    'seed_sql',
    'aapl-eu-antitrust-fine-20260312',
    'Apple loses antitrust case in EU, faces $4.5B fine',
    'AAPL',
    'Legal/Regulatory',
    'negative',
    '2026-03-12T18:30:00Z',
    '9 similar antitrust rulings. Stock averaged -1.4% over 3 days, recovered by day 10.',
    9,
    -1.4000,
    null
  )
on conflict (id) do update
set
  source_name = excluded.source_name,
  source_record_id = excluded.source_record_id,
  headline = excluded.headline,
  ticker = excluded.ticker,
  category = excluded.category,
  sentiment = excluded.sentiment,
  timestamp = excluded.timestamp,
  historical_analog = excluded.historical_analog,
  sample_size = excluded.sample_size,
  avg_return = excluded.avg_return,
  details = excluded.details;

insert into public.related_companies (
  id,
  event_id,
  source_ticker,
  target_ticker,
  name,
  relationship,
  strength
)
values
  ('61111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', 'NVDA', 'TSM', 'Taiwan Semi', 'Supplier', 0.9000),
  ('62222222-2222-2222-2222-222222222222', '11111111-1111-1111-1111-111111111111', 'NVDA', 'AMD', 'AMD', 'Competitor', 0.8500),
  ('63333333-3333-3333-3333-333333333333', '11111111-1111-1111-1111-111111111111', 'NVDA', 'AVGO', 'Broadcom', 'Sector Peer', 0.6000),
  ('64444444-4444-4444-4444-444444444444', '22222222-2222-2222-2222-222222222222', 'LLY', 'NVO', 'Novo Nordisk', 'Competitor', 0.7200),
  ('65555555-5555-5555-5555-555555555555', '22222222-2222-2222-2222-222222222222', 'LLY', 'AMGN', 'Amgen', 'Competitor', 0.6100),
  ('66666666-6666-6666-6666-666666666666', '33333333-3333-3333-3333-333333333333', 'TSLA', 'RIVN', 'Rivian', 'Competitor', 0.7000),
  ('67777777-7777-7777-7777-777777777777', '33333333-3333-3333-3333-333333333333', 'TSLA', 'PANW', 'Panasonic', 'Supplier', 0.5400),
  ('68888888-8888-8888-8888-888888888888', '44444444-4444-4444-4444-444444444444', 'MSFT', 'GOOGL', 'Alphabet', 'Competitor', 0.7800),
  ('69999999-9999-9999-9999-999999999999', '44444444-4444-4444-4444-444444444444', 'MSFT', 'AMZN', 'Amazon', 'Competitor', 0.8200),
  ('6aaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '44444444-4444-4444-4444-444444444444', 'MSFT', 'ORCL', 'Oracle', 'Sector Peer', 0.5800),
  ('6bbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '55555555-5555-5555-5555-555555555555', 'AAPL', 'GOOGL', 'Alphabet', 'Sector Peer', 0.6500),
  ('6ccccccc-cccc-cccc-cccc-cccccccccccc', '55555555-5555-5555-5555-555555555555', 'AAPL', 'META', 'Meta', 'Sector Peer', 0.6300),
  ('71111111-1111-1111-1111-111111111111', null, 'NVDA', 'TSM', 'Taiwan Semi', 'Supplier', 0.9000),
  ('72222222-2222-2222-2222-222222222222', null, 'NVDA', 'AMD', 'AMD', 'Competitor', 0.8500),
  ('73333333-3333-3333-3333-333333333333', null, 'NVDA', 'AVGO', 'Broadcom', 'Sector Peer', 0.6000),
  ('74444444-4444-4444-4444-444444444444', null, 'NVDA', 'INTC', 'Intel', 'Competitor', 0.7000),
  ('75555555-5555-5555-5555-555555555555', null, 'NVDA', 'MSFT', 'Microsoft', 'Customer', 0.8000),
  ('76666666-6666-6666-6666-666666666666', null, 'NVDA', 'GOOGL', 'Alphabet', 'Customer', 0.7500),
  ('77777777-7777-7777-7777-777777777777', null, 'TSM', 'AVGO', 'Broadcom', 'Supplier', 0.5000),
  ('78888888-8888-8888-8888-888888888888', null, 'AMD', 'INTC', 'Intel', 'Competitor', 0.8000)
on conflict (id) do update
set
  event_id = excluded.event_id,
  source_ticker = excluded.source_ticker,
  target_ticker = excluded.target_ticker,
  name = excluded.name,
  relationship = excluded.relationship,
  strength = excluded.strength;

insert into public.research_insights (
  id,
  title,
  summary,
  confidence,
  event_count
)
values
  ('81111111-1111-1111-1111-111111111111', 'AI Chip Supply Chain Pattern', 'Supplier stocks outperform by +1.8% avg within 5 days of major chip announcements.', 'High', 12),
  ('82222222-2222-2222-2222-222222222222', 'FDA Approval Momentum', 'Pharma stocks show sustained momentum for 10 days post-approval. Competitors show mild weakness.', 'Moderate', 8),
  ('83333333-3333-3333-3333-333333333333', 'Supply Chain Disruption Recovery', 'EV makers recover from production halts within 15 days on average. Competitors see brief lift.', 'Moderate', 15)
on conflict (id) do update
set
  title = excluded.title,
  summary = excluded.summary,
  confidence = excluded.confidence,
  event_count = excluded.event_count;

insert into public.company_profiles (
  id,
  ticker,
  name,
  sector,
  industry,
  market_cap,
  pe,
  revenue,
  employees
)
values
  ('91111111-1111-1111-1111-111111111111', 'NVDA', 'NVIDIA Corporation', 'Technology', 'Semiconductors', '$3.2T', 62.4000, '$130.5B', '32,000'),
  ('92222222-2222-2222-2222-222222222222', 'TSM', 'Taiwan Semiconductor Manufacturing', 'Technology', 'Semiconductor Manufacturing', '$915B', 27.8000, '$89.2B', '76,000'),
  ('93333333-3333-3333-3333-333333333333', 'AMD', 'Advanced Micro Devices', 'Technology', 'Semiconductors', '$298B', 54.1000, '$28.9B', '28,000'),
  ('94444444-4444-4444-4444-444444444444', 'MSFT', 'Microsoft Corporation', 'Technology', 'Software Infrastructure', '$3.1T', 38.6000, '$261.8B', '228,000'),
  ('95555555-5555-5555-5555-555555555555', 'LLY', 'Eli Lilly and Company', 'Healthcare', 'Drug Manufacturers', '$815B', 71.2000, '$45.6B', '47,000'),
  ('96666666-6666-6666-6666-666666666666', 'TSLA', 'Tesla, Inc.', 'Consumer Discretionary', 'Auto Manufacturers', '$772B', 58.9000, '$104.7B', '140,000'),
  ('97777777-7777-7777-7777-777777777777', 'AAPL', 'Apple Inc.', 'Technology', 'Consumer Electronics', '$3.0T', 31.4000, '$391.0B', '161,000')
on conflict (ticker) do update
set
  name = excluded.name,
  sector = excluded.sector,
  industry = excluded.industry,
  market_cap = excluded.market_cap,
  pe = excluded.pe,
  revenue = excluded.revenue,
  employees = excluded.employees;

insert into public.event_study_results (
  id,
  event_type,
  horizon,
  avg_return,
  win_rate,
  sample_size
)
values
  ('a1111111-1111-1111-1111-111111111111', 'Product Launch', '1D', 0.4500, 58.0000, 42),
  ('a2222222-2222-2222-2222-222222222222', 'Product Launch', '3D', 1.1200, 62.0000, 42),
  ('a3333333-3333-3333-3333-333333333333', 'Product Launch', '5D', 1.7800, 65.0000, 42),
  ('a4444444-4444-4444-4444-444444444444', 'Product Launch', '10D', 2.3400, 61.0000, 42),
  ('a5555555-5555-5555-5555-555555555555', 'Product Launch', '20D', 3.1500, 59.0000, 42),
  ('a6666666-6666-6666-6666-666666666666', 'Regulatory Approval', '1D', 0.8200, 60.0000, 28),
  ('a7777777-7777-7777-7777-777777777777', 'Regulatory Approval', '5D', 2.9600, 68.0000, 28),
  ('a8888888-8888-8888-8888-888888888888', 'Supply Disruption', '1D', -0.7300, 41.0000, 31),
  ('a9999999-9999-9999-9999-999999999999', 'Supply Disruption', '5D', -2.1000, 37.0000, 31)
on conflict (id) do update
set
  event_type = excluded.event_type,
  horizon = excluded.horizon,
  avg_return = excluded.avg_return,
  win_rate = excluded.win_rate,
  sample_size = excluded.sample_size;

insert into public.journal_entries (
  id,
  date,
  title,
  events,
  patterns,
  hypothesis,
  confidence
)
values
  (
    'b1111111-1111-1111-1111-111111111111',
    '2026-03-13',
    'AI Chip Supply Chain Analysis',
    '["NVDA product launch announcement", "TSM capacity expansion report"]'::jsonb,
    'Supplier stocks consistently outperform following major chip announcements. TSM shows strongest correlation (+0.82) with NVDA product events.',
    'NVDA AI chip announcement detected. Historical analogs suggest supplier stocks often outperform over the following week. Confidence: Moderate.',
    'Moderate'
  ),
  (
    'b2222222-2222-2222-2222-222222222222',
    '2026-03-12',
    'Pharma Regulatory Pattern',
    '["LLY FDA expanded approval", "NVO competitive response analysis"]'::jsonb,
    'FDA approvals for weight-loss drugs create sustained momentum. Competitor stocks show initial weakness but recover within 5 days.',
    'The GLP-1 market is expanding. Each new approval validates the category, potentially lifting all players long-term despite short-term competitive dynamics.',
    'High'
  ),
  (
    'b3333333-3333-3333-3333-333333333333',
    '2026-03-11',
    'EV Supply Chain Disruption',
    '["TSLA Shanghai production halt", "Battery supply constraints detected"]'::jsonb,
    'Production halts typically last 5-10 days. Stock drawdown averages -2.1% but recovers within 15 days. Competitors see temporary lift.',
    'Supply chain issues are becoming less impactful as EV makers diversify suppliers. Recovery times have shortened from 20 days to 15 days over the past 2 years.',
    'Low'
  )
on conflict (id) do update
set
  date = excluded.date,
  title = excluded.title,
  events = excluded.events,
  patterns = excluded.patterns,
  hypothesis = excluded.hypothesis,
  confidence = excluded.confidence;

insert into public.paper_trades (
  id,
  ticker,
  direction,
  signal,
  entry_price,
  current_price,
  entry_date,
  quantity,
  status
)
values
  ('c1111111-1111-1111-1111-111111111111', 'TSM', 'Long', 'NVDA chip announcement → Supplier outperformance pattern', 185.4000, 189.2000, '2026-03-13', 100.0000, 'Open'),
  ('c2222222-2222-2222-2222-222222222222', 'LLY', 'Long', 'FDA approval → Post-approval momentum pattern', 892.5000, 918.3000, '2026-03-13', 20.0000, 'Open'),
  ('c3333333-3333-3333-3333-333333333333', 'TSLA', 'Short', 'Production halt → Supply disruption drawdown pattern', 242.8000, 238.1000, '2026-03-13', 50.0000, 'Open'),
  ('c4444444-4444-4444-4444-444444444444', 'AMD', 'Long', 'NVDA competitor correlation → Sector momentum pattern', 178.6000, 176.9000, '2026-03-10', 75.0000, 'Closed')
on conflict (id) do update
set
  ticker = excluded.ticker,
  direction = excluded.direction,
  signal = excluded.signal,
  entry_price = excluded.entry_price,
  current_price = excluded.current_price,
  entry_date = excluded.entry_date,
  quantity = excluded.quantity,
  status = excluded.status;
