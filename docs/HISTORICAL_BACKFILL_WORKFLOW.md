# Historical Backfill Workflow

This workflow expands the deterministic evidence base with structured local events, structured local SEC-style filings, and extended local price history.

## Files

- `ingestion/sample_historical_events.json`
- `ingestion/sample_historical_sec_filings.json`
- `research/sample_extended_price_series.json`
- `ingestion/backfill_historical_events.py`
- `research/recompute_all_event_studies.py`
- `research/rescore_all_recent_events.py`

## Input Formats

Historical market events:

- same shape as the existing local market-event ingestion format
- one record per event with stable `source_name + source_record_id`
- optional explicit related companies

Historical SEC filings:

- same shape as the existing SEC ingestion format
- one filing per object with stable `accession_number`

Extended price history:

- supports either explicit `dates + closes`
- or `date_range + start_close + segments`
- segment mode expands business dates deterministically using repeated `daily_move` blocks

## Recommended Run Order

1. `python -m ingestion.backfill_historical_events`
2. `python -m research.recompute_all_event_studies`
3. `python -m research.rescore_all_recent_events`

Dry-run the same sequence first if needed by adding `--dry-run`.

## Deduplication

Event backfill:

- market events use deterministic IDs from `source_name + source_record_id`
- SEC filings use deterministic IDs from `source_name + accession_number`
- writes upsert into `events`

Study recomputation:

- studies upsert on `event_study_statistics.study_key`
- UI summary rows upsert on `event_study_results (event_type, horizon)`

Signal rescoring:

- signals upsert on `signal_scores.signal_key`

Rerunning the entire workflow should update rows in place instead of duplicating them.

## Verification

To verify study depth improved:

- compare `event_study_statistics` row counts before and after recomputation
- inspect category-summary coverage in the recompute logs
- inspect sample sizes on `event_study_statistics`

To verify confidence bands changed:

- inspect the `rescore_all_recent_events.py` before/after band distribution logs
- query `signal_scores` by `confidence_band`
- check Dashboard Top Signals after refresh

## Diagnostics

The batch scripts log:

- normalized event counts
- category coverage
- study-count growth
- signal confidence-band distribution

## Limitations

- still no live external event or price APIs
- still no LLM-based ranking
- still no broker execution or automated trading

## Future Extension Points

- larger quarterly backfill files
- regime-specific price history sets
- sector-specific backfill packs
- automated validation reports for category depth and signal confidence drift
