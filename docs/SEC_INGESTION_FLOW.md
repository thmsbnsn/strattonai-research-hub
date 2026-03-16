# SEC Ingestion Flow

This ingestion mode supports structured local SEC filing records and maps them into the same normalized event boundary already used by the market-event ingestion pipeline.

## Files

- `ingestion/load_sec_filings_file.py`
- `ingestion/map_sec_filing_to_event.py`
- `ingestion/taxonomy_config.json`
- `ingestion/classify_event.py`
- `ingestion/sample_input_sec_filings.json`
- `ingestion/run_ingestion.py`

## Raw SEC Input Shape

The SEC loader accepts either:
- a JSON array of filing objects
- an object with a `filings` array

Expected filing fields:
- `accession_number`
- `form_type`
- `filing_date`
- `company_name`
- `ticker`

Optional fields:
- `headline`
- `summary`
- `extracted_tags`
- `related_tickers`
- `metadata`

Example shape:

```json
{
  "accession_number": "0001326801-26-000031",
  "form_type": "8-K",
  "filing_date": "2026-03-14",
  "company_name": "NVIDIA Corporation",
  "ticker": "NVDA",
  "headline": "NVIDIA discloses multi-year strategic supply agreement for AI systems expansion",
  "summary": "The company disclosed a new multi-year strategic supply and infrastructure agreement.",
  "extracted_tags": ["major agreement", "strategic agreement"],
  "related_tickers": [
    {
      "ticker": "TSM",
      "name": "Taiwan Semi",
      "relationship": "Supplier",
      "strength": 0.88
    }
  ],
  "metadata": {
    "filing_sections": ["Item 1.01", "Item 8.01"]
  }
}
```

## Filing-To-Event Mapping

The SEC mapper converts each filing into the standard event payload before normalization. The shared classifier then assigns category and sentiment.
After normalization, the shared entity-expansion engine can attach graph-derived related companies even when the SEC filing did not provide explicit related tickers.

Source provenance:
- `source_name = "sec_filing"`
- `source_record_id = accession_number`

Standard event fields produced:
- `ticker`
- `headline`
- `category`
- `sentiment`
- `timestamp`
- `source_name`
- `source_record_id`
- `metadata`

Timestamp rule:
- `filing_date` is normalized to midnight UTC for deterministic event timing

Related company rule:
- related-company rows are only created when `related_tickers` is explicitly present in the structured filing input
- the shared graph expansion step may add inferred related companies after normalization, with `origin_type = inferred`

## Category Rules

Mapping is deterministic and tag/keyword driven, but the rules now live in the shared taxonomy layer instead of the SEC mapper.

Examples:
- `earnings`, `guidance`, `results of operations` -> `Earnings`
- `major agreement`, `partnership`, `strategic agreement` -> `Partnership`
- `legal`, `litigation`, `investigation`, `regulatory` -> `Legal/Regulatory`
- `acquisition`, `merger`, `capital expenditure`, `capex`, `restructuring` -> `Capital Expenditure`
- otherwise `8-K` defaults to `Macro Event`

## Sentiment Rules

Sentiment is also deterministic and rule-based:
- positive hints like `guidance raised`, `major agreement`, `partnership`, `acquisition` -> `positive`
- negative hints like `investigation`, `litigation`, `guidance cut`, `restructuring` -> `negative`
- otherwise:
  - taxonomy defaults apply for the resolved category

Resolution order:
- explicit source payload hints if any are present
- keyword scoring across headline, summary, extracted tags, form type, and selected metadata
- SEC form-type defaults
- `Macro Event` fallback

## Deduplication

Primary dedupe uses source identity:
- `source_name = sec_filing`
- `source_record_id = accession_number`

This flows into:
- deterministic event UUID generation
- the persisted `events.source_name + events.source_record_id` database identity

Compatibility fallback still checks natural keys if a legacy row already exists with a different ID.

## Running SEC Mode

Dry run:

```powershell
python -m ingestion.run_ingestion --source-type sec-filings --dry-run --input ingestion\sample_input_sec_filings.json
```

Real write:

```powershell
python -m ingestion.run_ingestion --source-type sec-filings --input ingestion\sample_input_sec_filings.json
```

With schema bootstrap:

```powershell
python -m ingestion.run_ingestion --source-type sec-filings --bootstrap-schema --input ingestion\sample_input_sec_filings.json
```

## Tables Updated

SEC mode updates the same normalized event boundary:
- `events`
- `related_companies` when explicitly supported by source data

It does not automatically create `research_insights` from SEC filings in this phase.

## Future Evolution

When live SEC connectors are added later, they should emit this same structured filing shape and then call the same SEC mapper plus shared classifier and normalized write path. That keeps the filing-specific parsing deterministic and isolated from the UI and database service layer.
