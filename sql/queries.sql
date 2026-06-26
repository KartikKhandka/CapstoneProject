-- 10 Analytical SQL Queries
-- Database: bluestock_mf.db (SQLite)
-- Q1: Top 5 Funds by AUM (Assets Under Management)

SELECT
    fp.amfi_code,
    fp.scheme_name,
    fp.fund_house,
    fp.category,
    fp.aum_crore,
    fp.morningstar_rating
FROM fact_performance fp
ORDER BY fp.aum_crore DESC
LIMIT 5;



-- Q2: Average NAV per Month (across all funds)

SELECT
    d.year,
    d.month,
    d.month_name,
    ROUND(AVG(fn.nav), 4)   AS avg_nav,
    COUNT(DISTINCT fn.amfi_code) AS num_funds,
    COUNT(*)                 AS nav_records
FROM fact_nav fn
JOIN dim_date d ON fn.date = d.date
GROUP BY d.year, d.month
ORDER BY d.year, d.month;

-- Q3: SIP Year-over-Year Growth

SELECT
    CAST(strftime('%Y', month) AS INTEGER) AS year,
    SUM(sip_inflow_crore)                  AS total_sip_inflow_crore,
    ROUND(AVG(yoy_growth_pct), 2)          AS avg_yoy_growth_pct,
    ROUND(MAX(active_sip_accounts_crore), 2) AS peak_active_accounts_crore,
    ROUND(SUM(new_sip_accounts_lakh), 1)   AS total_new_accounts_lakh
FROM fact_sip_inflows
GROUP BY year
ORDER BY year;


-- Q4: Transaction Count & Volume by State (Top 10)

SELECT
    ft.state,
    COUNT(*)                             AS txn_count,
    SUM(ft.amount_inr)                   AS total_amount_inr,
    ROUND(AVG(ft.amount_inr), 0)         AS avg_amount_inr,
    SUM(CASE WHEN ft.transaction_type = 'SIP' THEN 1 ELSE 0 END)        AS sip_count,
    SUM(CASE WHEN ft.transaction_type = 'Lumpsum' THEN 1 ELSE 0 END)    AS lumpsum_count,
    SUM(CASE WHEN ft.transaction_type = 'Redemption' THEN 1 ELSE 0 END) AS redemption_count
FROM fact_transactions ft
GROUP BY ft.state
ORDER BY total_amount_inr DESC
LIMIT 10;



-- Q5: Funds with Expense Ratio < 1%

SELECT
    df.amfi_code,
    df.scheme_name,
    df.fund_house,
    df.category,
    df.plan,
    df.expense_ratio_pct,
    fp.return_1yr_pct,
    fp.sharpe_ratio,
    fp.morningstar_rating
FROM dim_fund df
LEFT JOIN fact_performance fp ON df.amfi_code = fp.amfi_code
WHERE df.expense_ratio_pct < 1.0
ORDER BY df.expense_ratio_pct ASC;



-- Q6: Monthly Transaction Volume Trend

SELECT
    d.year,
    d.month,
    d.month_name,
    COUNT(*)                                     AS txn_count,
    SUM(ft.amount_inr)                           AS total_volume_inr,
    ROUND(AVG(ft.amount_inr), 0)                 AS avg_ticket_size,
    SUM(CASE WHEN ft.transaction_type = 'SIP'        THEN ft.amount_inr ELSE 0 END) AS sip_volume,
    SUM(CASE WHEN ft.transaction_type = 'Lumpsum'    THEN ft.amount_inr ELSE 0 END) AS lumpsum_volume,
    SUM(CASE WHEN ft.transaction_type = 'Redemption' THEN ft.amount_inr ELSE 0 END) AS redemption_volume
FROM fact_transactions ft
JOIN dim_date d ON ft.transaction_date = d.date
GROUP BY d.year, d.month
ORDER BY d.year, d.month;



-- Q7: Top 5 Fund Houses by Total Transaction Amount

SELECT
    df.fund_house,
    COUNT(*)                     AS txn_count,
    SUM(ft.amount_inr)           AS total_amount_inr,
    COUNT(DISTINCT ft.investor_id) AS unique_investors,
    COUNT(DISTINCT ft.amfi_code)   AS schemes_traded,
    ROUND(AVG(ft.amount_inr), 0)   AS avg_ticket_size
FROM fact_transactions ft
JOIN dim_fund df ON ft.amfi_code = df.amfi_code
GROUP BY df.fund_house
ORDER BY total_amount_inr DESC
LIMIT 5;



-- Q8: Gender-wise Investment Distribution

SELECT
    ft.gender,
    COUNT(*)                             AS txn_count,
    COUNT(DISTINCT ft.investor_id)       AS unique_investors,
    SUM(ft.amount_inr)                   AS total_invested_inr,
    ROUND(AVG(ft.amount_inr), 0)         AS avg_amount_inr,
    ROUND(AVG(ft.annual_income_lakh), 2) AS avg_income_lakh,
    SUM(CASE WHEN ft.transaction_type = 'SIP' THEN 1 ELSE 0 END)
        * 100.0 / COUNT(*)              AS sip_pct
FROM fact_transactions ft
GROUP BY ft.gender
ORDER BY total_invested_inr DESC;



-- Q9: Age Group × Risk Category Cross-Tabulation

SELECT
    ft.age_group,
    df.risk_category,
    COUNT(*)                         AS txn_count,
    SUM(ft.amount_inr)               AS total_amount_inr,
    COUNT(DISTINCT ft.investor_id)   AS unique_investors,
    ROUND(AVG(ft.amount_inr), 0)     AS avg_ticket_size
FROM fact_transactions ft
JOIN dim_fund df ON ft.amfi_code = df.amfi_code
GROUP BY ft.age_group, df.risk_category
ORDER BY ft.age_group, df.risk_category;



-- Q10: Category-wise Net Inflow Trend (Quarterly)

SELECT
    CAST(strftime('%Y', ci.month) AS INTEGER) AS year,
    CASE
        WHEN CAST(strftime('%m', ci.month) AS INTEGER) BETWEEN 1 AND 3 THEN 'Q1'
        WHEN CAST(strftime('%m', ci.month) AS INTEGER) BETWEEN 4 AND 6 THEN 'Q2'
        WHEN CAST(strftime('%m', ci.month) AS INTEGER) BETWEEN 7 AND 9 THEN 'Q3'
        ELSE 'Q4'
    END AS quarter,
    ci.category,
    ROUND(SUM(ci.net_inflow_crore), 2)   AS total_net_inflow_crore,
    ROUND(AVG(ci.net_inflow_crore), 2)   AS avg_monthly_inflow_crore,
    COUNT(*)                              AS months_count
FROM fact_category_inflows ci
GROUP BY year, quarter, ci.category
ORDER BY year, quarter, total_net_inflow_crore DESC;
