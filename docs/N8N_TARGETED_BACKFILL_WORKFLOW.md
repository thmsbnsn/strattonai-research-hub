# n8n Targeted Backfill Workflow

## Purpose

Use n8n as a deterministic research assistant for the weakest evidence slices already identified by StrattonAI.

n8n does not:

- classify events
- score signals
- persist directly into Supabase
- decide whether an example is valid on its own

n8n does:

- read ranked slice targets from the latest backfill plan
- run repeatable source lookups with stable queries
- capture candidate examples in a review bundle
- preserve exact source identity and evidence text

The Python/Supabase pipeline remains the source of truth for validation, normalization, taxonomy, event studies, scoring, and idempotent persistence.

## Inputs

- `reports/targeted_backfill_plan.json`
- `reports/coverage_audit.json`
- `reports/low_confidence_diagnostics.json`
- `ingestion/templates/n8n_targeted_research_template.json`
- optional existing starter outputs:
  - `ingestion/templates/targeted_market_events_template.json`
  - `ingestion/templates/targeted_sec_filings_template.json`

## Output Contract

n8n writes candidate research into:

- `ingestion/templates/n8n_targeted_research_template.json`
- repo starter workflow artifact:
  - `automation/n8n/strattonai_targeted_backfill_research_workflow.json`

Each record in that file is a slice-level work item plus zero or more collected examples. Every collected example stays `ready_for_ingestion=false` until a human or deterministic review step approves it.

## Workflow Stages

### 1. Read Priority Slices

Source of truth:

- `reports/targeted_backfill_plan.json`

Expected n8n step:

- Read the plan JSON from the repo or shared storage.
- Keep only the highest-priority items that are still unresolved.
- Copy stable planner fields into the research template:
  - `priority_rank`
  - `planner_score` -> `priority_score`
  - `source_gap_key`
  - `event_category`
  - `target_type`
  - `primary_ticker`
  - `related_ticker`
  - `relationship_type`
  - `current_sample_size` -> `current_sample_count`
  - `desired_min_sample_size` -> `desired_sample_count`
  - `gap_size`
  - `why_it_matters` -> `why_this_slice_matters`
  - `suggested_source_type`

Deterministic rule:

- n8n should not invent new slice targets. It should only work from the ranked planner output or a manually approved override list.

### 2. Generate Stable Search Tasks

Expected n8n step:

- For each target slice, populate `search_queries` with explicit search strings.
- Keep the queries stable and reproducible.
- Prefer exact company names, tickers, event-category terms, and relationship terms already implied by the plan.

Examples:

- `NVDA product launch site:news.example.com`
- `Meta antitrust ruling competitor Alphabet legal regulatory`
- `NVIDIA supplier TSMC partnership expansion press release`

Deterministic rule:

- Search text must be saved in the bundle.
- If the query changes, it should be a visible edit to the template, not hidden inside n8n.

### 3. Fetch Candidate Sources

Expected n8n step:

- Query approved sources or fetch approved source pages.
- Save candidate source metadata under `source_candidates`.
- Extract candidate fields into `collected_examples`.

Good source types:

- `market-events`
- `sec-filings`
- `press-release`
- `company-ir`
- `major-news`
- `exchange-announcement`

Deterministic rule:

- Every collected example must preserve:
  - `source_name`
  - `source_record_id`
  - `source_url`
  - `source_title`
  - `source_publisher`
  - `published_at`
  - evidence text used for review

### 4. Capture Evidence Into The Template

Expected n8n step:

- Create or update one `collected_examples` item per candidate event/filing.
- Fill only facts supported by the source.
- Leave unresolved fields blank or `null`.
- Set `ready_for_ingestion=false`.
- Set the slice `review_status` to `pending_review` when at least one candidate is present.

Deterministic rule:

- n8n may add `event_type_hint`, `sentiment_hint`, or `relationship_evidence` only as research hints.
- Final event type, sentiment, relationship mapping, and persistence happen later in the Python review/ingestion flow.

### 5. Manual Or Deterministic Review

Expected review step:

- Confirm the example is real, historical, and relevant to the target slice.
- Confirm primary and related company identity.
- Confirm the relationship path is explicit when required.
- Confirm the example is not already ingested.
- Flip `ready_for_ingestion=true` only after review.
- Update `review_status` to one of:
  - `approved_for_ingestion`
  - `rejected`
  - `needs_more_research`

Deterministic rule:

- Rejections and approvals should be recorded in `reviewer_notes`.

### 6. Handoff Into Existing Ingestion

