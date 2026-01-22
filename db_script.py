import os
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import pandas as pd
import requests

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


params = {
    "function": "TIME_SERIES_DAILY",
    "symbol": "GOOGL",
    "apikey": API_KEY,
    "outputsize": "compact"  
}

response = requests.get(BASE_URL, params=params)
data = response.json()

df = pd.DataFrame.from_dict(
    data["Time Series (Daily)"],
    orient="index"
)

df.index = pd.to_datetime(df.index)
df = df.astype(float)
df.sort_index(inplace=True)

df.columns = ["open", "high", "low", "close", "volume"]
df.reset_index(inplace=True)
df.rename(columns={"index": "trade_date"}, inplace=True)
df["trade_date"] = df["trade_date"].dt.date

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

records = list(df.itertuples(index=False, name=None))
# We can use df.to_sql('target table', conn, if_exist = '', index, method = 'multi')
# but on conflict won't be an option and we will have to clean the df in python first
insert_sql = """
INSERT INTO googl_daily_prices (
    trade_date, open, high, low, close, volume
    )
    VALUES %s ON CONFLICT (trade_date) DO NOTHING;
"""
execute_values(cur, insert_sql, records)
conn.commit()
cur.close()
conn.close()
print(f"Inserted {len(df)} rows into googl_daily_prices")
