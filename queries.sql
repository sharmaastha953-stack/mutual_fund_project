-- 1. Top 5 funds by latest AUM
SELECT amfi_code, MAX(aum_value) AS latest_aum
FROM fact_aum
GROUP BY amfi_code
ORDER BY latest_aum DESC
LIMIT 5;

-- 2. Average NAV per month for each fund
SELECT f.amfi_code,
       d.year,
       d.month,
       AVG(nav) AS avg_nav
FROM fact_nav n
JOIN dim_date d ON n.date_id = d.date_id
JOIN dim_fund f ON n.amfi_code = f.amfi_code
GROUP BY f.amfi_code, d.year, d.month
ORDER BY f.amfi_code, d.year, d.month;

-- 3. Year-over-year SIP growth by year
SELECT d.year,
       SUM(CASE WHEN transaction_type = 'SIP' THEN amount ELSE 0 END) AS total_sip
FROM fact_transactions t
JOIN dim_date d ON t.date_id = d.date_id
GROUP BY d.year
ORDER BY d.year;

-- 4. Transaction volume by state
SELECT state,
       COUNT(*) AS transaction_count,
       SUM(amount) AS total_amount
FROM fact_transactions
GROUP BY state
ORDER BY total_amount DESC;

-- 5. Funds with expense ratio between 0.1% and 2.5%
SELECT amfi_code,
       expense_ratio,
       COUNT(*) AS performance_rows
FROM fact_performance
WHERE expense_ratio BETWEEN 0.001 AND 2.5
GROUP BY amfi_code
ORDER BY expense_ratio ASC;

-- 6. Top 10 funds by 1-year return
SELECT amfi_code,
       AVG(return_1y) AS avg_1y_return
FROM fact_performance
GROUP BY amfi_code
ORDER BY avg_1y_return DESC
LIMIT 10;

-- 7. Monthly NAV volatility by fund
SELECT f.amfi_code,
       d.year,
       d.month,
       STDDEV(nav) AS nav_volatility
FROM fact_nav n
JOIN dim_date d ON n.date_id = d.date_id
JOIN dim_fund f ON n.amfi_code = f.amfi_code
GROUP BY f.amfi_code, d.year, d.month
ORDER BY nav_volatility DESC
LIMIT 20;

-- 8. Redemption totals by year and month
SELECT d.year,
       d.month,
       SUM(amount) AS redemption_total
FROM fact_transactions t
JOIN dim_date d ON t.date_id = d.date_id
WHERE transaction_type = 'REDEMPTION'
GROUP BY d.year, d.month
ORDER BY d.year, d.month;

-- 9. Average expense ratio by fund house
SELECT f.fund_house,
       AVG(p.expense_ratio) AS avg_expense_ratio
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
GROUP BY f.fund_house
ORDER BY avg_expense_ratio ASC;

-- 10. Funds with flagged performance anomalies
SELECT amfi_code,
       COUNT(*) AS anomaly_count
FROM fact_performance
WHERE anomaly_flag = 1
GROUP BY amfi_code
ORDER BY anomaly_count DESC;
