# Relationship Graph And Entity Expansion

StrattonAI now separates reusable company-to-company relationships from event-specific related-company rows.

## Graph Structure

Canonical graph rows live in `company_relationship_graph`.

Each row supports:

- `source_ticker`
- `source_name`
- `target_ticker`
- `target_name`
- `relationship_type`
- `strength`
- `is_directional`
- `notes`
- `provenance`

Event-specific rows still live in `related_companies`, but now also store:

- `relationship_type`
- `origin_type`
- `notes`
- `rationale`
- `graph_relationship_id`

`origin_type` distinguishes:

- `explicit`: provided directly by the source payload
- `inferred`: added by deterministic graph expansion

## Relationship Types

The centralized relationship layer currently supports:

- `Supplier`
- `Customer`
- `Competitor`
- `Sector Peer`
- `Partner`
- `Regulatory Peer`
- `Supply Chain Dependency`
- `Related`

## Event-Category-Sensitive Expansion

Expansion runs after an event has already been normalized and classified.

The engine:

1. loads the canonical graph from `ingestion/relationship_seed.json`
2. finds graph edges connected to the event ticker
3. applies category-specific relationship priorities
4. filters low-strength edges
5. merges inferred rows with explicit source-provided rows
6. keeps the final set deterministic through stable sorting and capped inferred counts

Current examples:

- `Product Launch`: prioritize `Supplier`, `Competitor`, `Customer`, `Sector Peer`
- `Supply Disruption`: prioritize `Supplier`, `Supply Chain Dependency`, `Customer`, `Competitor`
- `Regulatory Approval`: prioritize `Competitor`, `Regulatory Peer`
- `Legal/Regulatory`: prioritize `Regulatory Peer`, `Sector Peer`
- `Earnings`: prioritize `Competitor`, `Supplier`, `Customer`

## Merge Behavior

Explicit relationships are preserved.

When inferred rows are added:

- explicit rows always win over inferred rows for the same target ticker
- inferred rows fill remaining slots based on category priority and relationship strength
- reruns do not duplicate rows because event-specific IDs remain stable and the writer also resolves existing rows by natural keys

## Rationale Storage

Every inferred event-related company row stores structured rationale in `related_companies.rationale`.

Typical fields include:

- `origin`
- `event_category`
- `relationship_type`
- `priority_rank`
- `graph_strength`
- `graph_relationship_id`
- `used_reverse_edge`
- `graph_notes`
- `graph_provenance`
- `rule_name`

Explicit rows also store lightweight rationale so downstream review can distinguish source-provided relationships from inferred ones.

## Files

- `ingestion/relationship_seed.json`
- `ingestion/relationship_graph.py`
- `ingestion/relationship_rules.py`
- `ingestion/expand_related_entities.py`
- `supabase/sql/004_add_relationship_graph_and_related_company_metadata.sql`
- `supabase/sql/005_seed_company_relationship_graph.sql`

## Future Extension

Future sources should not invent their own ad hoc entity-expansion logic.

Instead:

1. normalize the event
2. classify the event
3. run the shared entity expansion step
4. add new graph rows or new category-sensitive rules when coverage needs to grow

This keeps relationship inference deterministic, inspectable, and reusable for later cross-company event studies.
