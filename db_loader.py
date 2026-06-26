"""
Day 2: SQLite Database Loader

"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from sqlalchemy import create_engine, text

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROCESSED_DIR = Path("data/processed")
DB_PATH = Path("data/bluestock_mf.db")
SCHEMA_PATH = Path("sql/schema.sql")

# Remove existing DB to start fresh
if DB_PATH.exists():
    DB_PATH.unlink()
    print(f"  🗑  Removed existing database: {DB_PATH}")

# Create SQLAlchemy engine
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
print(f"  🔗 Created engine: sqlite:///{DB_PATH}")


# 1. SCHEMA — indexes will be created AFTER data loading

print("\n" + "=" * 70)
print("  Schema: tables created via to_sql(); indexes deferred")
print("=" * 70)

schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")

print("  ✔ Schema created successfully")



# 2. LOAD DIMENSION TABLES


#| dim_fund |
print("\n" + "─" * 70)
print("  Loading: dim_fund")
print("─" * 70)

fm = pd.read_csv(PROCESSED_DIR / "01_fund_master.csv", parse_dates=["launch_date"])
fm.to_sql("dim_fund", engine, if_exists="replace", index=False)
print(f"  ✔ dim_fund loaded: {len(fm)} rows")


# ── dim_date (generated) ────
print("\n" + "─" * 70)
print("  Generating: dim_date")
print("─" * 70)

# Derive date range from NAV history
nav = pd.read_csv(PROCESSED_DIR / "02_nav_history.csv", parse_dates=["date"])
date_min = nav["date"].min()
date_max = nav["date"].max()

# Generate full calendar
dates = pd.date_range(date_min, date_max, freq="D")
dim_date = pd.DataFrame({"date": dates})
dim_date["year"] = dim_date["date"].dt.year
dim_date["month"] = dim_date["date"].dt.month
dim_date["day"] = dim_date["date"].dt.day
dim_date["quarter"] = dim_date["date"].dt.quarter
dim_date["day_of_week"] = dim_date["date"].dt.dayofweek
dim_date["day_name"] = dim_date["date"].dt.day_name()
dim_date["month_name"] = dim_date["date"].dt.month_name()
dim_date["is_weekend"] = (dim_date["day_of_week"] >= 5).astype(int)
dim_date["is_month_start"] = dim_date["date"].dt.is_month_start.astype(int)
dim_date["is_month_end"] = dim_date["date"].dt.is_month_end.astype(int)
dim_date["is_quarter_start"] = dim_date["date"].dt.is_quarter_start.astype(int)
dim_date["is_quarter_end"] = dim_date["date"].dt.is_quarter_end.astype(int)
# Indian fiscal year: Apr-Mar
dim_date["fiscal_year"] = dim_date.apply(
    lambda r: r["year"] + 1 if r["month"] >= 4 else r["year"], axis=1
)

dim_date.to_sql("dim_date", engine, if_exists="replace", index=False)
print(f"  ✔ dim_date generated & loaded: {len(dim_date)} rows ({date_min.date()} → {date_max.date()})")


# 3. LOAD FACT TABLES


#fact_nav
print("\n" + "─" * 70)
print("  Loading: fact_nav")
print("─" * 70)

nav.to_sql("fact_nav", engine, if_exists="replace", index=False)
print(f"  ✔ fact_nav loaded: {len(nav):,} rows")


#fact_transactions
print("\n" + "─" * 70)
print("  Loading: fact_transactions")
print("─" * 70)

txn = pd.read_csv(PROCESSED_DIR / "08_investor_transactions.csv",
                  parse_dates=["transaction_date"])
txn.to_sql("fact_transactions", engine, if_exists="replace", index=False)
print(f"  ✔ fact_transactions loaded: {len(txn):,} rows")


#fact_performance 
print("\n" + "─" * 70)
print("  Loading: fact_performance")
print("─" * 70)

perf = pd.read_csv(PROCESSED_DIR / "07_scheme_performance.csv")
perf.to_sql("fact_performance", engine, if_exists="replace", index=False)
print(f"  ✔ fact_performance loaded: {len(perf)} rows")


#fact_aum 
print("\n" + "─" * 70)
print("  Loading: fact_aum")
print("─" * 70)

aum = pd.read_csv(PROCESSED_DIR / "03_aum_by_fund_house.csv", parse_dates=["date"])
aum.to_sql("fact_aum", engine, if_exists="replace", index=False)
print(f"  ✔ fact_aum loaded: {len(aum)} rows")


# fact_sip_inflow
print("\n" + "─" * 70)
print("  Loading: fact_sip_inflows")
print("─" * 70)

sip = pd.read_csv(PROCESSED_DIR / "04_monthly_sip_inflows.csv", parse_dates=["month"])
sip.to_sql("fact_sip_inflows", engine, if_exists="replace", index=False)
print(f"  ✔ fact_sip_inflows loaded: {len(sip)} rows")


#fact_category_inflows 
print("\n" + "─" * 70)
print("  Loading: fact_category_inflows")
print("─" * 70)

cat = pd.read_csv(PROCESSED_DIR / "05_category_inflows.csv", parse_dates=["month"])
cat.to_sql("fact_category_inflows", engine, if_exists="replace", index=False)
print(f"  ✔ fact_category_inflows loaded: {len(cat)} rows")


#fact_folio_count
print("\n" + "─" * 70)
print("  Loading: fact_folio_count")
print("─" * 70)

folio = pd.read_csv(PROCESSED_DIR / "06_industry_folio_count.csv", parse_dates=["month"])
folio.to_sql("fact_folio_count", engine, if_exists="replace", index=False)
print(f"  ✔ fact_folio_count loaded: {len(folio)} rows")


#fact_portfolio_holdings
print("\n" + "─" * 70)
print("  Loading: fact_portfolio_holdings")
print("─" * 70)

hold = pd.read_csv(PROCESSED_DIR / "09_portfolio_holdings.csv",
                   parse_dates=["portfolio_date"])
hold.to_sql("fact_portfolio_holdings", engine, if_exists="replace", index=False)
print(f"  ✔ fact_portfolio_holdings loaded: {len(hold)} rows")


#fact_benchmark_indices 
print("\n" + "─" * 70)
print("  Loading: fact_benchmark_indices")
print("─" * 70)

bench = pd.read_csv(PROCESSED_DIR / "10_benchmark_indices.csv", parse_dates=["date"])
bench.to_sql("fact_benchmark_indices", engine, if_exists="replace", index=False)
print(f"\n  ✔ fact_benchmark_indices loaded: {len(bench)} rows")



# 4. CREATE INDEXES (deferred until after all data is loaded)

print("\n\n" + "=" * 70)
print("  CREATING INDEXES")
print("=" * 70)

with engine.connect() as conn:
    for statement in schema_sql.split(";"):
        stmt = statement.strip()
        if stmt and "CREATE INDEX" in stmt.upper():
            conn.execute(text(stmt))
    conn.commit()

print("  ✔ All indexes created successfully")


# 5. ROW COUNT VERIFICATION

print("\n\n" + "=" * 70)
print("  ROW COUNT VERIFICATION")
print("=" * 70)

source_counts = {
    "dim_fund":                len(fm),
    "dim_date":                len(dim_date),
    "fact_nav":                len(nav),
    "fact_transactions":       len(txn),
    "fact_performance":        len(perf),
    "fact_aum":                len(aum),
    "fact_sip_inflows":        len(sip),
    "fact_category_inflows":   len(cat),
    "fact_folio_count":        len(folio),
    "fact_portfolio_holdings": len(hold),
    "fact_benchmark_indices":  len(bench),
}

all_match = True
with engine.connect() as conn:
    for table_name, expected in source_counts.items():
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        actual = result.scalar()
        status = "✅" if actual == expected else "❌"
        if actual != expected:
            all_match = False
        print(f"  {status} {table_name:30s}  Source: {expected:>8,}  DB: {actual:>8,}")

print(f"\n  {'✅ ALL ROW COUNTS MATCH' if all_match else '❌ MISMATCH DETECTED'}")

# Print DB file size
db_size = DB_PATH.stat().st_size
print(f"\n  📦 Database file: {DB_PATH}")
print(f"  📦 Database size: {db_size / (1024*1024):.2f} MB")

print(f"\n{'=' * 70}")
print("  DATABASE LOADING COMPLETE ✅")
print(f"{'=' * 70}\n")
