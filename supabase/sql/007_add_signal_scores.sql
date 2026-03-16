create table if not exists public.signal_scores (
  id uuid primary key default gen_random_uuid(),
  signal_key text not null unique,
  source_study_key text references public.event_study_statistics(study_key) on delete set null,
  event_id uuid not null references public.events(id) on delete cascade,
  event_category text not null,
  primary_ticker text not null,
  target_ticker text not null,
  target_type text not null check (target_type in ('primary', 'related')),
  relationship_type text,
  horizon text not null,
  score numeric(10,4) not null,
  confidence_band text not null check (confidence_band in ('Low', 'Moderate', 'High')),
  evidence_summary text not null,
  rationale jsonb not null default '{}'::jsonb,
  sample_size integer not null default 0,
  avg_return numeric(10,4) not null,
  median_return numeric(10,4) not null,
  win_rate numeric(10,4) not null,
  origin_type text not null check (origin_type in ('primary', 'explicit', 'inferred')),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create index if not exists signal_scores_event_id_idx
on public.signal_scores (event_id);

create index if not exists signal_scores_primary_ticker_idx
on public.signal_scores (primary_ticker);

create index if not exists signal_scores_target_ticker_idx
on public.signal_scores (target_ticker);

create index if not exists signal_scores_target_type_idx
on public.signal_scores (target_type);

create index if not exists signal_scores_horizon_idx
on public.signal_scores (horizon);

create index if not exists signal_scores_confidence_band_idx
on public.signal_scores (confidence_band);

create index if not exists signal_scores_score_desc_idx
on public.signal_scores (score desc);

drop trigger if exists set_signal_scores_updated_at on public.signal_scores;
create trigger set_signal_scores_updated_at
before update on public.signal_scores
for each row
execute function public.set_updated_at();
