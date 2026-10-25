"""Load raw CSVs into SQLite and run the SQL pipeline (sql/02_*.sql onwards)."""
import pandas as pd

from .config import DATA_RAW, DB_PATH, SQL_DIR, ensure_dirs
from .db import connect, query, run_sql_file

TABLES = ["products", "customers", "orders", "order_items"]


def main():
    ensure_dirs()
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = connect()
    run_sql_file(conn, "01_schema.sql")
    for table in TABLES:
        df = pd.read_csv(DATA_RAW / f"{table}.csv")
        df.to_sql(table, conn, if_exists="append", index=False)

    for sql_file in sorted(SQL_DIR.glob("*.sql")):
        if sql_file.name != "01_schema.sql":
            print(f"  running {sql_file.name}")
            run_sql_file(conn, sql_file.name)

    counts = query(conn, """
        SELECT 'orders (raw)' AS item, COUNT(*) AS n FROM orders
        UNION ALL SELECT 'orders (clean)', COUNT(*) FROM v_orders_clean
        UNION ALL SELECT 'customers with orders', COUNT(*) FROM customer_summary
    """)
    print(counts.to_string(index=False))
    conn.close()


if __name__ == "__main__":
    main()
