# StrattonAI Agent Guide

This file is a concise guide for future coding agents or operators working inside the StrattonAI UI repository.

## Purpose

StrattonAI is a deterministic market-research system. The frontend is a React/Vite/Tailwind application, but the core product value comes from the local Python research pipeline and its Supabase-backed outputs.

Agents working in this repo should preserve that design:

- deterministic ingestion
- explainable classification and scoring
- rerunnable local workflows
- idempotent database writes
- mock fallback in the UI when live data is absent

## Working Principles

- Prefer extending the existing ingestion, research, and service layers instead of adding parallel systems.
- Keep classification, relationship expansion, event studies, and signal scoring explainable.
- Do not replace deterministic scoring with opaque AI logic.
- Keep secrets in `.env` only.
- Treat local datasets and Supabase tables as the source of truth for research artifacts.
- Preserve the current UI structure and branding unless a task explicitly calls for UI changes.

## High-Level Architecture

### Frontend

- `src/pages/`: route-level screens
- `src/components/`: shared UI building blocks
- `src/services/`: Supabase-first service layer with mock fallback
- `src/models/` and `src/types/`: typed frontend models
- `src/hooks/`: local UI state such as dashboard mode and trading mode

### Ingestion

- `ingestion/`: deterministic source loaders, source mappers, normalization boundary, taxonomy rules, relationship expansion, and Supabase writers

### Research

- `research/`: price loading, local backfills, event studies, signal scoring, coverage audits, targeted backfill planning, AI grounding, migration verification, health checks, risk gating, order preview, and local model gateway support

### Database

- `supabase/sql/`: additive schema migrations and seeds

### Local Models

- `models/ollama/`: local Ollama model store
- `models/huggingface/`: local retrieval and reranker models

## Key Runtime Flows

### Research pipeline

1. Ingest source data into normalized `events` and `related_companies`
2. Compute event studies from stored events plus local price history
3. Score recent events into `signal_scores`
4. Audit coverage and generate backfill priorities

### UI data flow

1. UI services query Supabase
2. If live tables are unavailable or empty, services fall back to mock data where supported
3. AI Trader components use grounded research context from the local AI gateway, and the company briefing / trader cards should prefer the shared gateway briefing payload over ad hoc parallel queries.

## Important Current Constraints

- `Partnership` remains the thinnest major event category.
- `Product Launch` and `Legal/Regulatory` still generate many low-confidence slices.
- The local AI layer is active, but the system should still function without the gateway running.
- Trader-side schema stages `009` through `013` may exist in code before they exist in the connected Supabase instance. Use the verifier before assuming those tables/columns are present.

## Useful Commands

Run from the repo root:

```powershell
python -m ingestion.run_ingestion --source-type financial-news
python -m research.recompute_all_event_studies
python -m research.rescore_all_recent_events
python -m research.generate_gap_report
python -m research.build_targeted_backfill_plan
python -m research.generate_low_confidence_diagnostics
python -m supabase.scripts.apply_and_verify_migrations --dry-run
python -m research.health_check
python -m research.fill_study_universe_gaps --ticker SPY --auto-recompute
python -m research.partnership_backfill_helper
python -m ingestion.build_n8n_handoff_bundles
npm run build
npm test
npm run ai:start
npm run ai:stop
```

## Related Docs

- `README.md`
- `docs/blueprint.md`
- `docs/roadmap.md`
- `docs/EVENT_INGESTION_FLOW.md`
- `docs/EVENT_STUDY_ENGINE.md`
- `docs/SIGNAL_SCORING_ENGINE.md`
- `docs/RELATIONSHIP_GRAPH_AND_ENTITY_EXPANSION.md`
- `docs/N8N_TARGETED_BACKFILL_WORKFLOW.md`
