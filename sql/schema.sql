-- SQLite Star Schema
-- Database: bluestock_mf.db
-- Design : Star schema with dimension + fact tables
-- DIMENSION TABLES
-- dim_fund: Fund/scheme master data
CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code           INTEGER     PRIMARY KEY,
    fund_house          TEXT        NOT NULL,
    scheme_name         TEXT        NOT NULL,
    category            TEXT        NOT NULL,
    sub_category        TEXT        NOT NULL,
    plan                TEXT        NOT NULL,          -- Direct / Regular
    launch_date         DATE,
    benchmark           TEXT,
    expense_ratio_pct   REAL,
    exit_load_pct       REAL,
    min_sip_amount      INTEGER,
    min_lumpsum_amount  INTEGER,
    fund_manager        TEXT,
    risk_category       TEXT,                          -- Low / Moderate / High / Very High
    sebi_category_code  TEXT
);

-- dim_date: Calendar dimension (generated)
CREATE TABLE IF NOT EXISTS dim_date (
    date                DATE        PRIMARY KEY,
    year                INTEGER     NOT NULL,
    month               INTEGER     NOT NULL,
    day                 INTEGER     NOT NULL,
    quarter             INTEGER     NOT NULL,
    day_of_week         INTEGER     NOT NULL,          -- 0=Mon … 6=Sun
    day_name            TEXT        NOT NULL,
    month_name          TEXT        NOT NULL,
    is_weekend          INTEGER     NOT NULL DEFAULT 0, -- 0/1
    is_month_start      INTEGER     NOT NULL DEFAULT 0,
    is_month_end        INTEGER     NOT NULL DEFAULT 0,
    is_quarter_start    INTEGER     NOT NULL DEFAULT 0,
    is_quarter_end      INTEGER     NOT NULL DEFAULT 0,
    fiscal_year         INTEGER     NOT NULL           -- Indian FY: Apr-Mar
);


-- FACT TABLES


-- fact_nav: Daily net asset value per fund
CREATE TABLE IF NOT EXISTS fact_nav (
    id                  INTEGER     PRIMARY KEY AUTOINCREMENT,
    amfi_code           INTEGER     NOT NULL,
    date                DATE        NOT NULL,
    nav                 REAL        NOT NULL CHECK(nav > 0),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date)      REFERENCES dim_date(date),
    UNIQUE (amfi_code, date)
);

-- fact_transactions: Individual investor transactions
CREATE TABLE IF NOT EXISTS fact_transactions (
    id                  INTEGER     PRIMARY KEY AUTOINCREMENT,
    investor_id         TEXT        NOT NULL,
    transaction_date    DATE        NOT NULL,
    amfi_code           INTEGER     NOT NULL,
    transaction_type    TEXT        NOT NULL CHECK(transaction_type IN ('SIP','Lumpsum','Redemption')),
    amount_inr          INTEGER     NOT NULL CHECK(amount_inr > 0),
    state               TEXT,
    city                TEXT,
    city_tier           TEXT,
    age_group           TEXT,
    gender              TEXT,
    annual_income_lakh  REAL,
    payment_mode        TEXT,
    kyc_status          TEXT        CHECK(kyc_status IN ('Verified','Pending')),
    FOREIGN KEY (amfi_code)          REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (transaction_date)   REFERENCES dim_date(date)
);

