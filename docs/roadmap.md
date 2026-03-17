# StrattonAI Roadmap

This roadmap reflects the current state of the repository after the research-capable backend, AI Trader workspace wiring, local AI gateway, semantic retrieval stack, and the first deterministic trader-side modules were added.

## Current Stage

StrattonAI is beyond mock-dashboard status. It now has:

- live event, study, and signal reads in the frontend
- deterministic ingestion and scoring pipelines
- local-first historical price workflows
- coverage auditing and targeted backfill planning
- a grounded local AI chat layer attached to the AI Trader dashboard
- trader-side deterministic modules for:
  - signal review and simulation
  - portfolio monitoring
  - portfolio construction
  - risk assessment
  - hard risk gating
  - order preview
  - transaction cost estimation
  - paper-first penny-stock loop scaffolding
- operator tooling for:
  - migration verification
  - full-system health checks
  - study-universe gap-fill automation
  - partnership backfill prioritization
  - loop history and rejection-reason reporting

The next work should focus on deepening evidence quality, tightening operator workflows, and safely wiring the trader workspace to richer live context, not reinventing the core architecture.

## Newly Completed In This Stage

These items are now current capabilities and should not be treated as future roadmap work:

- migration verifier for Supabase schema stages `009` through `013`
- gateway migration-health and full-health endpoints
- targeted gap-fill pipeline with optional recompute and rescoring
- background trading-loop execution with status and history endpoints
- unified hard risk gate across simulation, portfolio construction, and loop entry
- deterministic order preview with buying-power and fee checks
- evidence-slice drill-through and live relationship-study views across Event Studies, Companies, and AI Trader
- semantic retrieval cache support
- partnership backfill helper reports
- n8n-assisted targeted-backfill workflow contract plus reviewed-example handoff into source-specific ingestion bundles

## Priority 1: Unify The AI Trader Briefing Payload

Goal: make the AI Trader dashboard consume one coherent backend-facing evidence payload instead of several parallel queries.

Main tasks:

- extend the shared briefing payload with deeper profile/fundamental coverage and richer evidence slices
- keep reusing that payload in company briefing, trader cards, and chat grounding
- keep route-based citation drill-through current as new evidence surfaces are added

Success condition:

- the AI Trader dashboard behaves like one operator workspace instead of a set of loosely connected panels

## Priority 2: Improve Coverage Quality

Goal: strengthen weak exact slices and thin categories rather than only increasing raw event volume.

Main tasks:

- deepen `Partnership` history
- improve narrow related-company slices still showing weak evidence
- keep using targeted expansion waves instead of generic bulk ingestion
- continue to reduce low-confidence concentration in `Product Launch` and `Legal/Regulatory`

Success condition:

- a larger share of active signals moves from `Low` to `Moderate` or `High` for the right reasons

## Priority 3: Expand Profile And Fundamental Coverage

Goal: make company briefings and trader workflows less fallback-heavy.

Main tasks:

- populate `company_profiles` more completely
- add cleaner market cap, sector, industry, and business-description coverage
- prefer structured vendor/API sources that keep determinism and provenance intact

Success condition:

- AI Trader briefings and Companies page views stop relying on placeholder profile fields for covered names

## Priority 4: Expand Structured Source Coverage

Goal: improve research depth using source families that fit the current deterministic architecture.

Main tasks:

- use `FMP` for company profiles, fundamentals, and structured market metadata
- deepen filing coverage with the `SEC API`
- evaluate whether a macro/regulatory ingestion path from legislative transcript data is worth building

Success condition:

- company briefing and AI-grounding payloads become richer without weakening determinism

## Priority 5: Trader Workflow Safety And Execution Guardrails

Goal: keep the project useful for sandbox trading without creating unsafe automation.

Main tasks:

- keep paper trading as the first-class execution path
- add Alpaca account-state, positions, and order-preview workflows before any broader execution features
- keep explicit live-mode guardrails and operator confirmation in both settings and backend checks
- keep AI advisory and retrieval separate from execution authority

Success condition:

- the system can assist a trader without becoming an opaque auto-trading bot

## Priority 6: Performance And Operator Ergonomics

Goal: make the system faster and easier to run repeatedly.

Main tasks:

- keep and tune the semantic retrieval cache for repeated company queries
- cache or memoize repeated portfolio/risk calculations where appropriate
- continue using Parquet-first local data paths
- continue improving background operator scripts, health checks, and audit diff reporting
- keep reports easy to compare across passes

Success condition:

- repeated research sessions feel fast and predictable on the local machine

## Deprioritized For Now

These are intentionally not current priorities:

- replacing deterministic scoring with opaque ML ranking
- turning the app into a live-API-first product
- redesigning the UI
- broad schema churn
- auto-execution of broker trades

## Working Rule For Future Passes

The next best pass should usually satisfy all three:

1. improves evidence quality or operator usefulness
2. fits the current deterministic architecture
3. remains rerunnable without manual cleanup
