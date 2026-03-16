# StrattonAI Roadmap

This roadmap reflects the current state of the repository after the research-capable backend, AI Trader shell, local AI gateway, and local-model retrieval stack were added.

## Current Stage

StrattonAI is beyond mock-dashboard status. It now has:

- live event, study, and signal reads in the frontend
- deterministic ingestion and scoring pipelines
- local-first historical price workflows
- coverage auditing and targeted backfill planning
- a grounded local AI chat layer attached to the AI Trader dashboard

The next work should focus on deepening evidence quality and tightening end-to-end operator workflows, not reinventing the core architecture.

## Priority 1: Finish The AI Trader Data Wiring

Goal: turn the AI Trader shell into a truly grounded operator workspace.

Main tasks:

- unify company briefing data into one backend-facing payload
- wire trader cards to deterministic signal and event-study outputs
- add citation drill-through from chat responses into studies, events, and signals
- improve company search and selection flows for real operator use

Success condition:

- the AI Trader dashboard stops feeling like a shell and becomes a usable research cockpit

## Priority 2: Improve Coverage Quality

Goal: strengthen weak exact slices and thin categories rather than only increasing raw event volume.

Main tasks:

- deepen `Partnership` history
- improve narrow related-company slices still showing weak evidence
- keep using targeted expansion waves instead of generic bulk ingestion
- continue to reduce low-confidence concentration in `Product Launch` and `Legal/Regulatory`

Success condition:

- a larger share of active signals moves from `Low` to `Moderate` or `High` for the right reasons

## Priority 3: Close Price Coverage Gaps

Goal: eliminate remaining study-blocking ticker gaps.

Main tasks:

- solve `TTM` historical price coverage
- continue using deterministic external gap-fill workflows only when local sources miss needed tickers
- keep `daily_prices` aligned with the preferred local resolved dataset

Success condition:

- unlocked Tata-linked events begin contributing to event studies and downstream signals

## Priority 4: Expand Structured Source Coverage

Goal: improve research depth using source families that fit the current deterministic architecture.

Main tasks:

- use `FMP` for company profiles, fundamentals, and structured market metadata
- deepen filing coverage with the `SEC API`
- evaluate whether a macro/regulatory ingestion path from legislative transcript data is worth building

Success condition:

- company briefing and AI-grounding payloads become richer without weakening determinism

## Priority 5: Trader Workflow Safety

Goal: keep the project useful for sandbox trading without creating unsafe automation.

Main tasks:

- keep paper trading as the first-class execution path
- add Alpaca account-state and order-preview workflows before any live execution
- require explicit live-mode guardrails and operator confirmation
- keep AI advisory and retrieval separate from execution authority

Success condition:

- the system can assist a trader without becoming an opaque auto-trading bot

## Priority 6: Performance And Operator Ergonomics

Goal: make the system faster and easier to run repeatedly.

Main tasks:

- cache semantic retrieval for repeated company queries
- continue using Parquet-first local data paths
- improve background operator scripts and health checks
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
