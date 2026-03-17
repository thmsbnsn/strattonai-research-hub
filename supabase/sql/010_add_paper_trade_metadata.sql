-- Expand paper_trades for deterministic simulation, risk, and metadata capture.
-- Safe to rerun: columns are added with if-not-exists guards and the status constraint is recreated deterministically.

alter table public.paper_trades
add column if not exists metadata jsonb not null default '{}'::jsonb;

alter table public.paper_trades
add column if not exists mode text not null default 'simulated';

do $$
begin
  if exists (
    select 1
    from pg_constraint
    where conname = 'paper_trades_status_check'
      and conrelid = 'public.paper_trades'::regclass
  ) then
    alter table public.paper_trades drop constraint paper_trades_status_check;
  end if;
end
$$;

alter table public.paper_trades
add constraint paper_trades_status_check
check (lower(status) in ('simulated', 'open', 'closed', 'risk-blocked'));
