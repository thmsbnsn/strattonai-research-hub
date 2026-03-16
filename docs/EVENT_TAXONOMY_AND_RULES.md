# Event Taxonomy And Rules

StrattonAI now classifies all ingested events through a shared deterministic taxonomy layer. Source-specific loaders can still parse their own raw payloads, but category and sentiment assignment now happen in one place.

## Canonical Categories

- `Product Launch`
- `Earnings`
- `Partnership`
- `Legal/Regulatory`
- `Capital Expenditure`
- `Supply Disruption`
- `Regulatory Approval`
- `Macro Event`

The machine-readable source of truth is `ingestion/taxonomy_config.json`.

Each category definition can include:
- aliases
- keyword triggers
- default sentiment
- confidence note
- source-specific defaults such as SEC form-type hints

## Rule Inputs

The classifier consumes a source-agnostic input envelope:

- `headline`
- `summary`
- `extracted_tags`
- `form_type`
- `source_name`
- `event_type_hint`
- `sentiment_hint`
- `metadata`

Future sources should map their raw payloads into this envelope and then call the shared classifier instead of adding inline classification logic.

## Resolution Order

Category precedence is deterministic:

1. explicit `event_type_hint` alias match
2. keyword scoring across headline, summary, tags, form type, and selected metadata terms
3. source-specific hints such as `sec_filing` form-type defaults
4. fallback to `Macro Event`

Sentiment precedence is also deterministic:

1. explicit `sentiment_hint` alias match
2. sentiment keyword scoring across the same normalized search terms
3. category default sentiment from the taxonomy config

If multiple categories tie on keyword score, config order wins. That makes the result stable across reruns.

## Source-Specific Hints

Current source hints are intentionally narrow:

- `sec_filing`
  - `8-K` -> `Macro Event`
  - `10-Q` -> `Earnings`
  - `10-K` -> `Earnings`

These defaults only apply when alias and keyword rules do not already produce a stronger match.

## Sentiment Tendencies

The taxonomy currently encodes these defaults:

- `Product Launch` -> `positive`
- `Earnings` -> `neutral`
- `Partnership` -> `positive`
- `Legal/Regulatory` -> `negative`
- `Capital Expenditure` -> `positive`
- `Supply Disruption` -> `negative`
- `Regulatory Approval` -> `positive`
- `Macro Event` -> `neutral`

Keyword overrides still take precedence over these defaults when clear positive or negative terms are present.

## Rationale Capture

Every normalized event stores classification rationale in `events.metadata.classification`.

Stored fields:

- `category`
- `sentiment`
- `matched_rules`
- `explanation`
- `confidence`
- `confidence_note`

This gives downstream review and debugging a stable record of why a category and sentiment were assigned.

## Extending The Taxonomy

For new sources such as earnings summaries, transcripts, or live news feeds:

1. parse the raw source payload into a deterministic intermediate shape
2. pass source hints, tags, and summary text into the shared classifier
3. keep new rules in `taxonomy_config.json` where possible
4. only add Python rule code when config-based matching is not enough

The goal is to keep classification source-agnostic, auditable, and easy to expand without scattering logic across multiple ingestion adapters.
