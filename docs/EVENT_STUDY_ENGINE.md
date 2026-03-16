# Event Study Engine

StrattonAI now includes a deterministic historical event-study engine that reads stored events from Supabase, matches them against local structured price series, computes forward returns, and persists aggregate study results back into Supabase.

## Files

- `ingestion/load_price_series_file.py`
- `ingestion/sample_price_series.json`
- `research/event_study_models.py`
- `research/compute_forward_returns.py`
- `research/event_study_engine.py`
- `research/write_event_studies_to_supabase.py`
- `supabase/sql/006_add_event_study_statistics.sql`

## Price Series Input Format

The local sample price input is a JSON object with:

- `dates`: a shared ordered trading-date array
- `series`: an array of per-ticker close arrays

Example shape:

```json
{
  "dates": ["2026-03-12", "2026-03-13", "2026-03-16"],
  "series": [
    {
      "ticker": "NVDA",
      "closes": [134.38, 133.57, 136.51]
    }
  ]
}
```

Each ticker must provide exactly one close for each shared trading date.

## Date Alignment Rules

The engine computes close-to-close forward returns.

Alignment is deterministic:

1. read the stored event timestamp from Supabase
2. convert the timestamp to its calendar date
3. align to the first available trading date on or after that event date
4. use the aligned close as the entry price
5. use the close `N` trading sessions later as the exit price

This means weekend or holiday events roll forward to the next available trading session in the local price file.

## Forward Return Math

For each supported horizon:

- `1D`
- `3D`
- `5D`
- `10D`
- `20D`

the engine computes:

`((future_close / entry_close) - 1) * 100`

Returns are persisted as percentage values, not decimal fractions.

If the local price file does not have enough forward trading sessions for a horizon, that observation is skipped cleanly.

## Study Shapes

The engine computes observations for:

- the event primary ticker
- each event-related ticker attached to that event

It then aggregates those observations into deterministic study rows with these target types:

- `category_summary`
  - primary-ticker returns aggregated only by event category and horizon
- `primary`
  - primary-ticker returns aggregated by event category, primary ticker, and horizon
- `relationship`
  - related-ticker returns aggregated by event category, relationship type, and horizon
- `related`
  - related-ticker returns aggregated by event category, related ticker, relationship type, and horizon

## Persistence Strategy

Detailed results are written to `event_study_statistics`.

Stored fields include:

- `study_key`
- `study_target_type`
- `event_category`
- `primary_ticker`
- `related_ticker`
- `relationship_type`
- `horizon`
- `sample_size`
- `avg_return`
- `median_return`
- `win_rate`
- `notes`
- `metadata`

The existing `event_study_results` table is also updated with `category_summary` rows so the current Event Studies page can consume real Supabase-backed summary results without a redesign.

## Rerun Behavior

The engine is rerunnable.

- detailed rows are keyed by deterministic `study_key`
- UI summary rows are upserted by `event_type + horizon`

Recomputing the same study updates rows instead of creating duplicates.

## Running The Engine

Dry run:

```powershell
python -m research.event_study_engine --dry-run --price-file ingestion\sample_price_series.json
```

Apply the study-table migration and write results:

```powershell
python -m research.event_study_engine --bootstrap-schema --price-file ingestion\sample_price_series.json
```

Run against an already prepared database:

```powershell
python -m research.event_study_engine --price-file ingestion\sample_price_series.json
```

## Current Limitations

- price data still comes from a local structured file, not a live market-data source
- the current charts on the Event Studies page still use mock fallback data
- the page now consumes real computed summary rows for the selected event category, but it does not yet expose the richer `primary`, `relationship`, and `related` study slices in the UI

## Future Extension

The next logical extensions are:

- live or batch historical price ingestion into Supabase
- persistence of raw observation rows if deeper auditing becomes necessary
- UI filters that query `event_study_statistics` by primary ticker, related ticker, and relationship type
