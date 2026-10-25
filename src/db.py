"""Small helpers for working with the SQLite analytics database."""
import sqlite3

import pandas as pd

from .config import DB_PATH, SQL_DIR


def connect():
    return sqlite3.connect(DB_PATH)


def run_sql_file(conn, filename):
    sql = (SQL_DIR / filename).read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()


def query(conn, sql, params=None):
    return pd.read_sql_query(sql, conn, params=params)


def read_table(conn, table):
    return query(conn, f"SELECT * FROM {table}")
