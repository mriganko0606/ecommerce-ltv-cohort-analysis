-- =====================================================================
-- 08_customer_summary.sql
-- One row per purchasing customer: profile, cohort, historical value,
-- RFM segment and the 12-month activity flags used by the CLV model.
--
-- CLV windows (relative to the last order date in the data):
--   last 12m  = (last_date - 12 months, last_date]
--   prior 12m = (last_date - 24 months, last_date - 12 months]
-- These match DATESINPERIOD(..., -12, MONTH) in the Power BI measures.
-- =====================================================================
DROP TABLE IF EXISTS customer_summary;

CREATE TABLE customer_summary AS
WITH bounds AS (
    SELECT
        MAX(order_date)                   AS last_date,
        date(MAX(order_date), '-12 months') AS cut_12m,
        date(MAX(order_date), '-24 months') AS cut_24m
    FROM v_orders_clean
),
per_customer AS (
    SELECT
        o.customer_id,
        MIN(o.order_date)  AS first_order_date,
        MAX(o.order_date)  AS last_order_date,
        COUNT(*)           AS orders,
        SUM(o.order_revenue) AS revenue,
        SUM(o.gross_profit)  AS gross_profit,
        SUM(CASE WHEN o.order_date > b.cut_12m THEN o.order_revenue ELSE 0 END) AS revenue_last_12m,
        SUM(CASE WHEN o.order_date > b.cut_12m THEN o.gross_profit  ELSE 0 END) AS gross_profit_last_12m,
        MAX(CASE WHEN o.order_date > b.cut_12m THEN 1 ELSE 0 END)               AS active_last_12m,
        MAX(CASE WHEN o.order_date > b.cut_24m AND o.order_date <= b.cut_12m
                 THEN 1 ELSE 0 END)                                             AS active_prior_12m
    FROM v_orders_clean AS o
    CROSS JOIN bounds AS b
    GROUP BY o.customer_id
)
SELECT
    c.customer_id,
    c.country,
    c.acquisition_channel,
    c.signup_date,
    p.first_order_date,
    strftime('%Y-%m', p.first_order_date)        AS cohort_month,
    p.last_order_date,
    p.orders,
    ROUND(p.revenue, 2)                          AS historical_revenue,
    ROUND(p.gross_profit, 2)                     AS historical_gross_profit,
    ROUND(p.revenue / p.orders, 2)               AS avg_order_value,
    CAST(julianday(p.last_order_date) - julianday(p.first_order_date) AS INTEGER) AS lifespan_days,
    ROUND(p.revenue_last_12m, 2)                 AS revenue_last_12m,
    ROUND(p.gross_profit_last_12m, 2)            AS gross_profit_last_12m,
    p.active_last_12m,
    p.active_prior_12m,
    r.recency_days,
    r.r_score,
    r.f_score,
    r.m_score,
    r.rfm_cell,
    r.segment,
    RANK() OVER (ORDER BY p.revenue DESC)        AS revenue_rank
FROM per_customer AS p
JOIN customers    AS c ON c.customer_id = p.customer_id
JOIN rfm_segments AS r ON r.customer_id = p.customer_id;
