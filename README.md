# StrattonAI

StrattonAI is a deterministic market-research system with a React/Vite/Tailwind UI and a local-first research pipeline behind it. The UI keeps its existing terminal-style layout and mock fallback behavior, while the backend side now ingests structured event data, classifies it with rule-based taxonomy logic, expands related entities from a canonical graph, computes historical event studies, scores signals, and persists the outputs in Supabase.

## Current Status

As of the latest verified pass:

- Events in Supabase: `2317`
- Financial-news rows normalized through the deterministic pipeline: `2274`
- Stored `financial_news_local` rows: `2235`
- Additional normalized rows unlocked by the Tata Motors mapping expansion: `289`
- Additional stored `financial_news_local` rows unlocked by the mapping expansion: `287`
- Detailed event-study rows: `1217`
- UI event-study summary rows: `40`
- Valid forward-return observations: `17747`
- Signals: `1620`
- Confidence bands: `High 148`, `Moderate 213`, `Low 1259`
- Extended local price coverage max date: `2026-03-13`
- Events still missing primary price history: `287` (currently all `TTM`)

Category counts after the evidence-quality pass:

- `Macro Event`: `1117`
- `Product Launch`: `395`
- `Legal/Regulatory`: `219`
- `Earnings`: `201`
- `Capital Expenditure`: `189`
- `Supply Disruption`: `144`
- `Regulatory Approval`: `37`
- `Partnership`: `15`

## What Exists Today

### Frontend

- Vite + React + TypeScript + TailwindCSS
- Pages preserved:
  - Dashboard
  - Event Feed
  - Companies
  - Event Studies
  - Research Journal
  - Paper Trades
  - Settings
- Supabase-backed service layer with graceful mock fallback
- React Query data loading
- Functional Settings page persisted in local storage and wired into runtime behavior
- AI Trader dashboard shell with:
  - company search
  - company briefing
  - top-signal and research widgets
  - local AI chat panel wired for grounded responses through a repo-local gateway

### What is the current potential of the program? What can it do?

Today StrattonAI can operate as a real research workstation rather than a static mock dashboard.

- It can ingest structured market events, SEC filings, and local financial-news data through one deterministic normalization path.
- It can classify those events with explainable rules, store rationale, and attach explicit plus inferred related companies from the canonical relationship graph.
- It can compute forward-return studies across standard horizons, persist the results, and reuse those results to score current opportunities.
- It can rank signals for primary and related tickers, expose those signals in the UI, and show live event-study and signal data when Supabase is available.
- It can run coverage audits, generate targeted backfill plans, and report where the evidence base is still weak.
- It can power a local AI-assisted trader workspace: the AI Trader shell, company briefing view, and chat panel can now read grounded research context instead of operating as an isolated mock interface.

What it still does not do by design:

- It does not use opaque model scoring to replace the deterministic research pipeline.
- It does not require live market APIs during normal research runs once local datasets are built.
- It does not auto-trade or place broker orders as part of the current production workflow.
- It does not yet have complete price coverage for every mapped ticker, with `TTM` still the main uncovered gap.

### Deterministic Research Pipeline

- Structured ingestion for:
  - market events
  - SEC filings
  - local financial news
- Centralized taxonomy and rule-based classification
- Canonical company relationship graph plus deterministic entity expansion
- Historical event-study engine with persisted statistics
- Deterministic signal scoring
- Historical backfill workflow
- Coverage audit, low-confidence diagnostics, and targeted backfill planning
- Shared local price resolver with Parquet-first loading
- Massive-backed local historical price backfill

### Local AI Layer

- Repo-local model storage under `models/`
- Local Ollama-backed chat gateway for the AI Trader dashboard
- Grounded context assembly from:
  - company profiles
  - events
  - signal scores
  - event-study statistics
  - research insights
  - relationship graph data
