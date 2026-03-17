-- Persist deterministic market-regime snapshots for regime-aware research workflows.
-- Safe to rerun: the table and unique date key are created with if-not-exists guards.

create table if not exists public.market_regimes (
  id uuid not null default gen_random_uuid(),
  as_of_date date not null unique,
  regime_label text not null,
  spy_price numeric(12,4),
  sma_200 numeric(12,4),
  sma_50 numeric(12,4),
  vol_20d numeric(8,6),
  drawdown_from_high numeric(8,6),
  created_at timestamptz not null default timezone('utc', now()),
  primary key (id)
);

create index if not exists market_regimes_as_of_date_desc_idx
on public.market_regimes (as_of_date desc);
