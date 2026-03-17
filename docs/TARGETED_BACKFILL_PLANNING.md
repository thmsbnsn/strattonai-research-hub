# Targeted Backfill Planning

The targeted backfill planner turns `coverage_audit.json` into a ranked collection plan and starter templates for the next historical expansion wave.

## Inputs

- `reports/coverage_audit.json`

The planner reads:

- top audit gap candidates
- weak signal categories
- current slice sample sizes
- fallback-heavy related paths

## Ranking Logic

Plan ranking is deterministic and favors:

- high audit gap scores
- weak categories with poor confidence distribution
- important graph-central tickers
- repeated fallback usage
- slices where a modest number of real examples can materially improve exact coverage

The planner does not change scoring logic and does not fabricate data.

## Outputs

Run:

```bash
python -m research.build_targeted_backfill_plan
python -m research.export_backfill_templates
```

This produces:

- `reports/targeted_backfill_plan.json`
- `reports/targeted_backfill_plan.md`
- `ingestion/templates/targeted_market_events_template.json`
- `ingestion/templates/targeted_sec_filings_template.json`
- `docs/N8N_TARGETED_BACKFILL_WORKFLOW.md`
- `ingestion/templates/n8n_targeted_research_template.json`

## Plan Fields

Each plan item includes:

- priority rank
- event category
- primary ticker when applicable
- related ticker when applicable
- relationship type when applicable
- target type
- current sample size
- desired minimum sample size
- gap size
- why it matters
- suggested source type
- example-guidance prompts for real historical collection

## Template Generation

The templates:

- mirror the current highest-priority plan items
- contain placeholder records only
- preserve required ingestion fields
- include notes telling the collector what real historical example to find

They are not meant to be ingested unchanged.

## How To Use It

1. Refresh the coverage audit:
   - `python -m research.generate_gap_report`
2. Build the targeted plan:
   - `python -m research.build_targeted_backfill_plan`
3. Export starter templates:
   - `python -m research.export_backfill_templates`
4. If n8n is being used for assisted collection, populate `ingestion/templates/n8n_targeted_research_template.json` first and review candidates there.
5. Convert approved n8n examples into source-specific bundles:
   - `python -m ingestion.build_n8n_handoff_bundles`
6. Run the normal backfill workflow again against:
   - `ingestion/generated/n8n_market_events_review_bundle.json`
   - `ingestion/generated/n8n_sec_filings_review_bundle.json`

## Future Use

As live sources arrive later, this planner can stay in place and simply consume richer audit outputs. That keeps backfill work disciplined and aligned to the weakest evidence slices instead of whichever source is easiest to query.
