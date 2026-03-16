# Event Ingestion Flow

This is the first deterministic ingestion path for StrattonAI. It is intentionally local-file based so the pipeline can be validated before any live news feeds or API connectors are added.

## Files

- `ingestion/sample_input_events.json`
- `ingestion/sample_input_sec_filings.json`
- `ingestion/load_source_file.py`
- `ingestion/load_sec_filings_file.py`
- `ingestion/models.py`
- `ingestion/taxonomy_config.json`
- `ingestion/taxonomy.py`
- `ingestion/rules.py`
- `ingestion/classify_event.py`
- `ingestion/relationship_seed.json`
- `ingestion/relationship_graph.py`
- `ingestion/relationship_rules.py`
- `ingestion/expand_related_entities.py`
- `ingestion/map_sec_filing_to_event.py`
- `ingestion/normalize.py`
- `ingestion/write_to_supabase.py`
- `ingestion/run_ingestion.py`

## Raw Input Format

The market-event ingestion runner expects either:
- a JSON array of event objects
- an object with an `events` array

Required fields per event:
- `source_name`
- `source_record_id`
- `headline`
- `primary_ticker`
- `event_type`
- `sentiment`
- `occurred_at`

Optional fields:
- `historical_analog`
- `sample_size`
- `avg_return`
- `details`
- `related_companies`
- `research_insight`
- `metadata`

Example shape:

```json
{
  "source_name": "manual_seed",
  "source_record_id": "nvda-blackwell-ultra-20260313",
  "headline": "NVIDIA announces next-gen AI training chips with 2x performance",
  "primary_ticker": "nvda",
  "event_type": "product_launch",
  "sentiment": "bullish",
  "occurred_at": "2026-03-13T08:32:00Z",
  "related_companies": [
    {
      "ticker": "tsm",
      "name": "Taiwan Semi",
      "relationship": "supplier",
      "strength": 0.9
    }
  ]
}
```

## Normalization Flow

1. Load the local JSON records.
2. Validate required fields.
3. Normalize all tickers to uppercase.
4. Route category and sentiment assignment through the shared taxonomy and rule engine.
5. Normalize sentiment values to `positive`, `negative`, or `neutral`.
6. Normalize timestamps into UTC.
7. Fill safe defaults for optional fields like `sample_size`, `avg_return`, and `details`.
8. Generate stable UUIDs for events, related companies, and mapped research insights.
9. Persist source provenance in the `events` table via `source_name`, `source_record_id`, and `metadata`.
10. Persist classification rationale in `metadata.classification`.
11. Merge explicit related companies with deterministic graph-inferred related companies.

Category precedence:
- explicit event type hint alias
- keyword scoring
- source-specific hint
- `Macro Event` fallback

Sentiment precedence:
- explicit sentiment hint alias
- keyword scoring
- taxonomy default sentiment

## Deduplication

The pipeline is rerunnable without duplicating rows.

Primary strategy:
- events use a deterministic UUID from `source_name + source_record_id`
- related companies use a deterministic UUID from `event_id + source_ticker + target_ticker + relationship`
- research insights use a deterministic UUID from normalized title
- `events.source_name + events.source_record_id` is also stored in the database as an explicit source identity
- graph-inferred related companies use the same deterministic event-edge identity as explicit rows, so reruns update rather than duplicate

Compatibility strategy for seeded or legacy rows:
- `events` are matched by `ticker + headline + timestamp`
- `related_companies` are matched by `event_id + source_ticker + target_ticker + relationship`
- `research_insights` are matched by case-insensitive `title`

If a row already exists under a different ID, the ingestion writer reuses that existing ID and updates the row instead of inserting a duplicate.

## Database Write Flow

The writer connects directly to Supabase Postgres using:
- `SUPABASE_PROJECT_URL`
- `SUPABASE_DATABASE_PASSWORD`

It derives the standard direct host form:
- `db.<project-ref>.supabase.co`

Tables updated:
- `events`
- `related_companies`
- `research_insights` when the input record includes a `research_insight`

If the relationship-graph migrations have been applied, event-related company rows also store:
- `origin_type`
- `relationship_type`
- `notes`
- `rationale`
- optional `graph_relationship_id`

## Running The Script

Install the single dependency:

```powershell
python -m pip install -r ingestion\requirements.txt
```

Validate only:

```powershell
python -m ingestion.run_ingestion --source-type market-events --dry-run --input ingestion\sample_input_events.json
```

Bootstrap the core tables first if needed, then ingest:

```powershell
python -m ingestion.run_ingestion --source-type market-events --bootstrap-schema --input ingestion\sample_input_events.json
```

If you already created the first-pass schema earlier, apply the incremental provenance migration before rerunning ingestion:

```sql
-- supabase/sql/003_add_event_ingestion_source_fields.sql
```

Run against an already prepared database:

```powershell
python -m ingestion.run_ingestion --source-type market-events --input ingestion\sample_input_events.json
```

SEC filing mode uses the same write path with a different structured input shape:

```powershell
python -m ingestion.run_ingestion --source-type sec-filings --input ingestion\sample_input_sec_filings.json
```

## What The Sample Updates

The sample file contains five realistic event records:
- NVDA product launch
- LLY regulatory approval
- TSLA supply disruption
- MSFT capital expenditure
- AAPL legal/regulatory event

It also maps three research insights so Dashboard and Event Feed can move off pure fallback data.

## UI Verification

After ingestion:
- Dashboard and Event Feed should show live event rows
- Companies should still use seeded relationship graph rows plus live company/event data
- the existing data-source badge will indicate fully live, partial live, mock fallback, or fetch error

## Future Feed Integration

Later news or API adapters should convert their raw payloads into this same structured input shape and then call the same shared classifier, normalization, and write path. That keeps source-specific parsing outside the UI and preserves deterministic ingestion behavior.
