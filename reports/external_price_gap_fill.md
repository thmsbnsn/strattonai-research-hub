# External Price Gap Fill

- Base price dataset: `C:\Users\tlben\Bentlas\StrattonAI\data\prices\all_stock_data_extended.parquet` (parquet)
- Previous price max date: 2026-03-13
- New price max date: 2026-03-13
- Target tickers: TTM
- Tickers filled: None
- Tickers unresolved: TTM
- Total rows added: 0
- Cumulative external backfill rows: 0
- Supabase rows upserted: 0

## Ticker Results
- TTM: provider=None rows_found=0 rows_added=0 range=2025-02-01 -> 2025-09-28
  - massive_rest: status=no_rows, rows=0, message=Massive REST returned zero daily aggregate rows for the requested range.
  - massive_flatfiles: status=restricted, rows=0, message=Massive flat-file credentials can list day_aggs_v1 keys but cannot download objects (403 Forbidden).
  - alpaca: status=no_rows, rows=0, message=Alpaca returned no bars. Asset status=inactive tradable=False exchange=NYSE.
  - fmp: status=restricted, rows=0, message=Premium Query Parameter: 'Special Endpoint : This value set for 'symbol' is not available under your current subscription please visit our subscription page to upgrade your plan at https://financialmodelingprep.com/
  - alpha_vantage: status=restricted, rows=0, message=Thank you for using Alpha Vantage! The outputsize=full parameter value is a premium feature for the TIME_SERIES_DAILY endpoint. You may subscribe to any of the premium plans at https://www.alphavantage.co/premium/ to instantly unlock all premium features
