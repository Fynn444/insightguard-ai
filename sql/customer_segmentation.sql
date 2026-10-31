WITH scoped_customers AS (
    SELECT * FROM customers
    WHERE (:workspace_id IS NULL OR workspace_id = :workspace_id)
), customer_summary AS (
    SELECT
        c.customer_id,
        c.region,
        c.contract_type,
        MAX(CASE WHEN cl.churn_label = 1 THEN 1 ELSE 0 END) AS churn_flag,
        AVG(u.engagement_index) AS avg_engagement
    FROM scoped_customers c
    LEFT JOIN usage_records u ON u.customer_id = c.customer_id
    LEFT JOIN churn_labels cl ON cl.customer_id = c.customer_id AND cl.workspace_id = c.workspace_id
    GROUP BY c.customer_id, c.region, c.contract_type
)
SELECT
    region,
    contract_type,
    ROUND(AVG(CAST(churn_flag AS REAL)), 4) AS churn_rate,
    ROUND(AVG(avg_engagement), 4) AS avg_engagement
FROM customer_summary
GROUP BY region, contract_type
ORDER BY churn_rate DESC;