-- fact_performance: Scheme return & risk metrics
CREATE TABLE IF NOT EXISTS fact_performance (
    id                  INTEGER     PRIMARY KEY AUTOINCREMENT,
    amfi_code           INTEGER     NOT NULL,
    scheme_name         TEXT,
    fund_house          TEXT,
    category            TEXT,
    plan                TEXT,
    return_1yr_pct      REAL,
    return_3yr_pct      REAL,
    return_5yr_pct      REAL,
    benchmark_3yr_pct   REAL,
    alpha               REAL,
    beta                REAL,
    sharpe_ratio        REAL,
    sortino_ratio       REAL,
    std_dev_ann_pct     REAL,
    max_drawdown_pct    REAL,
    aum_crore           INTEGER,
    expense_ratio_pct   REAL,
    morningstar_rating  INTEGER     CHECK(morningstar_rating BETWEEN 1 AND 5),
    risk_grade          TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

-- fact_aum: AUM time-series per fund house
CREATE TABLE IF NOT EXISTS fact_aum (
    id                  INTEGER     PRIMARY KEY AUTOINCREMENT,
    date                DATE        NOT NULL,
    fund_house          TEXT        NOT NULL,
    aum_lakh_crore      REAL,
    aum_crore           INTEGER,
    num_schemes         INTEGER,
    FOREIGN KEY (date) REFERENCES dim_date(date)
);

-- fact_sip_inflows: Monthly SIP industry data
CREATE TABLE IF NOT EXISTS fact_sip_inflows (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    month                   DATE    NOT NULL,
    sip_inflow_crore        INTEGER,
    active_sip_accounts_crore REAL,
    new_sip_accounts_lakh   REAL,
    sip_aum_lakh_crore      REAL,
    yoy_growth_pct          REAL,
    FOREIGN KEY (month) REFERENCES dim_date(date)
);

-- fact_category_inflows: Monthly net inflows by category
CREATE TABLE IF NOT EXISTS fact_category_inflows (
    id                  INTEGER     PRIMARY KEY AUTOINCREMENT,
    month               DATE        NOT NULL,
    category            TEXT        NOT NULL,
    net_inflow_crore    REAL,
    FOREIGN KEY (month) REFERENCES dim_date(date)
);

-- fact_folio_count: Industry-level folio counts
CREATE TABLE IF NOT EXISTS fact_folio_count (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    month                   DATE    NOT NULL,
    total_folios_crore      REAL,
    equity_folios_crore     REAL,
    debt_folios_crore       REAL,
    hybrid_folios_crore     REAL,
    others_folios_crore     REAL,
    FOREIGN KEY (month) REFERENCES dim_date(date)
);

-- fact_portfolio_holdings: Fund portfolio composition
CREATE TABLE IF NOT EXISTS fact_portfolio_holdings (
    id                  INTEGER     PRIMARY KEY AUTOINCREMENT,
    amfi_code           INTEGER     NOT NULL,
    stock_symbol        TEXT,
    stock_name          TEXT,
    sector              TEXT,
    weight_pct          REAL,
    market_value_cr     REAL,
    current_price_inr   REAL,
    portfolio_date      DATE,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

-- fact_benchmark_indices: Daily benchmark index values
CREATE TABLE IF NOT EXISTS fact_benchmark_indices (
    id                  INTEGER     PRIMARY KEY AUTOINCREMENT,
    date                DATE        NOT NULL,
    index_name          TEXT        NOT NULL,
    close_value         REAL        NOT NULL,
    FOREIGN KEY (date)  REFERENCES dim_date(date),
    UNIQUE (date, index_name)
);


-- INDEXES for query performance

CREATE INDEX IF NOT EXISTS idx_fact_nav_amfi          ON fact_nav(amfi_code);
CREATE INDEX IF NOT EXISTS idx_fact_nav_date          ON fact_nav(date);
CREATE INDEX IF NOT EXISTS idx_fact_txn_amfi          ON fact_transactions(amfi_code);
CREATE INDEX IF NOT EXISTS idx_fact_txn_date          ON fact_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_fact_txn_type          ON fact_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_fact_txn_state         ON fact_transactions(state);
CREATE INDEX IF NOT EXISTS idx_fact_aum_date          ON fact_aum(date);
CREATE INDEX IF NOT EXISTS idx_fact_aum_fh            ON fact_aum(fund_house);
CREATE INDEX IF NOT EXISTS idx_fact_perf_amfi         ON fact_performance(amfi_code);
CREATE INDEX IF NOT EXISTS idx_fact_bench_date        ON fact_benchmark_indices(date);
CREATE INDEX IF NOT EXISTS idx_fact_bench_name        ON fact_benchmark_indices(index_name);
CREATE INDEX IF NOT EXISTS idx_dim_date_year_month    ON dim_date(year, month);
