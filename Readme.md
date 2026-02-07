# Stock Data Collection DAG

## Overview

This DAG:
- Runs daily at 6 PM on weekdays (after UK market close)
- Fetches the latest trading day data for 12 UK stocks
- Stores data in PostgreSQL with duplicate prevention
- Maintains comprehensive logs for monitoring and debugging
- Only fetches the most recent data point (not historical data)


## Monitoring

### Check Latest Data
```sql
SELECT * FROM stock_data
WHERE date = (SELECT MAX(date) FROM stock_data)
ORDER BY ticker;
```

### View Recent Logs
```sql
SELECT run_date, ticker, status, records_inserted, error_message
FROM stock_data_logs
ORDER BY created_at DESC
LIMIT 20;
```

### Today's Run Summary
```sql
SELECT 
    status,
    COUNT(*) as count,
    SUM(records_inserted) as total_records
FROM stock_data_logs
WHERE DATE(run_date) = CURRENT_DATE
GROUP BY status;
```

## Troubleshooting

### Issue: No data returned for a ticker
- **Cause**: Market holiday or ticker delisted
- **Solution**: Check yfinance directly or update ticker list

### Issue: Connection refused to PostgreSQL
- **Check**: PostgreSQL is running: `sudo service postgresql status`
- **Check**: Connection details in Airflow are correct
- **Check**: User has proper permissions

### Issue: Duplicate key violation
- This shouldn't happen due to `ON CONFLICT` clause
- If it does, check the UNIQUE constraint exists

### Issue: Task failures
1. Check Airflow logs: `airflow tasks test stock_data_daily_update fetch_and_store_stock_data 2024-01-01`
2. Check database logs: `SELECT * FROM stock_data_logs WHERE status = 'FAILED'`

## Maintenance

### Backup Data
```bash
pg_dump -U airflow_user stock_data_db > backup_$(date +%Y%m%d).sql
```

### Archive Old Logs
```sql
DELETE FROM stock_data_logs 
WHERE created_at < NOW() - INTERVAL '90 days';
```

### Vacuum Database
```sql
VACUUM ANALYZE stock_data;
VACUUM ANALYZE stock_data_logs;
```

## Additional Queries

See `database_schema.sql` for helpful queries including:
- Missing data detection
- Price change calculations
- Volume statistics
- Failure rate by ticker

## License
