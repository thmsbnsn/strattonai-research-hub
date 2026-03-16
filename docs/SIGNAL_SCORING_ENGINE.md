# Signal Scoring Engine

The signal engine ranks recent stored events using persisted event-study evidence. It is deterministic, source-agnostic, and explainable. It does not trade, call brokers, or rely on live market APIs.

## Inputs

- `events`
- `related_companies`
- `event_study_statistics`
- `events.metadata.classification`

The scorer evaluates both:

- primary-ticker opportunities
- related-company opportunities attached to the event

## Score Inputs

Each signal uses:

- `event_category`
- `primary_ticker`
- `target_ticker`
- `target_type`
- `relationship_type`
- `horizon`
- `avg_return`
- `median_return`
- `win_rate`
- `sample_size`
- classification confidence from `events.metadata.classification.confidence`
- relationship origin (`primary`, `explicit`, `inferred`)
- event recency

## Study Lookup Rules

Primary signals:

1. Exact `primary` study for `event_category + primary_ticker + horizon`
2. Fallback `category_summary` study for `event_category + horizon`

Related signals:

1. Exact `related` study for `event_category + related_ticker + relationship_type + horizon`
2. Fallback `relationship` study for `event_category + relationship_type + horizon`

If no study exists, the signal is skipped cleanly.

## Scoring Formula

The score uses transparent components:

- `avg_component = min(abs(avg_return) * 12, 30)`
- `median_component = min(abs(median_return) * 10, 20)`
- `consistency_component = max(consistency_rate - 50, 0) * 0.6`
- `sample_component = min(sample_size, 20) * 1.5`

`consistency_rate` is direction-aware:

- bullish studies use `win_rate`
- bearish studies use `100 - win_rate`

Multipliers:

- classifier confidence: `High=1.00`, `Moderate=0.93`, `Low=0.85`
- origin type: `primary=1.00`, `explicit=0.97`, `inferred=0.88`
- recency:
  - `<=2 days = 1.00`
  - `<=5 days = 0.96`
  - `<=10 days = 0.92`
  - `>10 days = 0.88`

Final score:

`min((avg + median + consistency + sample) * classifier * origin * recency, 100)`

## Confidence Bands

- `High`: strong score, adequate sample, strong return magnitude, and consistent historical direction
- `Moderate`: acceptable sample with usable evidence
- `Low`: anything weaker or thinly supported

The exact thresholds live in `research/signal_scoring.py`.

## Persistence

Signals are written to `signal_scores` with a stable `signal_key`.

Each row stores:

- event linkage
- target ticker and target type
- selected study reference
- score and confidence band
- evidence summary
- full scoring rationale JSON

Reruns are safe because writes upsert on `signal_key`.

## Running The Scorer

Apply the signal schema and score recent events:

```bash
python -m research.score_current_events --bootstrap-schema
```

Dry run:

```bash
python -m research.score_current_events --dry-run
```

Useful options:

- `--lookback-days 30`
- `--limit-events 50`
- `--verbose`

## Limitations

- No live price or market-regime filter yet
- No transaction-cost or liquidity model
- No automated trading or broker execution
- No LLM ranking or qualitative reasoning

## Future Extension Points

- market-regime conditioned studies
- confidence adjustments for overlapping evidence
- portfolio-aware ranking
- signal review UI and approval workflow
