# Bluestock Fintech — Data Dictionary

> **Database**: `bluestock_mf.db` (SQLite)  
> **Schema**: Star schema — 2 dimension tables, 9 fact tables  
> **Last Updated**: 2026-06-26

---

## Table of Contents

1. [dim_fund](#dim_fund) — Fund/Scheme Master
2. [dim_date](#dim_date) — Calendar Dimension
3. [fact_nav](#fact_nav) — Daily Net Asset Values
4. [fact_transactions](#fact_transactions) — Investor Transactions
5. [fact_performance](#fact_performance) — Scheme Performance Metrics
6. [fact_aum](#fact_aum) — AUM by Fund House
7. [fact_sip_inflows](#fact_sip_inflows) — Monthly SIP Inflows
8. [fact_category_inflows](#fact_category_inflows) — Category-wise Net Inflows
9. [fact_folio_count](#fact_folio_count) — Industry Folio Counts
10. [fact_portfolio_holdings](#fact_portfolio_holdings) — Portfolio Holdings
11. [fact_benchmark_indices](#fact_benchmark_indices) — Benchmark Index Values

---

## Dimension Tables

### dim_fund

Fund/scheme master data. One row per AMFI-registered mutual fund scheme.

**Source**: `01_fund_master.csv` → `data/processed/01_fund_master.csv`  
**Grain**: One row per scheme (amfi_code)  
**Row Count**: 40

| Column | SQL Type | Business Definition | Valid Values / Range |
|---|---|---|---|
| `amfi_code` | INTEGER (PK) | Unique scheme identifier assigned by AMFI (Association of Mutual Funds in India) | 6-digit integer |
| `fund_house` | TEXT | Asset Management Company (AMC) operating the fund | SBI, HDFC, ICICI Prudential, Kotak, Nippon India, Axis, Mirae Asset, Aditya Birla SL, UTI, Tata MF |
| `scheme_name` | TEXT | Full registered name of the mutual fund scheme | Free text |
| `category` | TEXT | SEBI-defined broad category | Equity, Debt, Hybrid |
| `sub_category` | TEXT | SEBI-defined sub-category within the broad category | Large Cap, Mid Cap, Small Cap, Large & Mid Cap, Flexi Cap, ELSS, Liquid, Short Duration, Corporate Bond, Balanced Advantage, Multi-Asset, Gilt Securities |
| `plan` | TEXT | Distribution plan variant | `Direct`, `Regular` |
| `launch_date` | DATE | Date when the scheme was first launched | YYYY-MM-DD |
| `benchmark` | TEXT | Reference benchmark index for performance comparison | e.g., NIFTY 50 TRI, S&P BSE 100 TRI |
| `expense_ratio_pct` | REAL | Annual total expense ratio charged to investors (percentage) | 0.0 – 5.0% |
| `exit_load_pct` | REAL | Fee charged on early redemption (percentage of NAV) | 0.0 – 2.0% |
| `min_sip_amount` | INTEGER | Minimum monthly SIP investment amount in INR | ≥ 100 |
| `min_lumpsum_amount` | INTEGER | Minimum one-time lumpsum investment amount in INR | ≥ 500 |
| `fund_manager` | TEXT | Name of the portfolio manager(s) | Free text |
| `risk_category` | TEXT | SEBI-mandated risk classification (Riskometer) | `Low`, `Moderate`, `High`, `Very High` |
| `sebi_category_code` | TEXT | SEBI category classification code | e.g., EC01, EC03, DC02 |

---

### dim_date

Calendar dimension table, auto-generated to cover the full date range of NAV history.

**Source**: Generated programmatically from NAV date range  
**Grain**: One row per calendar day  
**Row Count**: 1,608 (2022-01-03 to 2026-05-29)

| Column | SQL Type | Business Definition | Valid Values / Range |
|---|---|---|---|
| `date` | DATE (PK) | Calendar date | YYYY-MM-DD |
| `year` | INTEGER | Calendar year | 2022 – 2026 |
| `month` | INTEGER | Calendar month number | 1 – 12 |
| `day` | INTEGER | Day of month | 1 – 31 |
| `quarter` | INTEGER | Calendar quarter | 1 – 4 |
| `day_of_week` | INTEGER | ISO day of week (0 = Monday … 6 = Sunday) | 0 – 6 |
| `day_name` | TEXT | English name of the day | Monday – Sunday |
| `month_name` | TEXT | English name of the month | January – December |
| `is_weekend` | INTEGER | Whether the day falls on Saturday or Sunday | 0 (no), 1 (yes) |
| `is_month_start` | INTEGER | Whether the day is the first day of the month | 0, 1 |
| `is_month_end` | INTEGER | Whether the day is the last day of the month | 0, 1 |
| `is_quarter_start` | INTEGER | Whether the day is the first day of the quarter | 0, 1 |
| `is_quarter_end` | INTEGER | Whether the day is the last day of the quarter | 0, 1 |
| `fiscal_year` | INTEGER | Indian Fiscal Year (April–March). Apr 2024 → FY 2025 | 2022 – 2027 |

---

## Fact Tables

### fact_nav

Daily Net Asset Value (NAV) per mutual fund scheme. Forward-filled to include weekends and holidays.

**Source**: `02_nav_history.csv` → `data/processed/02_nav_history.csv`  
**Grain**: One row per (amfi_code, date)  
**Row Count**: 64,320 (46,000 original + 18,320 forward-filled)  
**Foreign Keys**: `amfi_code → dim_fund.amfi_code`, `date → dim_date.date`

| Column | SQL Type | Business Definition | Valid Values / Range |
|---|---|---|---|
| `amfi_code` | INTEGER (FK) | Scheme identifier — references `dim_fund` | Valid AMFI code |
| `date` | DATE (FK) | Date of the NAV observation | 2022-01-03 to 2026-05-29 |
| `nav` | REAL | Net Asset Value per unit in INR. For weekends/holidays, forward-filled from last trading day | > 0 (range: ~26 – ~4269) |

> **Note**: Original data contains NAV only for trading days. The cleaning pipeline forward-fills NAV for weekends and public holidays using the last available trading day's value.

---

### fact_transactions

Individual investor mutual fund transactions including demographic and geographic attributes.

**Source**: `08_investor_transactions.csv` → `data/processed/08_investor_transactions.csv`  
**Grain**: One row per transaction  
**Row Count**: 32,778  
**Foreign Keys**: `amfi_code → dim_fund.amfi_code`, `transaction_date → dim_date.date`

| Column | SQL Type | Business Definition | Valid Values / Range |
|---|---|---|---|
| `investor_id` | TEXT | Anonymised unique investor identifier | Format: INVxxxxxx |
| `transaction_date` | DATE (FK) | Date the transaction was executed | 2024-01-01 onwards |
| `amfi_code` | INTEGER (FK) | Scheme identifier — references `dim_fund` | Valid AMFI code |
| `transaction_type` | TEXT | Type of mutual fund transaction | `SIP`, `Lumpsum`, `Redemption` |
| `amount_inr` | INTEGER | Transaction amount in Indian Rupees | > 0 |
| `state` | TEXT | Indian state of the investor | Indian state names |
| `city` | TEXT | City of the investor | City names |
| `city_tier` | TEXT | City tier classification | `Tier 1`, `Tier 2`, `Tier 3` |
| `age_group` | TEXT | Age bracket of the investor | `18-25`, `26-35`, `36-45`, `46-60`, `60+` |
| `gender` | TEXT | Gender of the investor | `Male`, `Female` |
| `annual_income_lakh` | REAL | Investor's annual income in Lakhs INR | > 0 |
| `payment_mode` | TEXT | Payment method used for the transaction | `UPI`, `Net Banking`, `Mandate`, `Cheque` |
| `kyc_status` | TEXT | Know Your Customer verification status | `Verified`, `Pending` |

---

### fact_performance

Scheme-level performance, risk metrics, and ratings — point-in-time snapshot.

**Source**: `07_scheme_performance.csv` → `data/processed/07_scheme_performance.csv`  
**Grain**: One row per scheme  
**Row Count**: 40  
**Foreign Keys**: `amfi_code → dim_fund.amfi_code`

| Column | SQL Type | Business Definition | Valid Values / Range |
|---|---|---|---|
| `amfi_code` | INTEGER (FK) | Scheme identifier — references `dim_fund` | Valid AMFI code |
| `scheme_name` | TEXT | Full scheme name (denormalised for convenience) | Free text |
| `fund_house` | TEXT | AMC name (denormalised) | AMC names |
| `category` | TEXT | Fund category (denormalised) | Equity, Debt, Hybrid |
| `plan` | TEXT | Distribution plan | Direct, Regular |
| `return_1yr_pct` | REAL | Trailing 1-year return (%) | ~4% – ~25% |
| `return_3yr_pct` | REAL | Trailing 3-year CAGR (%) | ~5% – ~23% |
| `return_5yr_pct` | REAL | Trailing 5-year CAGR (%) | ~5% – ~24% |
| `benchmark_3yr_pct` | REAL | Benchmark's 3-year CAGR (%) | Numeric |
| `alpha` | REAL | Jensen's Alpha — excess return over benchmark (risk-adjusted) | Can be negative |
| `beta` | REAL | Beta coefficient — sensitivity to market movements | Typically 0.5 – 1.5 |
| `sharpe_ratio` | REAL | Sharpe Ratio — risk-adjusted return (higher = better) | Typically 0 – 3 |
| `sortino_ratio` | REAL | Sortino Ratio — downside risk-adjusted return | Typically 0 – 4 |
| `std_dev_ann_pct` | REAL | Annualised standard deviation of returns (volatility %) | > 0 |
| `max_drawdown_pct` | REAL | Maximum peak-to-trough decline (%) | Negative values |
| `aum_crore` | INTEGER | Assets Under Management in Crores INR | > 0 |
| `expense_ratio_pct` | REAL | Annual expense ratio (%) | 0.1% – 2.5% (validated) |
| `morningstar_rating` | INTEGER | Morningstar star rating | 1 – 5 |
| `risk_grade` | TEXT | Qualitative risk classification | `Low`, `Moderate`, `High`, `Very High` |

---

### fact_aum

Assets Under Management time-series data per fund house.

**Source**: `03_aum_by_fund_house.csv` → `data/processed/03_aum_by_fund_house.csv`  
**Grain**: One row per (fund_house, date)  
**Row Count**: 90  
**Foreign Keys**: `date → dim_date.date`

| Column | SQL Type | Business Definition | Valid Values / Range |
|---|---|---|---|
| `date` | DATE (FK) | Reporting date (typically end-of-quarter) | DATE |
| `fund_house` | TEXT | Asset Management Company name | AMC names |
| `aum_lakh_crore` | REAL | AUM in Lakh Crores INR (= ₹10 Trillion units) | > 0 |
| `aum_crore` | INTEGER | AUM in Crores INR | > 0 |
| `num_schemes` | INTEGER | Number of active schemes operated by the fund house | > 0 |

---

### fact_sip_inflows

Monthly industry-level SIP (Systematic Investment Plan) aggregate data.

**Source**: `04_monthly_sip_inflows.csv` → `data/processed/04_monthly_sip_inflows.csv`  
**Grain**: One row per month  
**Row Count**: 48  
**Foreign Keys**: `month → dim_date.date`

| Column | SQL Type | Business Definition | Valid Values / Range |
|---|---|---|---|
| `month` | DATE (FK) | First day of the reporting month | YYYY-MM-01 |
| `sip_inflow_crore` | INTEGER | Total SIP inflow during the month in Crores INR | > 0 |
| `active_sip_accounts_crore` | REAL | Total active SIP accounts in Crores (= 10M units) | > 0 |
| `new_sip_accounts_lakh` | REAL | New SIP accounts registered during the month in Lakhs | > 0 |
| `sip_aum_lakh_crore` | REAL | Total SIP AUM in Lakh Crores INR | > 0 |
| `yoy_growth_pct` | REAL | Year-over-year growth in SIP inflows (%) | Can be null for first year |

---

### fact_category_inflows

Monthly net inflows/outflows by SEBI mutual fund category.

**Source**: `05_category_inflows.csv` → `data/processed/05_category_inflows.csv`  
**Grain**: One row per (category, month)  
**Row Count**: 144  
**Foreign Keys**: `month → dim_date.date`

| Column | SQL Type | Business Definition | Valid Values / Range |
|---|---|---|---|
| `month` | DATE (FK) | First day of the reporting month | YYYY-MM-01 |
| `category` | TEXT | SEBI mutual fund category | Equity, Debt, Hybrid, Liquid, ETF, Others |
| `net_inflow_crore` | REAL | Net inflow (positive) or outflow (negative) in Crores INR | Can be negative (outflow) |

---

### fact_folio_count

Monthly industry-wide folio counts by fund type.

**Source**: `06_industry_folio_count.csv` → `data/processed/06_industry_folio_count.csv`  
**Grain**: One row per month  
**Row Count**: 21  
**Foreign Keys**: `month → dim_date.date`

| Column | SQL Type | Business Definition | Valid Values / Range |
|---|---|---|---|
| `month` | DATE (FK) | First day of the reporting month | YYYY-MM-01 |
| `total_folios_crore` | REAL | Total folios across all categories in Crores | > 0 |
| `equity_folios_crore` | REAL | Equity fund folios in Crores | > 0 |
| `debt_folios_crore` | REAL | Debt fund folios in Crores | > 0 |
| `hybrid_folios_crore` | REAL | Hybrid fund folios in Crores | > 0 |
| `others_folios_crore` | REAL | Other fund type folios in Crores | > 0 |

> **Note**: A "folio" is a unique investor account within a mutual fund scheme. One investor can have multiple folios.

---

### fact_portfolio_holdings

Fund-level portfolio composition showing individual stock holdings.

**Source**: `09_portfolio_holdings.csv` → `data/processed/09_portfolio_holdings.csv`  
**Grain**: One row per (amfi_code, stock_symbol)  
**Row Count**: 322  
**Foreign Keys**: `amfi_code → dim_fund.amfi_code`

| Column | SQL Type | Business Definition | Valid Values / Range |
|---|---|---|---|
| `amfi_code` | INTEGER (FK) | Scheme identifier — references `dim_fund` | Valid AMFI code |
| `stock_symbol` | TEXT | NSE/BSE ticker symbol of the held stock | e.g., RELIANCE, TCS, HDFCBANK |
| `stock_name` | TEXT | Full name of the company | Free text |
| `sector` | TEXT | Industry sector of the stock | e.g., Financial Services, IT, Energy |
| `weight_pct` | REAL | Percentage weight of the stock in the fund's portfolio | 0 – 100 (sum per fund ≈ 100%) |
| `market_value_cr` | REAL | Market value of the holding in Crores INR | > 0 |
| `current_price_inr` | REAL | Current stock price in INR | > 0 |
| `portfolio_date` | DATE | Date of the portfolio snapshot | DATE |

---

### fact_benchmark_indices

Daily closing values for benchmark market indices.

**Source**: `10_benchmark_indices.csv` → `data/processed/10_benchmark_indices.csv`  
**Grain**: One row per (index_name, date)  
**Row Count**: 8,050  
**Foreign Keys**: `date → dim_date.date`

| Column | SQL Type | Business Definition | Valid Values / Range |
|---|---|---|---|
| `date` | DATE (FK) | Trading date of the observation | 2022-01-03 onwards |
| `index_name` | TEXT | Name of the benchmark index | e.g., NIFTY 50, SENSEX, NIFTY MIDCAP 150 |
| `close_value` | REAL | Closing value of the index on the given date | > 0 |

---

## Star Schema Diagram

```
                    ┌─────────────┐
                    │  dim_date   │
                    │─────────────│
                    │ date (PK)   │
                    │ year        │
                    │ month       │
                    │ quarter     │
                    │ fiscal_year │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐      ┌─────▼─────┐     ┌────▼────┐
    │fact_nav │      │fact_txns  │     │fact_aum │
    │─────────│      │───────────│     │─────────│
    │amfi_code│──┐   │amfi_code  │──┐  │date     │
    │date     │  │   │txn_date   │  │  │aum_crore│
    │nav      │  │   │amount_inr │  │  └─────────┘
    └─────────┘  │   │txn_type   │  │
                 │   └───────────┘  │
            ┌────▼────┐             │
            │dim_fund │◄────────────┘
            │─────────│
            │amfi_code│ (PK)
            │fund_hous│
            │category │
            │risk_cat │
            └─────────┘
```

---

## Data Quality Notes

1. **NAV Forward-Fill**: 18,320 rows added for weekends/holidays using last available trading day NAV
2. **No Null Values**: All primary datasets have zero null values
3. **No Duplicates**: Zero exact duplicates found across all 10 datasets
4. **Transaction Types**: Already standardised in source — `SIP`, `Lumpsum`, `Redemption`
5. **KYC Status**: Binary enum — `Verified` or `Pending`
6. **Expense Ratios**: All within 0.55% – 1.64% (well within 0.1% – 2.5% validation range)
7. **Date Range**: NAV data spans 2022-01-03 to 2026-05-29 (4+ years)

---

## Glossary

| Term | Definition |
|---|---|
| **AMFI** | Association of Mutual Funds in India — industry body that assigns unique scheme codes |
| **NAV** | Net Asset Value — per-unit market value of a mutual fund scheme |
| **SIP** | Systematic Investment Plan — periodic (usually monthly) fixed-amount investment |
| **AUM** | Assets Under Management — total market value of all investments managed by a fund |
| **CAGR** | Compound Annual Growth Rate — annualised return over a period |
| **Alpha** | Excess return generated by a fund manager over the benchmark return |
| **Beta** | Measure of a fund's volatility relative to the market |
| **Sharpe Ratio** | Risk-adjusted return: (Fund Return - Risk-Free Rate) / Std Dev |
| **Sortino Ratio** | Downside risk-adjusted return — variant of Sharpe using only downside deviation |
| **Max Drawdown** | Largest peak-to-trough decline in fund value |
| **Expense Ratio** | Annual fee charged by the fund as a percentage of AUM |
| **Exit Load** | Fee charged when an investor redeems units before a specified period |
| **Folio** | A unique investor account number within a mutual fund scheme |
| **Crore** | Indian numbering unit = 10,000,000 (10 million) |
| **Lakh** | Indian numbering unit = 100,000 |
| **SEBI** | Securities and Exchange Board of India — market regulator |
| **KYC** | Know Your Customer — identity verification process mandated by SEBI |
