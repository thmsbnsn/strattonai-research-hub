# Financial News Dataset Inspection

- Canonical source: `C:\Users\tlben\Bentlas\StrattonAI\data\events\financialNews\financial_news_events.csv`
- Row count: 3024
- Date range: 2025-02-01 -> 2025-08-14
- Duplicate rows: 0 (0.00%)

## Columns
- Date
- Headline
- Source
- Market_Event
- Market_Index
- Index_Change_Percent
- Trading_Volume
- Sentiment
- Sector
- Impact_Level
- Related_Company
- News_Url

## Missing Key Fields
- Date: 0
- Headline: 148
- Source: 0
- Market_Event: 0
- Related_Company: 0

## Company Mapping
- Apple Inc.: AAPL (existing_us_primary)
- Boeing: BA (existing_us_primary)
- ExxonMobil: XOM (existing_us_primary)
- Goldman Sachs: GS (existing_us_primary)
- JP Morgan Chase: JPM (existing_us_primary)
- Microsoft: MSFT (existing_us_primary)
- Tata Motors: TTM (nyse_adr)
- Tesla: TSLA (existing_us_primary)
- UNMAPPED Reliance Industries: 296 rows. Reason: Skipped because the project does not yet define a canonical foreign-listing convention across NSE, BSE, and depository receipt symbols.
- UNMAPPED Samsung Electronics: 336 rows. Reason: Skipped because the project does not yet define a canonical foreign-listing convention across KRX primary shares, London GDRs, and OTC lines.

## Alternate Representations
- financial_news_events.csv: 656483 bytes
- financial_news_events.json: 1223829 bytes
- financial_news_events.xlsx: 215208 bytes
