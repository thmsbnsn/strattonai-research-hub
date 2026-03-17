# StrattonAI Blueprint

This document is the high-level system blueprint for StrattonAI. It explains how the major layers fit together and where the repo’s more detailed docs should be used.

## System Goal

StrattonAI is a deterministic event-intelligence and market-research platform. Its purpose is to turn structured event inputs and historical price data into explainable studies, ranked signals, and operator-facing research tools.

The system is intentionally not built around opaque model-driven trade decisions. AI sits on top of the research stack as a grounded interface layer, not as a replacement for classification or scoring.

## Major Layers

### 1. Data Ingestion

The ingestion layer converts raw structured sources into a normalized event boundary.

Current source families:

- market events
- SEC filings
- local financial news

Core responsibilities:

- validate source records
- preserve `source_name + source_record_id`
- normalize timestamps and tickers
- classify category and sentiment through shared taxonomy rules
- store classification rationale
- attach explicit and inferred related companies

Primary code area:

- `ingestion/`

Detailed references:

- `docs/EVENT_INGESTION_FLOW.md`
- `docs/SEC_INGESTION_FLOW.md`
- `docs/EVENT_TAXONOMY_AND_RULES.md`
- `docs/RELATIONSHIP_GRAPH_AND_ENTITY_EXPANSION.md`

### 2. Canonical Research Storage

Supabase is the first persistent backend for research outputs and UI-facing state.

Important tables include:

- `events`
- `related_companies`
- `company_relationship_graph`
- `company_profiles`
- `event_study_statistics`
- `event_study_results`
- `signal_scores`
- `daily_prices`
- `portfolio_allocations`
- `market_regimes`

Primary code area:

- `supabase/sql/`
- research writers in `research/`
- ingestion writers in `ingestion/`

Detailed references:

- `docs/SUPABASE_SCHEMA_PLAN.md`
- `docs/SUPABASE_SETUP_AND_SEED.md`

### 3. Historical Price Layer

The price layer is local-first and resolver-driven.

Design principles:

- prefer local Parquet
- keep runtime independent from live market APIs
- make backfills reproducible
- allow multiple local source datasets to enrich a preferred merged dataset

Current sources:

- base all-stock dataset
- Massive local historical backfills
- Papers With Backtest enrichment
- deterministic external gap-fill providers for uncovered study tickers

Primary code area:

- `research/price_dataset.py`
- `research/massive_price_backfill.py`
- `research/load_prices_to_supabase.py`
- `research/import_paperswithbacktest_prices.py`
- `research/fill_external_price_gap.py`
- `research/fill_study_universe_gaps.py`

### 4. Event Study Engine

The event-study layer links stored events to local price history and computes forward returns across fixed horizons.

Current standard horizons:

- `1D`
- `3D`
- `5D`
- `10D`
- `20D`

It persists:

- category summaries
- primary ticker studies
- related ticker studies
- relationship-level studies

Primary code area:

- `research/event_study_engine.py`
- `research/recompute_all_event_studies.py`

Detailed reference:

- `docs/EVENT_STUDY_ENGINE.md`

### 5. Signal Scoring

The signal layer takes current events plus stored event-study evidence and produces ranked, explainable signals.

Inputs include:

- event category
- target ticker
- relationship type
- sample size
- avg return
- median return
- win rate
- classifier confidence
- origin type
- recency

Primary code area:

- `research/signal_scoring.py`
- `research/rescore_all_recent_events.py`

Detailed reference:

- `docs/SIGNAL_SCORING_ENGINE.md`

### 6. Coverage Management

The coverage layer exists to keep the evidence base scientifically useful instead of drifting into ad hoc data collection.

It measures:

- category depth
- weak exact slices
- confidence concentration
- price gaps
- fallback-heavy study usage

It produces:

- coverage audits
- coverage diffs
- low-confidence diagnostics
- targeted backfill plans
- partnership backfill priorities

Primary code area:

- `research/coverage_audit.py`
- `research/generate_gap_report.py`
- `research/generate_low_confidence_diagnostics.py`
- `research/build_targeted_backfill_plan.py`

Detailed references:

- `docs/COVERAGE_AUDIT_AND_GAP_FILLING.md`
- `docs/HISTORICAL_BACKFILL_WORKFLOW.md`
- `docs/TARGETED_BACKFILL_PLANNING.md`
- `docs/N8N_TARGETED_BACKFILL_WORKFLOW.md`

### 6.5. n8n-Assisted Targeted Backfill

n8n is an optional research-collection layer for weak slices already ranked by the deterministic planner.

It is intentionally limited to:

- reading ranked slice targets
- building stable search tasks
- collecting candidate source metadata
- documenting evidence in the review bundle contract

It is intentionally not allowed to:

- classify final event types
- decide relationship truth
- write directly into research tables
- bypass idempotent ingestion

Repo-owned workflow and handoff artifacts:

- `automation/n8n/strattonai_targeted_backfill_research_workflow.json`
- `ingestion/templates/n8n_targeted_research_template.json`
- `ingestion/build_n8n_handoff_bundles.py`

That keeps n8n in the operator-assistance boundary while Python remains the source of truth.

### 7. Frontend Application

The frontend is a Supabase-first research UI with mock fallback preserved.

Main surfaces:

- Research Dashboard
- Event Feed
- Companies
- Event Studies
- Research Journal
- Paper Trades
- Settings
- AI Trader Dashboard shell
- shared gateway-backed company briefing payload reused by company briefing, trader cards, and chat

Frontend design rules:

- keep the existing terminal-style identity
- preserve routing and layout structure
- prefer service-layer reads over direct mock imports

Primary code area:

- `src/`

### 8. Local AI Layer

The local AI layer is an interface and retrieval layer, not the source of truth for research logic.

Current responsibilities:

- retrieve grounded research context
- rerank relevant evidence locally
- prompt the local chat model
- return cited answers to the AI Trader dashboard
- assemble a deterministic company-briefing payload with profile, events, relationships, studies, signals, and live-readiness guardrails
- fall back deterministically when the local model stack is unavailable
- expose trader-side gateway endpoints for health, risk, preview, portfolio, and loop controls

Model roles:

- Ollama chat model for analyst interaction
- `bge-m3` for semantic retrieval
- `bge-reranker-v2-m3` for reranking

### 9. Trader Safety And Operator Control

The trader layer sits on top of the research stack and remains explicitly guarded.

Current responsibilities:

- build deterministic order previews before any non-dry-run order path
- apply a unified hard risk gate
- keep live-mode execution behind explicit operator confirmation
- expose health, migration, loop-status, and gap-fill controls to the UI

Primary code area:

- `research/risk_gate.py`
- `research/order_preview.py`
- `research/trading_loop.py`
- `research/health_check.py`
- `supabase/scripts/apply_and_verify_migrations.py`

Primary code area:

- `research/local_ai_gateway.py`
- `research/semantic_retrieval.py`
- `src/components/trader/AIChatPanel.tsx`

## Operating Philosophy

StrattonAI works best when each layer remains narrow and explicit:

- ingestion normalizes
- taxonomy classifies
- graph logic expands relationships
- price files power studies
- studies power signals
- audits reveal gaps
- AI explains and helps navigate the evidence

That separation is the main reason the system remains reproducible and debuggable.