- Deterministic structured fallback when Ollama or a model is unavailable
- Semantic retrieval and reranking now use local `bge-m3` and `bge-reranker-v2-m3`
- Current semantic runtime default: `cpu` to avoid GPU contention with Ollama

## Core Architecture

### UI and Services

- `src/services/`
  - Supabase-first domain services with mock fallback
- `src/models/` and `src/types/`
  - Typed models used by the UI
- `src/engine/`
  - Lightweight frontend-side helpers used by the UI and settings behavior

### Ingestion

- `ingestion/`
  - source loaders
  - source-specific deterministic mappers
  - shared normalization boundary
  - shared taxonomy and classification rules
  - Supabase writer with idempotent upsert behavior

### Research

- `research/`
  - price dataset resolution
  - Massive price backfill
  - event-study computation
  - signal scoring
  - coverage audit
  - low-confidence diagnostics
  - targeted backfill planning
  - before/after comparison reporting

### Database

- `supabase/sql/`
  - deterministic schema and seed files
  - additive migrations for studies, signals, and relationship graph support

## Determinism and Idempotency

StrattonAI is intentionally built so the same inputs produce the same outputs.

- Source identity is preserved with `source_name + source_record_id`.
- Ingestion reruns do not duplicate rows.
- Classification is rules-based and source-agnostic.
- Related-company expansion is graph-based and explainable.
- Event-study recompute and signal rescoring are reproducible from stored events plus local price files.
- Price-heavy workflows use local persisted files, not live price APIs at runtime.
- Mock fallback remains available for the UI when Supabase data is missing or partially populated.

## Canonical Local Datasets

### Financial News Events

Canonical source:

- `../data/events/financialNews/financial_news_events.csv`

Alternate representations are intentionally not double-ingested:

- `financial_news_events.json`
- `financial_news_events.xlsx`

Latest dataset inspection summary:

- Rows: `3024`
- Date range: `2025-02-01` -> `2025-08-14`
- Duplicate rows: `0`
- Missing headlines: `148`
- Supported deterministic company mappings:
  - `Apple Inc.` -> `AAPL`
  - `Boeing` -> `BA`
  - `ExxonMobil` -> `XOM`
  - `Goldman Sachs` -> `GS`
  - `JP Morgan Chase` -> `JPM`
  - `Microsoft` -> `MSFT`
  - `Tata Motors` -> `TTM` using the NYSE ADR as the project’s canonical tradable line
  - `Tesla` -> `TSLA`
- Currently skipped as unsupported deterministic mappings:
  - `Samsung Electronics`
  - `Reliance Industries`

Normalized financial-news results:

- Input rows: `3024`
- Normalized events: `2274`
- Skipped rows: `750`
- Failed rows: `0`

### Local Price Datasets

Default resolution order:

1. Explicit `--price-file`
2. `../data/prices/all_stock_data_extended_enriched.parquet`
3. `../data/prices/all_stock_data_extended.parquet`
4. `../data/prices/all_stock_data.parquet`
5. `../data/prices/all_stock_data_extended_enriched.csv`
6. `../data/prices/all_stock_data_extended.csv`
7. `../data/prices/all_stock_data.csv`
8. Sample JSON fallback only where the existing architecture intentionally allows it

Massive backfill outputs:

- `../data/prices/backfills/massive_daily_backfill.csv`
- `../data/prices/backfills/massive_daily_backfill.parquet`
- `../data/prices/all_stock_data_extended.csv`
- `../data/prices/all_stock_data_extended.parquet`

Papers With Backtest integration:

- `../data/DoWeLikeThis/StocksDailyPrice-PapersWithBacktest/`
- `../data/prices/backfills/paperswithbacktest_daily_backfill.csv`
- `../data/prices/backfills/paperswithbacktest_daily_backfill.parquet`
- `../data/prices/all_stock_data_extended_enriched.csv`
- `../data/prices/all_stock_data_extended_enriched.parquet`

Latest validated price coverage:

