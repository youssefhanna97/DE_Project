import os
import psycopg2
from faker import Faker
import random
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}

fake = Faker()

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()

        # ---- Create tables ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            user_id INT REFERENCES users(id),
            amount NUMERIC(10,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # ---- Insert dummy users ----
    user_ids = []
    for _ in range(100):
        cur.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id;",
            (fake.name(), fake.unique.email())
        )
        user_ids.append(cur.fetchone()[0])

    # ---- Insert dummy orders ----
    for _ in range(300):
        cur.execute(
            "INSERT INTO orders (user_id, amount) VALUES (%s, %s);",
            (random.choice(user_ids), round(random.uniform(10, 500), 2))
        )

    print("✅ Tables created and dummy data inserted")
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
