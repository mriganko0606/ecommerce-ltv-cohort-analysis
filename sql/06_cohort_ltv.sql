-- =====================================================================
-- 06_cohort_ltv.sql
-- Cumulative revenue per acquired customer, by cohort and month since
-- first purchase - i.e. how lifetime value builds up over time.
-- =====================================================================
DROP TABLE IF EXISTS cohort_ltv;

CREATE TABLE cohort_ltv AS
WITH cohort_sizes AS (
    SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_size
    FROM v_orders_with_cohort
    GROUP BY cohort_month
),
cohort_revenue AS (
    SELECT cohort_month, month_number, SUM(order_revenue) AS revenue
    FROM v_orders_with_cohort
    GROUP BY cohort_month, month_number
)
SELECT
    r.cohort_month,
    r.month_number,
    s.cohort_size,
    ROUND(r.revenue, 2) AS revenue,
    ROUND(SUM(r.revenue) OVER (
        PARTITION BY r.cohort_month ORDER BY r.month_number
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) / s.cohort_size, 2) AS cumulative_revenue_per_customer
FROM cohort_revenue AS r
JOIN cohort_sizes   AS s ON s.cohort_month = r.cohort_month
ORDER BY r.cohort_month, r.month_number;
