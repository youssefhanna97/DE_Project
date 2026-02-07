from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import psycopg2
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import logging
import os

TICKERS = ["III.L", "AAF.L", "ANTO.L", "AZN.L", "BME.L", "BAB.L",
           "BA.L", "BARC.L", "BWY.L", "BKG.L", "BP.L", "BRBY.L"]
POSTGRES_CONN_ID = 'postgres_default'
SCHEMA_NAME = "stg_stock"
STOCK_DATA_TABLE = 'stock_data'
LOG_TABLE = 'stock_data_logs'

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}


def fetch_and_store_stock_data(**context):
    """
    Fetch latest stock data for each ticker and store in PostgreSQL
    """
    postgres_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    run_date = datetime.now()
    
    total_success = 0
    total_failed = 0
    
    for ticker in TICKERS:
        try:
            logging.info(f"Fetching data for {ticker}")
            
            data = yf.download(ticker, period="5d", interval="1d", progress=False)
            
            if data.empty:
                raise ValueError(f"No data returned for {ticker}")
            
            # Handle MultiIndex columns
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            data = data.reset_index()
            
            # Get only the latest date
            latest_data = data.iloc[-1:].copy()
            latest_data['Ticker'] = ticker
            
            # Standardize column names
            latest_data = latest_data.rename(columns={
                'Date': 'date',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume',
                'Ticker': 'ticker'
            })
            
            latest_data = latest_data[['date', 'ticker', 'open', 'high', 'low', 'close', 'volume']]
            
            # Convert date to string format for PostgreSQL
            latest_data['date'] = pd.to_datetime(latest_data['date']).dt.date
            
            # Insert data using INSERT ON CONFLICT to handle duplicates
            insert_query = f"""
            INSERT INTO {SCHEMA_NAME}.{STOCK_DATA_TABLE} (date, ticker, open, high, low, close, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (date, ticker) 
            DO UPDATE SET 
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume,
                created_at = CURRENT_TIMESTAMP;
            """
            
            for _, row in latest_data.iterrows():
                postgres_hook.run(insert_query, parameters=(
                    row['date'],
                    row['ticker'],
                    float(row['open']),
                    float(row['high']),
                    float(row['low']),
                    float(row['close']),
                    int(row['volume'])
                ))
            
            # Log success
            log_query = f"""
            INSERT INTO {SCHEMA_NAME}.{LOG_TABLE} (run_date, ticker, status, records_inserted)
            VALUES (%s, %s, %s, %s);
            """
            postgres_hook.run(log_query, parameters=(
                run_date,
                ticker,
                'SUCCESS',
                len(latest_data)
            ))
            
            total_success += 1
            logging.info(f"Successfully inserted {len(latest_data)} record(s) for {ticker}")
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Error processing {ticker}: {error_msg}")
            
            # Log failure
            log_query = f"""
            INSERT INTO {LOG_TABLE} (run_date, ticker, status, records_inserted, error_message)
            VALUES (%s, %s, %s, %s, %s);
            """
            postgres_hook.run(log_query, parameters=(
                run_date,
                ticker,
                'FAILED',
                0,
                error_msg[:500] 
            ))
            
            total_failed += 1
    
    logging.info(f"Processing complete. Success: {total_success}, Failed: {total_failed}")
    
    # Push results to XCom for monitoring
    context['ti'].xcom_push(key='total_success', value=total_success)
    context['ti'].xcom_push(key='total_failed', value=total_failed)

def validate_data(**context):
    """
    Validate that data was inserted successfully
    """
    postgres_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    run_date = context['execution_date'].date()
    
    # Check how many tickers have data for today
    check_query = f"""
    SELECT COUNT(DISTINCT ticker) as ticker_count
    FROM {SCHEMA_NAME}.{STOCK_DATA_TABLE}
    WHERE date = %s;
    """
    
    result = postgres_hook.get_first(check_query, parameters=(run_date,))
    ticker_count = result[0] if result else 0
    
    logging.info(f"Found data for {ticker_count} tickers on {run_date}")
    
    # Check logs for failures
    log_query = f"""
    SELECT ticker, error_message
    FROM {SCHEMA_NAME}.{LOG_TABLE}
    WHERE DATE(run_date) = %s AND status = 'FAILED';
    """
    
    failed_tickers = postgres_hook.get_records(log_query, parameters=(run_date,))
    
    if failed_tickers:
        logging.warning(f"Failed tickers: {failed_tickers}")
    
    return ticker_count


# Define the DAG
with DAG(
    'stock_data_daily_update',
    default_args=default_args,
    description='Fetch latest stock data from Yahoo Finance and store in PostgreSQL',
    schedule_interval='0 18 * * 1-5',  # Run at 6 PM on weekdays (after market close)
    catchup=False,
    tags=['stocks', 'finance', 'yfinance'],
) as dag:
    
    # Task 1: Fetch and store stock data
    fetch_data_task = PythonOperator(
        task_id='fetch_and_store_stock_data',
        python_callable=fetch_and_store_stock_data,
        provide_context=True,
    )
    
    # Task 2: Validate data
    validate_data_task = PythonOperator(
        task_id='validate_data',
        python_callable=validate_data,
        provide_context=True,
    )
    
    # Define task dependencies
    fetch_data_task >> validate_data_task
