-- =====================================================================
-- 05_cohort_retention.sql
-- Monthly acquisition cohorts: % of each cohort that purchases again
-- N months after their first purchase (month 0 = 100%).
-- =====================================================================
DROP TABLE IF EXISTS cohort_retention;

CREATE TABLE cohort_retention AS
WITH cohort_activity AS (
    SELECT
        cohort_month,
        month_number,
        COUNT(DISTINCT customer_id) AS active_customers
    FROM v_orders_with_cohort
    GROUP BY cohort_month, month_number
)
SELECT
    cohort_month,
    month_number,
    active_customers,
    FIRST_VALUE(active_customers) OVER (
        PARTITION BY cohort_month ORDER BY month_number
    ) AS cohort_size,
    ROUND(100.0 * active_customers / FIRST_VALUE(active_customers) OVER (
        PARTITION BY cohort_month ORDER BY month_number
    ), 2) AS retention_pct
FROM cohort_activity
ORDER BY cohort_month, month_number;
