create table if not exists public.event_study_statistics (
  id uuid primary key default gen_random_uuid(),
  study_key text not null unique,
  study_target_type text not null check (study_target_type in ('category_summary', 'primary', 'relationship', 'related')),
  event_category text not null,
  primary_ticker text,
  related_ticker text,
  relationship_type text,
  horizon text not null,
  sample_size integer not null default 0,
  avg_return numeric(10,4) not null,
  median_return numeric(10,4) not null,
  win_rate numeric(10,4) not null,
  notes text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create index if not exists event_study_statistics_event_category_idx
on public.event_study_statistics (event_category);

create index if not exists event_study_statistics_horizon_idx
on public.event_study_statistics (horizon);

create index if not exists event_study_statistics_target_type_idx
on public.event_study_statistics (study_target_type);

create index if not exists event_study_statistics_primary_ticker_idx
on public.event_study_statistics (primary_ticker);

create index if not exists event_study_statistics_related_ticker_idx
on public.event_study_statistics (related_ticker);

create index if not exists event_study_statistics_relationship_type_idx
on public.event_study_statistics (relationship_type);

drop trigger if exists set_event_study_statistics_updated_at on public.event_study_statistics;
create trigger set_event_study_statistics_updated_at
before update on public.event_study_statistics
for each row
execute function public.set_updated_at();
