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
2. `../data/prices/all_stock_data_extended.parquet`
3. `../data/prices/all_stock_data.parquet`
4. `../data/prices/all_stock_data_extended.csv`
5. `../data/prices/all_stock_data.csv`
6. Sample JSON fallback only where the existing architecture intentionally allows it

Massive backfill outputs:

- `../data/prices/backfills/massive_daily_backfill.csv`
- `../data/prices/backfills/massive_daily_backfill.parquet`
- `../data/prices/all_stock_data_extended.csv`
- `../data/prices/all_stock_data_extended.parquet`

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
- `financial_news_alignment_diff.json`
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

### 4. Run the full financial-news alignment workflow

This inspects the news dataset, ingests normalized events, optionally backfills prices, recomputes studies, rescores signals, reruns the audit, and rebuilds the planner.

```powershell
python -m research.run_financial_news_alignment
```

To reuse existing extended local price files without calling Massive again:

```powershell
python -m research.run_financial_news_alignment --skip-backfill
```

### 5. Run the precision evidence-quality pass

This reruns the financial-news alignment inputs, applies the quality-focused targeted wave, recomputes studies, rescales signals, and regenerates diagnostics and planner outputs.

```powershell
python -m research.run_precision_evidence_quality_pass
```

### 6. Recompute event studies only

```powershell
python -m research.recompute_all_event_studies
```

### 7. Rescore signals only

```powershell
python -m research.rescore_all_recent_events
```

### 8. Rerun audit and planner

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
- runs `npm run build` automatically if `dist` is missing
- starts `vite preview` on `http://127.0.0.1:4173`
- opens the app in your default browser
- reuses the existing local preview server if it is already running

### Stop the local preview server

```powershell
npm run stop:desktop
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
