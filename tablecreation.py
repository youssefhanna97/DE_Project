from airflow.providers.postgres.hooks.postgres import PostgresHook

def create_tables():
    """
    Create PostgreSQL tables if they don't exist
    """
    postgres_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    
    # Create stock data table
    create_stock_table_query = f"""
    CREATE TABLE IF NOT EXISTS {STOCK_DATA_TABLE} (
        id SERIAL PRIMARY KEY,
        date DATE NOT NULL,
        ticker VARCHAR(20) NOT NULL,
        open DECIMAL(10, 2),
        high DECIMAL(10, 2),
        low DECIMAL(10, 2),
        close DECIMAL(10, 2),
        volume BIGINT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(date, ticker)
    );
    
    CREATE INDEX IF NOT EXISTS idx_stock_date_ticker 
    ON {STOCK_DATA_TABLE}(date, ticker);
    """
    
    # Create log table
    create_log_table_query = f"""
    CREATE TABLE IF NOT EXISTS {LOG_TABLE} (
        id SERIAL PRIMARY KEY,
        run_date TIMESTAMP NOT NULL,
        ticker VARCHAR(20) NOT NULL,
        status VARCHAR(20) NOT NULL,
        records_inserted INTEGER DEFAULT 0,
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_log_run_date 
    ON {LOG_TABLE}(run_date);
    """
    
    postgres_hook.run(create_stock_table_query)
    postgres_hook.run(create_log_table_query)
    
    logging.info("Tables created successfully")