-- =====================================================================
-- 03_rfm_segmentation.sql
-- RFM (Recency, Frequency, Monetary) scoring and segmentation.
--   Recency   = days since last purchase, measured from the day after
--               the last order in the dataset (snapshot date)
--   Frequency = number of completed orders
--   Monetary  = total completed revenue
-- Each dimension is scored 1-5 with NTILE(5); 5 = best.
-- =====================================================================
DROP TABLE IF EXISTS rfm_segments;

CREATE TABLE rfm_segments AS
WITH snapshot AS (
    SELECT date(MAX(order_date), '+1 day') AS snapshot_date
    FROM v_orders_clean
),
customer_metrics AS (
    SELECT
        customer_id,
        MAX(order_date)          AS last_order_date,
        COUNT(DISTINCT order_id) AS frequency,
        ROUND(SUM(order_revenue), 2) AS monetary
    FROM v_orders_clean
    GROUP BY customer_id
),
rfm_base AS (
    SELECT
        cm.*,
        CAST(julianday(s.snapshot_date) - julianday(cm.last_order_date) AS INTEGER) AS recency_days
    FROM customer_metrics AS cm
    CROSS JOIN snapshot AS s
),
rfm_scores AS (
    SELECT
        *,
        -- Most recent customers land in the top tile -> score 5
        NTILE(5) OVER (ORDER BY recency_days DESC)        AS r_score,
        -- Ties on order count broken by spend, so the scores are stable
        NTILE(5) OVER (ORDER BY frequency, monetary)       AS f_score,
        NTILE(5) OVER (ORDER BY monetary)                  AS m_score
    FROM rfm_base
)
SELECT
    customer_id,
    last_order_date,
    recency_days,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    CAST(r_score AS TEXT) || f_score || m_score AS rfm_cell,
    r_score + f_score + m_score                AS rfm_total,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyal Customers'
        WHEN r_score =  5 AND f_score =  1 THEN 'New Customers'
        WHEN r_score >= 4                  THEN 'Potential Loyalists'
        WHEN r_score <= 2 AND f_score >= 4 THEN 'Cannot Lose Them'
        WHEN r_score <= 2 AND f_score =  3 THEN 'At Risk'
        WHEN r_score =  3                  THEN 'Need Attention'
        WHEN r_score =  2                  THEN 'Hibernating'
        ELSE 'Lost'
    END AS segment
FROM rfm_scores;

CREATE INDEX idx_rfm_customer ON rfm_segments (customer_id);