After review:

- Approved market-event style examples move into `ingestion/templates/targeted_market_events_template.json` or a source-specific market-events bundle.
- Approved filing-style examples move into `ingestion/templates/targeted_sec_filings_template.json` or a source-specific sec-filings bundle.
- Ingestion still runs through the normal source-type entrypoints:
  - `python -m ingestion.run_ingestion --source-type market-events --input ...`
  - `python -m ingestion.run_ingestion --source-type sec-filings --input ...`

Deterministic rule:

- Approved records must carry stable `source_name + source_record_id`.
- Idempotency stays in the existing pipeline, not in n8n.

## Recommended n8n Steps

1. Trigger from schedule or manual run.
2. Read `reports/targeted_backfill_plan.json`.
3. Filter to the next N unresolved slices.
4. Build deterministic `search_queries`.
5. Fetch source pages or API responses.
6. Parse fields into `source_candidates` and `collected_examples`.
7. Compute a stable `duplicate_check_key`.
8. Write the updated JSON bundle back to shared storage or the repo staging area.
9. Notify reviewer that items are ready for review.

## Starter Workflow

The current n8n workflow created for StrattonAI is:

- `StrattonAI Targeted Backfill Research v2`

Its repo-owned import file is:

- `automation/n8n/strattonai_targeted_backfill_research_workflow.json`

Current behavior:

- manual trigger for deterministic runs
- one branch that emits a per-query search task queue
- one branch that emits a full review-bundle JSON payload matching `ingestion/templates/n8n_targeted_research_template.json`
- public SEC enrichment inside the review-bundle branch for `sec-filings` slices:
  - resolves public SEC ticker mappings
  - fetches recent public submissions metadata
  - captures filing candidates for review without bypassing human approval
- current default slice seeds exclude the Tata/TTM price-gap item and focus on the live SEC and market-event gaps

This starter workflow is intentionally conservative. It creates stable research tasks and review bundles first, so external fetch steps can be added without moving classification or persistence into n8n.

## Dedupe Safeguards

Use all of these:

- Stable `source_name`
- Stable `source_record_id`
- Stable `source_url`
- Stable `duplicate_check_key`
- `source_gap_key` linking the example back to the exact target slice

Recommended `duplicate_check_key` format:

- `source_name|source_record_id|primary_ticker|event_category|published_at`

If the source has no durable record id:

- derive a deterministic surrogate from a canonical URL path plus publication date

## Review Checkpoints

Before marking `ready_for_ingestion=true`, confirm:

1. The example directly addresses the requested slice.
2. The source is reputable and linkable.
3. The source quote supports the event and relationship claim.
4. The example does not duplicate an existing stored event or filing.
5. The example contains enough facts to survive deterministic normalization.

## How n8n Should Populate The Template

- Populate slice headers from `reports/targeted_backfill_plan.json`.
- Populate `search_queries` from stable planner fields and saved source preferences.
- Populate `source_candidates` with every source page or API result worth review.
- Populate `collected_examples` only with concrete candidate examples.
- Keep unresolved fields blank instead of guessing.
- Mark all newly collected examples `ready_for_ingestion=false`.

## How The Completed Template Flows Into StrattonAI

1. n8n produces the research bundle.
2. A reviewer approves or rejects examples in the bundle.
3. Approved examples are converted into source-specific ingestion bundles with:
   - `python -m ingestion.build_n8n_handoff_bundles`
4. StrattonAI runs normal ingestion, normalization, taxonomy, relationship expansion, event studies, and scoring.
5. Coverage audit and targeted backfill planning are rerun, which closes the loop and re-ranks the next weakest slices.

The converter writes:

- `ingestion/generated/n8n_market_events_review_bundle.json`
- `ingestion/generated/n8n_sec_filings_review_bundle.json`
- `reports/n8n_handoff_summary.json`

Those outputs are ready for the normal ingestion entrypoints:

- `python -m ingestion.run_ingestion --source-type market-events --input ingestion/generated/n8n_market_events_review_bundle.json`
- `python -m ingestion.run_ingestion --source-type sec-filings --input ingestion/generated/n8n_sec_filings_review_bundle.json`

## Deterministic Boundary Summary

n8n is allowed to:

- fetch
- search
- extract
- document

n8n is not allowed to:

- make final classification decisions
- infer unsupported relationships
- bypass duplicate safeguards
- write directly into research tables as truth

That keeps the backfill workflow explainable, reproducible, and compatible with the current StrattonAI architecture.