- Base local dataset max date: `2024-11-04`
- Extended local dataset max date: `2026-03-13`
- Backfill rows fetched: `7098`
- Covered requested tickers after merge: `21`
- Uncovered requested tickers after merge in the main extended dataset: none
- Current uncovered mapped ticker during the evidence-quality pass: `TTM`

## Key Reports

Generated reports are written under `reports/`. Current high-signal outputs include:

- `financial_news_dataset_inspection.json`
- `massive_price_backfill.json`
- `paperswithbacktest_price_import.json`
- `external_price_gap_fill.json`
- `financial_news_alignment_diff.json`
- `daily_prices_load.json`
- `coverage_audit.json`
- `coverage_audit_after_news_alignment.json`
- `low_confidence_diagnostics.json`
- `targeted_backfill_plan.json`

Useful current before/after diff:

- `reports/financial_news_alignment_diff.md`
- `reports/evidence_quality_pass_diff.md`

## Main Workflows

Run commands from `C:\Users\tlben\Bentlas\StrattonAI\ui`.

### 1. Inspect the local financial-news dataset

```powershell
python -m ingestion.inspect_financial_news_dataset
```

### 2. Ingest the local financial-news dataset

```powershell
python -m ingestion.run_ingestion --source-type financial-news
```

### 3. Backfill local price history from Massive

This uses credentials from `.env` and writes local CSV + Parquet artifacts. It does not make research runs depend on live API access after files are built.

```powershell
python -m research.massive_price_backfill
```

### 4. Load price history into Supabase

This bootstraps the `daily_prices` table if needed and upserts the locally resolved Parquet/CSV dataset for frontend price charts.

```powershell
python -m research.load_prices_to_supabase --bootstrap-schema --study-universe
```

### 5. Import Papers With Backtest stock prices into the local price layer

This checks whether the Papers With Backtest stock dataset adds missing rows for the current StrattonAI study universe and writes a report. If it finds new rows, it builds an enriched local dataset that the shared resolver will prefer automatically.

```powershell
python -m research.import_paperswithbacktest_prices --dry-run
```

### 6. Attempt to fill uncovered study tickers from external keyed providers

This tries the configured provider stack in deterministic order and merges successful rows into the enriched local dataset that the shared resolver already prefers.

```powershell
python -m research.fill_external_price_gap --ticker TTM --dry-run
```

### 7. Run the full financial-news alignment workflow

This inspects the news dataset, ingests normalized events, optionally backfills prices, recomputes studies, rescores signals, reruns the audit, and rebuilds the planner.

```powershell
python -m research.run_financial_news_alignment
```

To reuse existing extended local price files without calling Massive again:

```powershell
python -m research.run_financial_news_alignment --skip-backfill
```

### 8. Run the precision evidence-quality pass

This reruns the financial-news alignment inputs, applies the quality-focused targeted wave, recomputes studies, rescales signals, and regenerates diagnostics and planner outputs.

```powershell
python -m research.run_precision_evidence_quality_pass
```

### 9. Recompute event studies only

```powershell
python -m research.recompute_all_event_studies
```

### 10. Rescore signals only

```powershell
python -m research.rescore_all_recent_events
```

### 11. Rerun audit and planner

```powershell
python -m research.generate_gap_report
python -m research.build_targeted_backfill_plan
python -m research.generate_low_confidence_diagnostics
```

## Desktop Launcher

StrattonAI now includes a Windows launcher that starts the built UI locally and opens it in your default browser.

### Create the desktop shortcut

```powershell
npm run desktop:shortcut
```

This creates `StrattonAI.lnk` on your Desktop and points it at the repo-local launcher script.

### Start StrattonAI from the terminal

```powershell
npm run start:desktop
```

Behavior:

- uses the existing production build in `dist`
- runs `npm run build` automatically if `dist` is missing or if `src/`, `public/`, or the root Vite entry files are newer than the current build
- starts `vite preview` on `http://127.0.0.1:4173` when that port is free
- automatically uses the next available local port if `4173` is already occupied by a different project
- opens the app in your default browser
- reuses the existing local StrattonAI preview server if it is already running

