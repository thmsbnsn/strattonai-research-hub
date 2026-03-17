# Supabase Setup And Seed

This project now includes a raw SQL setup path so the existing frontend can read seeded Supabase data immediately.

## What Gets Created

The SQL creates these first-pass tables:
- `events`
- `related_companies`
- `research_insights`
- `journal_entries`
- `paper_trades`
- `company_profiles`
- `event_study_results`
- `signal_scores`
- `daily_prices`
- `portfolio_allocations`
- `market_regimes`

It also creates:
- `public.set_updated_at()` trigger function
- `updated_at` triggers for mutable tables
- indexes that match the current UI lookup patterns
- additive metadata columns needed by the AI Trader workflow

## SQL Files

Run these files in order:
1. `supabase/sql/001_create_core_tables.sql`
2. `supabase/sql/002_seed_core_data.sql`
3. `supabase/sql/004_add_relationship_graph_and_related_company_metadata.sql`
4. `supabase/sql/005_seed_company_relationship_graph.sql`
5. `supabase/sql/006_add_event_study_statistics.sql`
6. `supabase/sql/007_add_signal_scores.sql`
7. `supabase/sql/008_add_daily_prices.sql`
8. `supabase/sql/009_add_portfolio_allocations.sql`
9. `supabase/sql/010_add_paper_trade_metadata.sql`
10. `supabase/sql/011_add_market_regimes.sql`
11. `supabase/sql/012_add_trading_loop_fields.sql`
12. `supabase/sql/013_add_signal_score_metadata.sql`

## How To Run In Supabase

Using the Supabase dashboard:
1. Open your project.
2. Go to `SQL Editor`.
3. Paste and run `001_create_core_tables.sql`.
4. Paste and run `002_seed_core_data.sql`.
5. Paste and run `004_add_relationship_graph_and_related_company_metadata.sql`.
6. Paste and run `005_seed_company_relationship_graph.sql`.
7. Paste and run `006_add_event_study_statistics.sql`.
8. Paste and run `007_add_signal_scores.sql`.
9. Paste and run `008_add_daily_prices.sql`.
10. Paste and run `009_add_portfolio_allocations.sql`.
11. Paste and run `010_add_paper_trade_metadata.sql`.
12. Paste and run `011_add_market_regimes.sql`.
13. Paste and run `012_add_trading_loop_fields.sql`.
14. Paste and run `013_add_signal_score_metadata.sql`.

Using the Supabase CLI:
1. Save the files as-is in the repo.
2. Run them against your linked project with your normal Supabase SQL workflow.

Using the local verifier:
1. Ensure `.env` contains `SUPABASE_PROJECT_URL` and `SUPABASE_DATABASE_PASSWORD`.
2. Run a dry-run validation first:

```powershell
python -m supabase.scripts.apply_and_verify_migrations --dry-run
```

3. Apply and verify against the live database:

```powershell
python -m supabase.scripts.apply_and_verify_migrations
```

The verifier applies migrations `009` through `013` in order, wraps them in transactions, and confirms the expected tables and columns exist afterward.

## What The Seed Covers

The starter seed is intentionally small but enough to light up the current UI:
- Dashboard: events and research insights
- Dashboard: top signals when `signal_scores` is populated
- Event Feed: event list plus related companies
- Companies: company profiles and relationship graph data
- Event Studies: seeded event study rows
- Research Journal: journal entries
- Paper Trades: seeded paper trades
- AI Trader: live signal review, relationship studies, and regime display once the later migrations and loaders are applied

The seed data is based on the current mock semantics, normalized into the new SQL structure.

## How To Verify The UI Is Reading Live Data

In the running app:
1. Open Dashboard or Settings.
2. Check the developer-facing data badge.
3. Expected badge states:
   - `Supabase connected`: all first-pass tables are live
   - `Partial live / partial fallback`: some seeded tables are live, some are still falling back
   - `Mock fallback`: the core tables are missing or empty
   - `Fetch error`: Supabase is reachable but a query is failing

Quick verification path:
1. Seed the SQL.
2. Refresh the app.
3. Confirm the dashboard shows the seeded headlines like the NVIDIA and Eli Lilly events.
4. Open Companies and confirm the default `NVDA` profile resolves from Supabase.
5. Open Paper Trades and confirm the seeded `TSM`, `LLY`, `TSLA`, and `AMD` rows render.
6. Start the local AI gateway and confirm `GET /health/migrations` or the Settings page migration badge shows all trader migrations verified.

## Current Mock-Only Areas

These areas still intentionally use mock fallback data in the frontend:
- market indexes
- sector performance
- VIX
- `daily_prices` table: wired in frontend (`companyService.getPriceHistory`). Load via `python -m research.load_prices_to_supabase --bootstrap-schema`. Falls back to mock if table is empty or missing.
- company event markers
- event return distribution
- event forward curve
- portfolio performance series

The AI Trader dashboard is no longer pure shell, but some panels are gateway-backed rather than Supabase-direct:
- portfolio monitor
- portfolio constructor
- risk engine
- transaction cost estimates
- penny-stock sandbox
- Alpaca account/positions
- trading loop history and preview flows
- price-gap fill controls and migration health status

That fallback path remains in place by design, so partial database rollout does not break the UI.
