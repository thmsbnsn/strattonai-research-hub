-- Persist local daily OHLCV price history for UI charts and research-side reuse.
-- Safe to rerun: the table and indexes are created with if-not-exists guards.

create table if not exists public.daily_prices (
  id uuid primary key default gen_random_uuid(),
  ticker text not null,
  trade_date date not null,
  open numeric(14,4),
  high numeric(14,4),
  low numeric(14,4),
  close numeric(14,4) not null,
  volume bigint,
  dividends numeric(14,6),
  stock_splits numeric(14,6),
  created_at timestamptz not null default timezone('utc', now()),
  constraint daily_prices_ticker_date_key unique (ticker, trade_date)
);

create index if not exists daily_prices_ticker_idx
on public.daily_prices (ticker);

create index if not exists daily_prices_trade_date_desc_idx
on public.daily_prices (trade_date desc);

create index if not exists daily_prices_ticker_date_idx
on public.daily_prices (ticker, trade_date);
