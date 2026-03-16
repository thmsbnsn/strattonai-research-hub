create extension if not exists pgcrypto;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

create table if not exists public.events (
  id uuid primary key default gen_random_uuid(),
  source_name text,
  source_record_id text,
  headline text not null,
  ticker text not null,
  category text not null,
  sentiment text not null check (sentiment in ('positive', 'negative', 'neutral')),
  timestamp timestamptz not null,
  historical_analog text,
  sample_size integer not null default 0,
  avg_return numeric(10,4) not null default 0,
  details text,
  metadata jsonb not null default '{}'::jsonb,
  ingested_at timestamptz not null default timezone('utc', now()),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.related_companies (
  id uuid primary key default gen_random_uuid(),
  event_id uuid references public.events(id) on delete cascade,
  source_ticker text not null,
  target_ticker text not null,
  name text,
  relationship text not null,
  strength numeric(5,4),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.research_insights (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  summary text not null,
  confidence text not null check (confidence in ('High', 'Moderate', 'Low')),
  event_count integer not null default 0,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.journal_entries (
  id uuid primary key default gen_random_uuid(),
  date date not null,
  title text not null,
  events jsonb not null default '[]'::jsonb,
  patterns text not null,
  hypothesis text not null,
  confidence text not null check (confidence in ('High', 'Moderate', 'Low')),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.paper_trades (
  id uuid primary key default gen_random_uuid(),
  ticker text not null,
  direction text not null check (direction in ('Long', 'Short')),
  signal text not null,
  entry_price numeric(12,4) not null,
  current_price numeric(12,4),
  entry_date date not null,
  quantity numeric(18,4) not null,
  status text not null check (status in ('Open', 'Closed')),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.company_profiles (
  id uuid primary key default gen_random_uuid(),
  ticker text not null unique,
  name text not null,
  sector text,
  industry text,
  market_cap text,
  pe numeric(12,4),
  revenue text,
  employees text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.event_study_results (
  id uuid primary key default gen_random_uuid(),
  event_type text not null,
  horizon text not null,
  avg_return numeric(10,4) not null,
  win_rate numeric(10,4) not null,
  sample_size integer not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint event_study_results_event_type_horizon_key unique (event_type, horizon)
);

create index if not exists events_ticker_idx on public.events (ticker);
create index if not exists events_category_idx on public.events (category);
create index if not exists events_timestamp_desc_idx on public.events (timestamp desc);
create index if not exists events_sentiment_idx on public.events (sentiment);
create unique index if not exists events_source_identity_uidx
on public.events (source_name, source_record_id)
where source_name is not null and source_record_id is not null;

create index if not exists related_companies_event_id_idx on public.related_companies (event_id);
create index if not exists related_companies_source_ticker_idx on public.related_companies (source_ticker);
create index if not exists related_companies_target_ticker_idx on public.related_companies (target_ticker);
create index if not exists related_companies_source_target_idx on public.related_companies (source_ticker, target_ticker);

create index if not exists research_insights_confidence_idx on public.research_insights (confidence);
create index if not exists research_insights_created_at_desc_idx on public.research_insights (created_at desc);

create index if not exists journal_entries_date_desc_idx on public.journal_entries (date desc);
create index if not exists journal_entries_confidence_idx on public.journal_entries (confidence);
create index if not exists journal_entries_events_gin_idx on public.journal_entries using gin (events);

create index if not exists paper_trades_ticker_idx on public.paper_trades (ticker);
create index if not exists paper_trades_status_idx on public.paper_trades (status);
create index if not exists paper_trades_entry_date_desc_idx on public.paper_trades (entry_date desc);

create index if not exists company_profiles_sector_idx on public.company_profiles (sector);
create index if not exists company_profiles_industry_idx on public.company_profiles (industry);

create index if not exists event_study_results_event_type_idx on public.event_study_results (event_type);
create index if not exists event_study_results_horizon_idx on public.event_study_results (horizon);

drop trigger if exists set_events_updated_at on public.events;
create trigger set_events_updated_at
before update on public.events
for each row
execute function public.set_updated_at();

drop trigger if exists set_related_companies_updated_at on public.related_companies;
create trigger set_related_companies_updated_at
before update on public.related_companies
for each row
execute function public.set_updated_at();

drop trigger if exists set_research_insights_updated_at on public.research_insights;
create trigger set_research_insights_updated_at
before update on public.research_insights
for each row
execute function public.set_updated_at();

drop trigger if exists set_journal_entries_updated_at on public.journal_entries;
create trigger set_journal_entries_updated_at
before update on public.journal_entries
for each row
execute function public.set_updated_at();

drop trigger if exists set_paper_trades_updated_at on public.paper_trades;
create trigger set_paper_trades_updated_at
before update on public.paper_trades
for each row
execute function public.set_updated_at();

drop trigger if exists set_company_profiles_updated_at on public.company_profiles;
create trigger set_company_profiles_updated_at
before update on public.company_profiles
for each row
execute function public.set_updated_at();

drop trigger if exists set_event_study_results_updated_at on public.event_study_results;
create trigger set_event_study_results_updated_at
before update on public.event_study_results
for each row
execute function public.set_updated_at();
