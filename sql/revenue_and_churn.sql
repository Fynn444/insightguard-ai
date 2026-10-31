WITH scoped_customers AS (
    SELECT * FROM customers
    WHERE (:workspace_id IS NULL OR workspace_id = :workspace_id)
), churn_by_contract AS (
    SELECT
        c.contract_type,
        AVG(CAST(cl.churn_label AS REAL)) AS churn_rate,
        SUM(c.total_revenue) AS total_revenue,
        COUNT(*) AS customer_count
    FROM scoped_customers c
    LEFT JOIN churn_labels cl ON cl.customer_id = c.customer_id AND cl.workspace_id = c.workspace_id
    GROUP BY c.contract_type
)
SELECT
    contract_type,
    ROUND(total_revenue, 2) AS total_revenue,
    ROUND(churn_rate, 4) AS churn_rate,
    customer_count
FROM churn_by_contract
ORDER BY total_revenue DESC;
