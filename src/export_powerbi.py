"""Export a star-schema dataset for the Power BI dashboard (powerbi/data/)."""
from .config import POWERBI_DATA, ensure_dirs
from .db import connect, query, read_table

EXPORTS = {
    "fact_orders": """
        SELECT order_id, customer_id, order_date, order_month, cohort_month,
               month_number AS months_since_first_order,
               order_revenue AS revenue, order_cost AS cost, gross_profit, units
        FROM v_orders_with_cohort
        ORDER BY order_date, order_id
    """,
    "fact_order_lines": """
        SELECT oi.order_item_id, oi.order_id, o.customer_id, o.order_date, oi.product_id,
               oi.quantity, oi.unit_price,
               ROUND(oi.quantity * oi.unit_price, 2) AS line_revenue,
               ROUND(oi.quantity * p.unit_cost, 2)   AS line_cost
        FROM order_items AS oi
        JOIN v_orders_clean AS o ON o.order_id = oi.order_id
        JOIN products AS p ON p.product_id = oi.product_id
        ORDER BY oi.order_item_id
    """,
    "dim_customers": "SELECT * FROM customer_summary ORDER BY customer_id",
    "dim_products": "SELECT * FROM products ORDER BY product_id",
}


def main():
    ensure_dirs()
    conn = connect()
    for name, sql in EXPORTS.items():
        df = query(conn, sql)
        df.to_csv(POWERBI_DATA / f"{name}.csv", index=False)
        print(f"  powerbi/data/{name}.csv  ({len(df):,} rows)")
    for table in ("cohort_retention", "segment_summary", "monthly_kpis"):
        df = read_table(conn, table)
        df.to_csv(POWERBI_DATA / f"{table}.csv", index=False)
        print(f"  powerbi/data/{table}.csv  ({len(df):,} rows)")
    conn.close()


if __name__ == "__main__":
    main()
