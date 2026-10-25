-- =====================================================================
-- 02_clean_orders.sql
-- Order-level revenue view used by every downstream query.
--   * keeps only completed orders (drops cancelled / returned)
--   * drops guest checkouts (no customer_id)
--   * aggregates line items to order revenue, cost and gross profit
-- =====================================================================
DROP VIEW IF EXISTS v_orders_with_cohort;
DROP VIEW IF EXISTS v_orders_clean;

CREATE VIEW v_orders_clean AS
WITH order_totals AS (
    SELECT
        oi.order_id,
        SUM(oi.quantity * oi.unit_price) AS order_revenue,
        SUM(oi.quantity * p.unit_cost)   AS order_cost,
        SUM(oi.quantity)                 AS units
    FROM order_items AS oi
    JOIN products    AS p ON p.product_id = oi.product_id
    GROUP BY oi.order_id
)
SELECT
    o.order_id,
    o.customer_id,
    o.order_date,
    strftime('%Y-%m', o.order_date)          AS order_month,
    ROUND(t.order_revenue, 2)                AS order_revenue,
    ROUND(t.order_cost, 2)                   AS order_cost,
    ROUND(t.order_revenue - t.order_cost, 2) AS gross_profit,
    t.units
FROM orders AS o
JOIN order_totals AS t ON t.order_id = o.order_id
WHERE o.status = 'completed'
  AND o.customer_id IS NOT NULL;


-- Same orders, tagged with each customer's acquisition cohort
-- (month of first purchase) and months elapsed since that cohort month.
CREATE VIEW v_orders_with_cohort AS
WITH first_purchase AS (
    SELECT customer_id, MIN(order_month) AS cohort_month
    FROM v_orders_clean
    GROUP BY customer_id
)
SELECT
    o.*,
    f.cohort_month,
    (CAST(substr(o.order_month, 1, 4) AS INTEGER) - CAST(substr(f.cohort_month, 1, 4) AS INTEGER)) * 12
  + (CAST(substr(o.order_month, 6, 2) AS INTEGER) - CAST(substr(f.cohort_month, 6, 2) AS INTEGER))
        AS month_number
FROM v_orders_clean AS o
JOIN first_purchase AS f ON f.customer_id = o.customer_id;
