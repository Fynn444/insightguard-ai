WITH monthly_engagement AS (
    SELECT
        customer_id,
        month,
        AVG(engagement_index) AS engagement_score
    FROM usage_records
    GROUP BY customer_id, month
), trend AS (
    SELECT
        customer_id,
        LAG(engagement_score) OVER (PARTITION BY customer_id ORDER BY month) AS previous_score,
        engagement_score AS latest_score,
        month
    FROM monthly_engagement
)
SELECT customer_id, previous_score, latest_score, month
FROM trend
WHERE previous_score IS NOT NULL
  AND latest_score < previous_score * 0.85
ORDER BY latest_score ASC
LIMIT 25;
