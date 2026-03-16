create table if not exists public.company_relationship_graph (
  id uuid primary key default gen_random_uuid(),
  source_ticker text not null,
  source_name text,
  target_ticker text not null,
  target_name text,
  relationship_type text not null,
  strength numeric(5,4) not null default 0.5,
  is_directional boolean not null default true,
  notes text,
  provenance jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists company_relationship_graph_edge_uidx
on public.company_relationship_graph (source_ticker, target_ticker, relationship_type);

create index if not exists company_relationship_graph_source_idx
on public.company_relationship_graph (source_ticker);

create index if not exists company_relationship_graph_target_idx
on public.company_relationship_graph (target_ticker);

create index if not exists company_relationship_graph_relationship_type_idx
on public.company_relationship_graph (relationship_type);

alter table public.related_companies
  add column if not exists graph_relationship_id uuid references public.company_relationship_graph(id) on delete set null,
  add column if not exists relationship_type text,
  add column if not exists origin_type text not null default 'explicit',
  add column if not exists notes text,
  add column if not exists rationale jsonb not null default '{}'::jsonb;

update public.related_companies
set relationship_type = coalesce(relationship_type, relationship)
where relationship_type is null;

update public.related_companies
set rationale = jsonb_build_object(
  'origin',
  coalesce(origin_type, 'explicit'),
  'relationship_type',
  coalesce(relationship_type, relationship)
)
where rationale = '{}'::jsonb;

create unique index if not exists related_companies_event_edge_uidx
on public.related_companies (event_id, source_ticker, target_ticker, relationship_type)
where event_id is not null;

create index if not exists related_companies_origin_type_idx
on public.related_companies (origin_type);

create index if not exists related_companies_graph_relationship_id_idx
on public.related_companies (graph_relationship_id);

drop trigger if exists set_company_relationship_graph_updated_at on public.company_relationship_graph;
create trigger set_company_relationship_graph_updated_at
before update on public.company_relationship_graph
for each row
execute function public.set_updated_at();
