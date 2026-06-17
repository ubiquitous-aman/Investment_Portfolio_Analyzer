import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "portfolio.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def initialize_database():
    conn = get_connection()

    schema = """CREATE TABLE IF NOT EXISTS holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    buy_price REAL NOT NULL
);"""

    conn.executescript(schema)

    conn.commit()
    conn.close()


def add_holding(ticker, quantity, buy_price):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO holdings
        (ticker, quantity, buy_price)
        VALUES (?, ?, ?)
        """,
        (ticker, quantity, buy_price),
    )

    conn.commit()
    conn.close()


def get_all_holdings():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, ticker, quantity, buy_price
        FROM holdings
        ORDER BY id DESC
        """)

    rows = cursor.fetchall()
    conn.close()
    return rows


def delete_holding(holding_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM holdings
        WHERE id = ?
        """,
        (holding_id,),
    )

    conn.commit()
    conn.close()
