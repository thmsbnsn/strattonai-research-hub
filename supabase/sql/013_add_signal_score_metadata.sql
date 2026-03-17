-- Add signal metadata storage for regime-aware and trader-side annotations.
-- Safe to rerun: the jsonb column is created with an if-not-exists guard.

alter table public.signal_scores
add column if not exists metadata jsonb not null default '{}'::jsonb;
