from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

import os
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import pandas as pd
import requests
from datetime import timedelta

load_dotenv()

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
BASE_URL = "https://www.alphavantage.co/query"

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD")
}

def extract_data(**context):
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": "GOOGL",
        "apikey": API_KEY,
        "outputsize": "compact"  
    }

    response = requests.get(BASE_URL, params=params)
    data = response.json()

    return data["Time Series (Daily)"]

def transform_data(**context):
    ti = context["ti"]
    raw_data = ti.xcom_pull(task_ids="extract_data")

    df = pd.DataFrame.from_dict(raw_data,orient="index")

    df.index = pd.to_datetime(df.index)
    df = df.astype(float)
    df.sort_index(inplace=True)

    df.columns = ["open", "high", "low", "close", "volume"]
    df.reset_index(inplace=True)
    df.rename(columns={"index": "trade_date"}, inplace=True)
    df["trade_date"] = df["trade_date"].dt.date

    return df.to_dict(orient='records')

def load_data(**context):
    ti = context["ti"]
    raw_data = ti.xcom_pull(task_ids="transform_data")

    df = pd.DataFrame(raw_data)

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS googl_daily_prices (
        trade_date DATE PRIMARY KEY,
        open NUMERIC,
        high NUMERIC,
        low NUMERIC,
        close NUMERIC,
        volume BIGINT
    );
    """
    cur.execute(create_table_sql)
    conn.commit()

    insert_sql = """
    INSERT INTO googl_daily_prices (
        trade_date, open, high, low, close, volume
        )
        VALUES %s ON CONFLICT (trade_date) DO NOTHING;
    """
    execute_values(cur, insert_sql, df.itertuples(index=False, name=None))
    conn.commit()
    cur.close()
    conn.close()
    print(f"Inserted {len(df)} rows into googl_daily_prices")


default_args = {    
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5)
    }

with DAG(
    dag_id="googl_daily_prices_pipeline",
    default_args=default_args,
    description="Daily GOOGL prices from Alpha Vantage to Postgres",
    schedule_interval="@daily",
    start_date=days_ago(1),
    catchup=False,
    tags=["stocks", "postgres", "alphavantage"],
) as dag:
    fetch = PythonOperator(
        task_id="extract_data",
        python_callable=extract_data,
    )

    transform = PythonOperator(
        task_id="transform_data",
        python_callable=transform_data,
    )

    load = PythonOperator(
        task_id="load_data",
        python_callable=load_data,
    )

    fetch >> transform >> load  