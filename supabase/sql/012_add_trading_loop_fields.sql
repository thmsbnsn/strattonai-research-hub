-- Extend paper_trades for trading-loop and broker-linked tracking.
-- Safe to rerun: columns and indexes are created with if-not-exists guards.

alter table public.paper_trades
add column if not exists alpaca_order_id text;

alter table public.paper_trades
add column if not exists exit_price numeric(12,4);

alter table public.paper_trades
add column if not exists exit_date date;

alter table public.paper_trades
add column if not exists realized_pnl numeric(18,4);

alter table public.paper_trades
add column if not exists universe text not null default 'main';

create index if not exists paper_trades_mode_idx
on public.paper_trades (mode);

create index if not exists paper_trades_universe_idx
on public.paper_trades (universe);
