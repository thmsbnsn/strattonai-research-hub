alter table public.events
add column if not exists source_name text,
add column if not exists source_record_id text,
add column if not exists metadata jsonb not null default '{}'::jsonb,
add column if not exists ingested_at timestamptz not null default timezone('utc', now());

create unique index if not exists events_source_identity_uidx
on public.events (source_name, source_record_id)
where source_name is not null and source_record_id is not null;
