# Price Dataset Parity

## Full Dataset
- Parquet rows=34646152, tickers=9315, coverage=1962-01-02 -> 2024-11-04, rejected=106
- CSV rows=34646152, tickers=9315, coverage=1962-01-02 -> 2024-11-04, rejected=106

## Parity Checks
- distinct_ticker_count_equal: True
- max_date_equal: True
- min_date_equal: True
- missing_columns_equal: True
- rejected_rows_equal: True
- rejection_reasons_equal: True
- required_columns_equal: True
- row_count_equal: True

## Referenced Ticker Parity
- referenced_ticker_count=17, parquet_loaded=17, csv_loaded=17, mismatch_count=0
