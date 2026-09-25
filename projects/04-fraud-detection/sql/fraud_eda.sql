-- DuckDB EDA aggregates for credit-card fraud (portfolio).
-- Expects a registered view/table named `tx` with columns Time, Amount, Class, V1..V28.

SELECT
  COUNT(*) AS n_transactions,
  SUM(Class) AS n_fraud,
  ROUND(100.0 * SUM(Class) / COUNT(*), 4) AS fraud_pct,
  ROUND(AVG(Amount), 4) AS mean_amount,
  ROUND(MEDIAN(Amount), 4) AS median_amount,
  ROUND(AVG(CASE WHEN Class = 1 THEN Amount END), 4) AS mean_amount_fraud,
  ROUND(AVG(CASE WHEN Class = 0 THEN Amount END), 4) AS mean_amount_legit,
  ROUND(MIN(Time), 1) AS time_min_s,
  ROUND(MAX(Time), 1) AS time_max_s,
  ROUND((MAX(Time) - MIN(Time)) / 3600.0, 2) AS span_hours
FROM tx;

-- Amount buckets × class (coarse histogram)
SELECT
  CASE
    WHEN Amount < 1 THEN '0_<1'
    WHEN Amount < 10 THEN '1_1-10'
    WHEN Amount < 50 THEN '2_10-50'
    WHEN Amount < 100 THEN '3_50-100'
    WHEN Amount < 500 THEN '4_100-500'
    ELSE '5_500+'
  END AS amount_bucket,
  Class AS is_fraud,
  COUNT(*) AS n
FROM tx
GROUP BY 1, 2
ORDER BY 1, 2;

-- Hour-of-day proxy from Time (seconds from first tx) × fraud rate
SELECT
  CAST(FLOOR((Time % 86400) / 3600) AS INTEGER) AS hour_of_day,
  COUNT(*) AS n,
  SUM(Class) AS n_fraud,
  ROUND(100.0 * SUM(Class) / COUNT(*), 4) AS fraud_pct
FROM tx
GROUP BY 1
ORDER BY 1;
