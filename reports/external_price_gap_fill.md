# External Price Gap Fill

- Base price dataset: `C:\Users\tlben\Bentlas\StrattonAI\data\prices\all_stock_data_extended_enriched.parquet` (parquet)
- Previous price max date: 2023-01-23
- New price max date: 2023-01-23
- Target tickers: TTM
- Tickers filled: None
- Tickers unresolved: TTM
- Total rows added: 0
- Cumulative external backfill rows: 1611
- Supabase rows upserted: 0

## Ticker Results
- TTM: provider=databento rows_found=1191 rows_added=0 range=2018-01-01 -> 2026-03-17
  - massive_rest: status=no_rows, rows=0, message=Massive REST returned zero daily aggregate rows for the requested range.
  - yfinance: status=no_rows, rows=0, message=Yahoo Finance returned no rows for the requested ticker.
  - databento: status=success, rows=1191, message=Databento returned historical OHLCV rows from XNYS.PILLAR.
