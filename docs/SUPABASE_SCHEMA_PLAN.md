# Supabase Schema Plan

This document describes a first-pass schema for moving the StrattonAI UI from mock data to Supabase-backed reads. It is intentionally minimal and aimed at supporting the current frontend routes without blocking future normalization.

## `events`

Purpose: Store detected market-moving events shown in the dashboard and event feed.

Suggested columns:
- `id uuid not null default gen_random_uuid()`
- `headline text not null`
- `ticker text not null`
- `category text not null`
- `sentiment text not null`
- `timestamp timestamptz not null`
- `historical_analog text null`
- `sample_size integer null`
- `avg_return numeric(10,4) null`
- `details text null`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

Primary key:
- `id`

Useful indexes:
- `events_ticker_idx` on `ticker`
- `events_category_idx` on `category`
- `events_timestamp_desc_idx` on `timestamp desc`
- `events_sentiment_idx` on `sentiment`

Future expansion notes:
- Add source metadata such as `source_system`, `source_url`, and `dedupe_hash`.
- Consider a JSONB `tags` column for taxonomy labels.
- If event clustering becomes important, add `cluster_id` or a separate linking table.

## `related_companies`

Purpose: Represent company-to-company relationships and optional event-specific related-company links.

Suggested columns:
- `id uuid not null default gen_random_uuid()`
- `event_id uuid null references events(id) on delete cascade`
- `source_ticker text not null`
- `target_ticker text not null`
- `name text null`
- `relationship text not null`
- `strength numeric(5,4) null`
- `created_at timestamptz not null default now()`

Primary key:
- `id`

Useful indexes:
- `related_companies_event_id_idx` on `event_id`
- `related_companies_source_ticker_idx` on `source_ticker`
- `related_companies_target_ticker_idx` on `target_ticker`
- `related_companies_source_target_idx` on `(source_ticker, target_ticker)`

Future expansion notes:
- Split event-specific links and long-lived company graph edges into separate tables if semantics diverge.
- Add `relationship_confidence` or provenance columns if this graph is model-generated.

## `research_insights`

Purpose: Store compact insight cards summarizing patterns detected across historical events.

Suggested columns:
- `id uuid not null default gen_random_uuid()`
- `title text not null`
- `summary text not null`
- `confidence text not null`
- `event_count integer not null default 0`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

Primary key:
- `id`

Useful indexes:
- `research_insights_confidence_idx` on `confidence`
- `research_insights_created_at_desc_idx` on `created_at desc`

Future expansion notes:
- Add references to supporting events or studies through join tables.
- Add authoring metadata such as `generated_by`, `reviewed_by`, and `review_status`.

## `journal_entries`

Purpose: Store research journal items shown in the expandable journal UI.

Suggested columns:
- `id uuid not null default gen_random_uuid()`
- `date date not null`
- `title text not null`
- `events jsonb not null default '[]'::jsonb`
- `patterns text not null`
- `hypothesis text not null`
- `confidence text not null`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

Primary key:
- `id`

Useful indexes:
- `journal_entries_date_desc_idx` on `date desc`
- `journal_entries_confidence_idx` on `confidence`
- `journal_entries_events_gin_idx` using `gin (events)`

Future expansion notes:
- Add links to event IDs instead of only storing human-readable event names.
- Support richer entry content with `body_markdown` or `body_json`.

## `paper_trades`

Purpose: Store simulated trade ideas and their current status for the paper trade tracker.

Suggested columns:
- `id uuid not null default gen_random_uuid()`
- `ticker text not null`
- `direction text not null`
- `signal text not null`
- `entry_price numeric(12,4) not null`
- `current_price numeric(12,4) null`
- `entry_date date not null`
- `quantity numeric(18,4) not null`
- `status text not null`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

Primary key:
- `id`

Useful indexes:
- `paper_trades_ticker_idx` on `ticker`
- `paper_trades_status_idx` on `status`
- `paper_trades_entry_date_desc_idx` on `entry_date desc`

Future expansion notes:
- Add exit fields such as `exit_price`, `exit_date`, and realized P&L.
- If daily equity curves are needed, add a separate `paper_trade_snapshots` table rather than overloading this table.

## `company_profiles`

Purpose: Store company metadata used by the company research page.

Suggested columns:
- `id uuid not null default gen_random_uuid()`
- `ticker text not null unique`
- `name text not null`
- `sector text null`
- `industry text null`
- `market_cap text null`
- `pe numeric(12,4) null`
- `revenue text null`
- `employees text null`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

Primary key:
- `id`

Useful indexes:
- `company_profiles_ticker_uidx` unique on `ticker`
- `company_profiles_sector_idx` on `sector`
- `company_profiles_industry_idx` on `industry`

Future expansion notes:
- If numeric analytics are required, consider splitting display strings like `market_cap` and `revenue` into machine-readable numeric columns plus display formatting in the UI.
- Add identifiers such as CIK, LEI, ISIN, or exchange code later if the broader Bentlas ecosystem needs them.

## `event_study_results`

Purpose: Store historical event-study summary rows used by the event study explorer.

Suggested columns:
- `id uuid not null default gen_random_uuid()`
- `event_type text not null`
- `horizon text not null`
- `avg_return numeric(10,4) not null`
- `win_rate numeric(10,4) not null`
- `sample_size integer not null`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

Primary key:
- `id`

Useful indexes:
- `event_study_results_event_type_idx` on `event_type`
- `event_study_results_horizon_idx` on `horizon`
- `event_study_results_event_type_horizon_uidx` unique on `(event_type, horizon)`

Future expansion notes:
- Add related dimensions such as `primary_ticker`, `related_ticker`, `sector`, or `market_regime`.
- If the UI later needs distribution points or forward curves from the database, create dedicated child tables keyed by study ID.
