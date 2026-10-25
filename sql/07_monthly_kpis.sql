-- =====================================================================
-- 07_monthly_kpis.sql
-- Monthly business KPIs with month-over-month growth, a 3-month moving
-- average and year-to-date running totals (LAG / AVG / SUM windows).
-- =====================================================================
DROP TABLE IF EXISTS monthly_kpis;

CREATE TABLE monthly_kpis AS
WITH monthly AS (
    SELECT
        order_month,
        SUM(order_revenue)          AS revenue,
        SUM(gross_profit)           AS gross_profit,
        COUNT(*)                    AS orders,
        COUNT(DISTINCT customer_id) AS active_customers,
        COUNT(DISTINCT CASE WHEN month_number = 0 THEN customer_id END) AS new_customers
    FROM v_orders_with_cohort
    GROUP BY order_month
)
SELECT
    order_month,
    ROUND(revenue, 2)       AS revenue,
    ROUND(gross_profit, 2)  AS gross_profit,
    orders,
    active_customers,
    new_customers,
    active_customers - new_customers AS returning_customers,
    ROUND(revenue / orders, 2)       AS avg_order_value,
    ROUND(LAG(revenue) OVER w, 2)    AS prev_month_revenue,
    ROUND(100.0 * (revenue - LAG(revenue) OVER w) / LAG(revenue) OVER w, 2) AS revenue_mom_pct,
    ROUND(100.0 * (active_customers - LAG(active_customers) OVER w)
          / LAG(active_customers) OVER w, 2)                                AS customers_mom_pct,
    ROUND(AVG(revenue) OVER (ORDER BY order_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2)
                                                                            AS revenue_3m_avg,
    ROUND(SUM(revenue) OVER (PARTITION BY substr(order_month, 1, 4) ORDER BY order_month), 2)
                                                                            AS revenue_ytd
FROM monthly
WINDOW w AS (ORDER BY order_month)
ORDER BY order_month;
