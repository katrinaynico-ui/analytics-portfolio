-- Monthly acquisition cohorts + retention (DuckDB dialect).
-- Input view: transactions (CustomerID, InvoiceDate, line_revenue, InvoiceNo, ...)
-- Retention_rate = share of cohort customers active in month_offset after first purchase.

WITH first_purchase AS (
  SELECT
    CustomerID,
    DATE_TRUNC('month', MIN(InvoiceDate)) AS cohort_month
  FROM transactions
  GROUP BY 1
),
activity AS (
  SELECT
    t.CustomerID,
    DATE_TRUNC('month', t.InvoiceDate) AS activity_month,
    SUM(t.line_revenue) AS revenue
  FROM transactions t
  GROUP BY 1, 2
),
cohort_sized AS (
  SELECT
    cohort_month,
    COUNT(*) AS cohort_size
  FROM first_purchase
  GROUP BY 1
),
joined AS (
  SELECT
    fp.cohort_month,
    a.activity_month,
    DATE_DIFF('month', fp.cohort_month, a.activity_month) AS month_offset,
    COUNT(DISTINCT a.CustomerID) AS active_customers,
    SUM(a.revenue) AS revenue
  FROM first_purchase fp
  JOIN activity a USING (CustomerID)
  GROUP BY 1, 2, 3
)
SELECT
  j.cohort_month,
  j.activity_month,
  j.month_offset,
  cs.cohort_size,
  j.active_customers,
  ROUND(j.active_customers * 1.0 / cs.cohort_size, 4) AS retention_rate,
  ROUND(j.revenue, 2) AS revenue
FROM joined j
JOIN cohort_sized cs USING (cohort_month)
WHERE j.month_offset >= 0
ORDER BY j.cohort_month, j.month_offset;
