-- =====================================================================
-- 04_revenue_contribution.sql
-- How much revenue each RFM segment and each customer decile drives.
-- =====================================================================
DROP TABLE IF EXISTS segment_summary;

CREATE TABLE segment_summary AS
WITH seg AS (
    SELECT
        segment,
        COUNT(*)          AS customers,
        SUM(monetary)     AS revenue,
        AVG(recency_days) AS avg_recency_days,
        AVG(frequency)    AS avg_frequency,
        AVG(monetary)     AS avg_monetary
    FROM rfm_segments
    GROUP BY segment
)
SELECT
    segment,
    customers,
    ROUND(100.0 * customers / SUM(customers) OVER (), 2) AS pct_customers,
    ROUND(revenue, 2)                                    AS revenue,
    ROUND(100.0 * revenue / SUM(revenue) OVER (), 2)     AS pct_revenue,
    ROUND(100.0 * SUM(revenue) OVER (ORDER BY revenue DESC ROWS UNBOUNDED PRECEDING)
          / SUM(revenue) OVER (), 2)                     AS cumulative_pct_revenue,
    RANK() OVER (ORDER BY revenue DESC)                  AS revenue_rank,
    ROUND(avg_recency_days, 1) AS avg_recency_days,
    ROUND(avg_frequency, 2)    AS avg_frequency,
    ROUND(avg_monetary, 2)     AS avg_monetary
FROM seg
ORDER BY revenue DESC;


-- Pareto view: customers ranked by spend and split into 10 equal deciles
DROP TABLE IF EXISTS customer_deciles;

CREATE TABLE customer_deciles AS
WITH ranked AS (
    SELECT customer_id, monetary,
           NTILE(10) OVER (ORDER BY monetary DESC) AS decile
    FROM rfm_segments
),
deciles AS (
    SELECT decile,
           COUNT(*)      AS customers,
           SUM(monetary) AS revenue,
           MIN(monetary) AS min_spend,
           MAX(monetary) AS max_spend
    FROM ranked
    GROUP BY decile
)
SELECT
    decile,
    customers,
    ROUND(revenue, 2)                                AS revenue,
    ROUND(100.0 * revenue / SUM(revenue) OVER (), 2) AS pct_revenue,
    ROUND(100.0 * SUM(revenue) OVER (ORDER BY decile) / SUM(revenue) OVER (), 2)
                                                     AS cumulative_pct_revenue,
    ROUND(min_spend, 2) AS min_spend,
    ROUND(max_spend, 2) AS max_spend
FROM deciles
ORDER BY decile;
