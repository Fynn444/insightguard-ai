WITH scoped_customers AS (
    SELECT * FROM customers
    WHERE (:workspace_id IS NULL OR workspace_id = :workspace_id)
), scoped_payments AS (
    SELECT p.* FROM payments p
    INNER JOIN scoped_customers c ON c.customer_id = p.customer_id
)
SELECT 'missing_age' AS issue_type, COUNT(*) AS issue_count FROM scoped_customers WHERE age IS NULL
UNION ALL
SELECT 'missing_monthly_spend', COUNT(*) FROM scoped_customers WHERE monthly_spend IS NULL
UNION ALL
SELECT 'unknown_contracts', COUNT(*) FROM scoped_customers WHERE contract_type = 'unknown'
UNION ALL
SELECT 'duplicate_customers', COUNT(*) FROM (
    SELECT customer_id FROM scoped_customers GROUP BY customer_id HAVING COUNT(*) > 1
)
UNION ALL
SELECT 'outlier_payment_amount', COUNT(*) FROM scoped_payments WHERE amount > 10000
UNION ALL
SELECT 'negative_tenure', COUNT(*) FROM scoped_customers WHERE tenure_months < 0;
