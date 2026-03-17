-- Persist deterministic portfolio-construction runs for the trader workspace.
-- Safe to rerun: table and indexes are created with if-not-exists guards.

create table if not exists public.portfolio_allocations (
  id uuid not null default gen_random_uuid(),
  run_id uuid not null default gen_random_uuid(),
  method text not null,
  ticker text not null,
  allocation_dollars numeric(18,4) not null,
  weight numeric(8,6) not null,
  signal_key text,
  capital_total numeric(18,4) not null,
  created_at timestamptz not null default timezone('utc', now()),
  primary key (id)
);

create index if not exists portfolio_allocations_run_id_idx
on public.portfolio_allocations (run_id);

create index if not exists portfolio_allocations_ticker_idx
on public.portfolio_allocations (ticker);
