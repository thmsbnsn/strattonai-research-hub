# Coverage Audit And Gap Filling

The coverage audit measures where the current historical evidence base is strong, where it is thin, and which areas should get the next deterministic backfill wave.

## What The Audit Measures

- event counts by category
- event counts by source
- study counts by category, horizon, and target type
- sample-size distribution by category
- confidence-band distribution by category
- sparse exact primary slices
- sparse exact related slices
- sparse relationship slices
- tickers with missing or insufficient price history
- categories with weak or no high-confidence signals

## Gap Ranking

The audit assigns a deterministic `gap_score` using:

- sample-size shortfall versus required minimums
- missing horizons
- fallback frequency
  - primary signals using `category_summary`
  - related signals using `relationship`
- current signal usage
- category importance
- relationship importance where applicable

No scoring formula changes are made here. This module only diagnoses the evidence base.

## Output

Run:

```bash
python -m research.generate_gap_report
```

This writes:

- `reports/coverage_audit.json`
- `reports/coverage_audit.md`

## How To Use The Report

Use the report to guide the next backfill wave:

- if a category is thin, add more events in that category
- if a primary slice keeps falling back to `category_summary`, add more examples for that exact ticker/category pair
- if a related slice keeps falling back to `relationship`, add more events attaching that related ticker explicitly
- if price history is short, extend the structured local price file before recomputing studies

## Gap-Fill Candidates

The audit also generates deterministic recommendation candidates such as:

- add more `Macro Event` examples for a primary ticker
- add more `Product Launch` examples for a related ticker slice
- add more `Supplier` or `Competitor` relationship-path examples
- extend price history for a heavily referenced ticker

These are recommendations only. The framework does not fabricate data.

## How This Supports Future Expansion

Later, when live sources are added, the same audit can be used to:

- prioritize which live sources should be integrated first
- measure whether new live data is improving exact-slice depth
- decide where source expansion is still needed
- keep the evidence base balanced instead of letting one category dominate