### Stop the local preview server

```powershell
npm run stop:desktop
```

## Local AI Gateway

The AI Trader dashboard chat panel now talks to a repo-local gateway that reads grounded research context and then calls the local Ollama model when available.

### Start the local AI gateway

```powershell
npm run ai:start
```

This will:

- start Ollama if needed
- start the local HTTP gateway on `http://127.0.0.1:8787`
- use `qwen2.5:14b-instruct` by default
- use semantic retrieval + reranking when the local AI runtime is installed
- fall back to deterministic structured responses if Ollama or the semantic runtime is unavailable

### Stop the local AI gateway

```powershell
npm run ai:stop
```

### Current retrieval mode

- Current production path: semantic retrieval over grounded Supabase research context, reranked locally before prompting Qwen
- Deterministic fallback path: structured retrieval when semantic runtime dependencies are unavailable
- The gateway health endpoint reports the active retrieval mode and semantic runtime readiness

### Local AI runtime packages

If the embedded Python runtime needs to be rebuilt on another machine, install:

```powershell
C:\Users\tlben\.lmstudio\extensions\backends\vendor\_amphibian\cpython3.11-win-x86@6\python.exe -m pip install -r research\requirements-local-ai.txt
```

## Testing and Build

### Python Research Tests

```powershell
python -m unittest discover -s research\tests -p "test_*.py"
```

### Python Ingestion Tests

```powershell
python -m unittest discover -s ingestion\tests -p "test_*.py"
```

### Frontend Tests

```powershell
npm test
```

### Production Build

```powershell
npm run build
```

## Important Implementation Notes

- Secrets stay in `.env`. Do not hardcode or print them.
- Massive is used only to build local historical files.
- Supabase remains the first persistent backend for events, studies, signals, and UI-facing data.
- Study and signal persistence now use full-sync recompute semantics, so stale historical rows do not survive after a clean recompute.
- Explicit related-company rows remain preferred over inferred ones.
- UI mock fallback is intentionally retained during this phase.

## Current Bottlenecks

The system is now research-capable, but the evidence base is still uneven.

- `Partnership` remains the thinnest category.
- `TTM` is now mapped deterministically, but it still has no local price rows, so 287 Tata-linked events cannot yet contribute study observations.
- `Product Launch` and `Legal/Regulatory` still generate many low-confidence signals.
- Several exact relationship slices remain narrow:
  - `Legal/Regulatory / GOOGL / Sector Peer`
  - `Capital Expenditure / ORCL / Sector Peer`
  - `Partnership / TSM / Supplier`
  - `Partnership / MSFT / Customer`
  - `Legal/Regulatory / META / Sector Peer`
  - `Partnership / AVGO / Sector Peer`
  - `Capital Expenditure / AMZN / Competitor`
  - `Product Launch / GOOGL / Competitor`
  - `Product Launch / TSM / Supplier`
  - `Product Launch / AMD / Competitor`
- For several of those slices, the new diagnostics show the blocker is now weak edge quality rather than depth alone.
- Remaining follow-up work should focus on targeted historical coverage quality and TTM price coverage, not new scoring formulas.

## Recommended Next Step

The next highest-value pass is a targeted historical expansion wave focused on:

- remaining narrow exact relationship slices
- deeper `Partnership` coverage
- better `Product Launch` exact related-company slices
- TTM local price coverage so the unlocked Tata Motors news corpus can contribute to studies and signals

## Operator Notes

- If you explicitly pass `--price-file`, that path wins.
- If you do not pass `--price-file`, the shared resolver prefers local extended Parquet automatically.
- Financial-news ingestion is safe to rerun.
- Massive price backfill is safe to rerun.
- Study recompute, signal rescoring, audit generation, and planner generation are all deterministic batch operations.
