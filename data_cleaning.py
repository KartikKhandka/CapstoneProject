"""
Data Cleaning Pipeline

"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

RAW_DIR = Path("dataset")
OUT_DIR = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Cleaning report collector
report = []


def log(dataset: str, action: str, detail: str = ""):
    """Append to the cleaning report."""
    msg = f"[{dataset}] {action}"
    if detail:
        msg += f" — {detail}"
    report.append(msg)
    print(f"{msg}")


# 1. FUND MASTER

print("\n" + "=" * 70)
print("  Cleaning: 01_fund_master.csv")
print("=" * 70)

fm = pd.read_csv(RAW_DIR / "01_fund_master.csv")
original_len = len(fm)

# Parse launch_date
fm["launch_date"] = pd.to_datetime(fm["launch_date"], errors="coerce")
log("fund_master", "Parsed launch_date to datetime")

# Strip whitespace from string columns
str_cols = fm.select_dtypes(include="object").columns
fm[str_cols] = fm[str_cols].apply(lambda c: c.str.strip())
log("fund_master", "Stripped whitespace from string columns")

# Remove exact duplicates
dups = fm.duplicated().sum()
fm = fm.drop_duplicates()
log("fund_master", "Removed duplicates", f"{dups} found")

# Validate amfi_code uniqueness
assert fm["amfi_code"].is_unique, "amfi_code is not unique in fund_master!"
log("fund_master", "Validated amfi_code uniqueness", "PASS")

# Validate expense_ratio range
bad_er = fm[(fm["expense_ratio_pct"] < 0) | (fm["expense_ratio_pct"] > 5)]
log("fund_master", "Validated expense_ratio_pct >= 0", f"{len(bad_er)} violations")

fm.to_csv(OUT_DIR / "01_fund_master.csv", index=False)
log("fund_master", "Saved", f"{len(fm)} rows (was {original_len})")



# 2. NAV HISTORY

print("\n" + "=" * 70)
print("  Cleaning: 02_nav_history.csv")
print("=" * 70)

nav = pd.read_csv(RAW_DIR / "02_nav_history.csv")
original_len = len(nav)

# Parse date to datetime
nav["date"] = pd.to_datetime(nav["date"], errors="coerce")
log("nav_history", "Parsed date to datetime")

# Remove rows with invalid dates
bad_dates = nav["date"].isna().sum()
nav = nav.dropna(subset=["date"])
log("nav_history", "Dropped rows with invalid dates", f"{bad_dates} dropped")

# Sort by amfi_code + date
nav = nav.sort_values(["amfi_code", "date"]).reset_index(drop=True)
log("nav_history", "Sorted by (amfi_code, date)")

# Remove duplicate (amfi_code, date) pairs — keep first
dup_keys = nav.duplicated(subset=["amfi_code", "date"]).sum()
nav = nav.drop_duplicates(subset=["amfi_code", "date"], keep="first")
log("nav_history", "Removed duplicate (amfi_code, date)", f"{dup_keys} found")

# Validate NAV > 0
bad_nav = (nav["nav"] <= 0).sum()
nav = nav[nav["nav"] > 0]
log("nav_history", "Validated nav > 0", f"{bad_nav} violations removed")

# Forward-fill missing NAV for weekends/holidays
# Reindex each fund to a full calendar date range
date_min = nav["date"].min()
date_max = nav["date"].max()
full_dates = pd.date_range(date_min, date_max, freq="D")

filled_frames = []
for amfi_code, group in nav.groupby("amfi_code"):
    group = group.set_index("date").reindex(full_dates)
    group["amfi_code"] = amfi_code
    group["nav"] = group["nav"].ffill()
    group.index.name = "date"
    group = group.reset_index()
    filled_frames.append(group)

nav_filled = pd.concat(filled_frames, ignore_index=True)
nav_filled["amfi_code"] = nav_filled["amfi_code"].astype(int)

added_rows = len(nav_filled) - len(nav)
log("nav_history", "Forward-filled NAV for weekends/holidays", f"{added_rows} rows added")

# Final sort
nav_filled = nav_filled.sort_values(["amfi_code", "date"]).reset_index(drop=True)

nav_filled.to_csv(OUT_DIR / "02_nav_history.csv", index=False)
log("nav_history", "Saved", f"{len(nav_filled)} rows (was {original_len})")


# 3. AUM BY FUND HOUSE

print("\n" + "=" * 70)
print("  Cleaning: 03_aum_by_fund_house.csv")
print("=" * 70)

aum = pd.read_csv(RAW_DIR / "03_aum_by_fund_house.csv")
original_len = len(aum)

# Parse date
aum["date"] = pd.to_datetime(aum["date"], errors="coerce")
log("aum_by_fund_house", "Parsed date to datetime")

# Strip strings
str_cols = aum.select_dtypes(include="object").columns
aum[str_cols] = aum[str_cols].apply(lambda c: c.str.strip())

# Remove duplicates
dups = aum.duplicated().sum()
aum = aum.drop_duplicates()
log("aum_by_fund_house", "Removed duplicates", f"{dups} found")

# Validate AUM > 0
bad_aum = (aum["aum_crore"] <= 0).sum()
log("aum_by_fund_house", "Validated aum_crore > 0", f"{bad_aum} violations")

# Sort
aum = aum.sort_values(["fund_house", "date"]).reset_index(drop=True)

aum.to_csv(OUT_DIR / "03_aum_by_fund_house.csv", index=False)
log("aum_by_fund_house", "Saved", f"{len(aum)} rows (was {original_len})")


# 4. MONTHLY SIP INFLOWS

print("\n" + "=" * 70)
print("  Cleaning: 04_monthly_sip_inflows.csv")
print("=" * 70)

sip = pd.read_csv(RAW_DIR / "04_monthly_sip_inflows.csv")
original_len = len(sip)

# Parse month
sip["month"] = pd.to_datetime(sip["month"], errors="coerce")
log("monthly_sip_inflows", "Parsed month to datetime")

# Remove duplicates
dups = sip.duplicated().sum()
sip = sip.drop_duplicates()
log("monthly_sip_inflows", "Removed duplicates", f"{dups} found")

# Validate inflows > 0
bad = (sip["sip_inflow_crore"] <= 0).sum()
log("monthly_sip_inflows", "Validated sip_inflow_crore > 0", f"{bad} violations")

# Sort
sip = sip.sort_values("month").reset_index(drop=True)

sip.to_csv(OUT_DIR / "04_monthly_sip_inflows.csv", index=False)
log("monthly_sip_inflows", "Saved", f"{len(sip)} rows (was {original_len})")


# 5. CATEGORY INFLOWS

print("\n" + "=" * 70)
print("  Cleaning: 05_category_inflows.csv")
print("=" * 70)

cat = pd.read_csv(RAW_DIR / "05_category_inflows.csv")
original_len = len(cat)

cat["month"] = pd.to_datetime(cat["month"], errors="coerce")
log("category_inflows", "Parsed month to datetime")

str_cols = cat.select_dtypes(include="object").columns
cat[str_cols] = cat[str_cols].apply(lambda c: c.str.strip())

dups = cat.duplicated().sum()
cat = cat.drop_duplicates()
log("category_inflows", "Removed duplicates", f"{dups} found")

cat = cat.sort_values(["category", "month"]).reset_index(drop=True)

cat.to_csv(OUT_DIR / "05_category_inflows.csv", index=False)
log("category_inflows", "Saved", f"{len(cat)} rows (was {original_len})")

# 6. INDUSTRY FOLIO COUNT

print("\n" + "=" * 70)
print("  Cleaning: 06_industry_folio_count.csv")
print("=" * 70)

folio = pd.read_csv(RAW_DIR / "06_industry_folio_count.csv")
original_len = len(folio)

folio["month"] = pd.to_datetime(folio["month"], errors="coerce")
log("industry_folio_count", "Parsed month to datetime")

dups = folio.duplicated().sum()
folio = folio.drop_duplicates()
log("industry_folio_count", "Removed duplicates", f"{dups} found")

# Validate folios > 0
bad = (folio["total_folios_crore"] <= 0).sum()
log("industry_folio_count", "Validated total_folios_crore > 0", f"{bad} violations")

folio = folio.sort_values("month").reset_index(drop=True)

folio.to_csv(OUT_DIR / "06_industry_folio_count.csv", index=False)
log("industry_folio_count", "Saved", f"{len(folio)} rows (was {original_len})")

# 7. SCHEME PERFORMANCE
print("\n" + "=" * 70)
print("  Cleaning: 07_scheme_performance.csv")
print("=" * 70)

perf = pd.read_csv(RAW_DIR / "07_scheme_performance.csv")
original_len = len(perf)

# Strip strings
str_cols = perf.select_dtypes(include="object").columns
perf[str_cols] = perf[str_cols].apply(lambda c: c.str.strip())

# Validate all return columns are numeric
return_cols = ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
               "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio",
               "sortino_ratio", "std_dev_ann_pct", "max_drawdown_pct"]

for col in return_cols:
    perf[col] = pd.to_numeric(perf[col], errors="coerce")
    non_numeric = perf[col].isna().sum()
    if non_numeric > 0:
        log("scheme_performance", f"Non-numeric values in {col}", f"{non_numeric} coerced to NaN")

log("scheme_performance", "Validated all return columns are numeric", "PASS")

# Flag expense_ratio anomalies (outside 0.1% – 2.5%)
er_anomalies = perf[
    (perf["expense_ratio_pct"] < 0.1) | (perf["expense_ratio_pct"] > 2.5)
]
if len(er_anomalies) > 0:
    log("scheme_performance", "⚠ expense_ratio outside 0.1–2.5%",
        f"{len(er_anomalies)} rows flagged")
    for _, row in er_anomalies.iterrows():
        print(f"      ⚠ {row['amfi_code']} ({row['scheme_name'][:40]}): {row['expense_ratio_pct']}%")
else:
    log("scheme_performance", "expense_ratio_pct within 0.1–2.5%", "All PASS")

# Remove duplicates
dups = perf.duplicated().sum()
perf = perf.drop_duplicates()
log("scheme_performance", "Removed duplicates", f"{dups} found")

# Validate morningstar_rating in 1–5
bad_rating = perf[~perf["morningstar_rating"].isin([1, 2, 3, 4, 5])]
log("scheme_performance", "Validated morningstar_rating ∈ {1..5}",
    f"{len(bad_rating)} violations")

perf.to_csv(OUT_DIR / "07_scheme_performance.csv", index=False)
log("scheme_performance", "Saved", f"{len(perf)} rows (was {original_len})")


# 8. INVESTOR TRANSACTIONS

print("\n" + "=" * 70)
print("  Cleaning: 08_investor_transactions.csv")
print("=" * 70)

txn = pd.read_csv(RAW_DIR / "08_investor_transactions.csv")
original_len = len(txn)

# Parse transaction_date
txn["transaction_date"] = pd.to_datetime(txn["transaction_date"], errors="coerce")
log("investor_transactions", "Parsed transaction_date to datetime")

# Drop rows with invalid dates
bad_dates = txn["transaction_date"].isna().sum()
txn = txn.dropna(subset=["transaction_date"])
log("investor_transactions", "Dropped invalid dates", f"{bad_dates} dropped")

# Standardise transaction_type to title-case enum
valid_types = {"SIP": "SIP", "sip": "SIP",
               "Lumpsum": "Lumpsum", "lumpsum": "Lumpsum", "LUMPSUM": "Lumpsum",
               "Redemption": "Redemption", "redemption": "Redemption", "REDEMPTION": "Redemption"}
# General approach: title-case then map known variants
txn["transaction_type"] = txn["transaction_type"].str.strip()
txn["transaction_type"] = txn["transaction_type"].map(
    lambda x: valid_types.get(x, x.title() if isinstance(x, str) else x)
)
allowed_types = {"SIP", "Lumpsum", "Redemption"}
bad_types = txn[~txn["transaction_type"].isin(allowed_types)]
if len(bad_types) > 0:
    log("investor_transactions", "⚠ Non-standard transaction_type values",
        f"{len(bad_types)} rows — values: {bad_types['transaction_type'].unique()}")
else:
    log("investor_transactions", "Standardised transaction_type", "All ∈ {SIP, Lumpsum, Redemption}")

# Validate amount > 0
bad_amt = (txn["amount_inr"] <= 0).sum()
txn = txn[txn["amount_inr"] > 0]
log("investor_transactions", "Validated amount_inr > 0", f"{bad_amt} violations removed")

# Validate kyc_status enum
allowed_kyc = {"Verified", "Pending"}
txn["kyc_status"] = txn["kyc_status"].str.strip()
bad_kyc = txn[~txn["kyc_status"].isin(allowed_kyc)]
if len(bad_kyc) > 0:
    log("investor_transactions", "⚠ Non-standard kyc_status",
        f"{len(bad_kyc)} rows — values: {bad_kyc['kyc_status'].unique()}")
else:
    log("investor_transactions", "Validated kyc_status ∈ {Verified, Pending}", "All PASS")

# Strip string columns
str_cols = txn.select_dtypes(include="object").columns
txn[str_cols] = txn[str_cols].apply(lambda c: c.str.strip())

# Remove exact duplicates
dups = txn.duplicated().sum()
txn = txn.drop_duplicates()
log("investor_transactions", "Removed duplicates", f"{dups} found")

# Sort
txn = txn.sort_values(["transaction_date", "investor_id"]).reset_index(drop=True)

txn.to_csv(OUT_DIR / "08_investor_transactions.csv", index=False)
log("investor_transactions", "Saved", f"{len(txn)} rows (was {original_len})")

# 9. PORTFOLIO HOLDINGS

print("\n" + "=" * 70)
print("  Cleaning: 09_portfolio_holdings.csv")
print("=" * 70)

hold = pd.read_csv(RAW_DIR / "09_portfolio_holdings.csv")
original_len = len(hold)

# Parse portfolio_date
hold["portfolio_date"] = pd.to_datetime(hold["portfolio_date"], errors="coerce")
log("portfolio_holdings", "Parsed portfolio_date to datetime")

# Strip strings
str_cols = hold.select_dtypes(include="object").columns
hold[str_cols] = hold[str_cols].apply(lambda c: c.str.strip())

# Remove duplicates
dups = hold.duplicated().sum()
hold = hold.drop_duplicates()
log("portfolio_holdings", "Removed duplicates", f"{dups} found")

# Validate weight_pct > 0
bad_w = (hold["weight_pct"] <= 0).sum()
log("portfolio_holdings", "Validated weight_pct > 0", f"{bad_w} violations")

# Validate portfolio weights sum to ~100% per fund
weight_sums = hold.groupby("amfi_code")["weight_pct"].sum()
bad_sums = weight_sums[(weight_sums < 95) | (weight_sums > 105)]
if len(bad_sums) > 0:
    log("portfolio_holdings", "⚠ Weight sums outside 95–105%", f"{len(bad_sums)} funds")
else:
    log("portfolio_holdings", "Weight sums within 95–105%", "All PASS")

hold = hold.sort_values(["amfi_code", "weight_pct"], ascending=[True, False]).reset_index(drop=True)

hold.to_csv(OUT_DIR / "09_portfolio_holdings.csv", index=False)
log("portfolio_holdings", "Saved", f"{len(hold)} rows (was {original_len})")

# 10. BENCHMARK INDICES

print("\n" + "=" * 70)
print("  Cleaning: 10_benchmark_indices.csv")
print("=" * 70)

bench = pd.read_csv(RAW_DIR / "10_benchmark_indices.csv")
original_len = len(bench)

# Parse date
bench["date"] = pd.to_datetime(bench["date"], errors="coerce")
log("benchmark_indices", "Parsed date to datetime")

# Strip strings
str_cols = bench.select_dtypes(include="object").columns
bench[str_cols] = bench[str_cols].apply(lambda c: c.str.strip())

# Remove duplicates
dups = bench.duplicated().sum()
bench = bench.drop_duplicates()
log("benchmark_indices", "Removed duplicates", f"{dups} found")

# Validate close_value > 0
bad_val = (bench["close_value"] <= 0).sum()
log("benchmark_indices", "Validated close_value > 0", f"{bad_val} violations")

# Sort
bench = bench.sort_values(["index_name", "date"]).reset_index(drop=True)

bench.to_csv(OUT_DIR / "10_benchmark_indices.csv", index=False)
log("benchmark_indices", "Saved", f"{len(bench)} rows (was {original_len})")


# CLEANING REPORT SUMMARY

print("\n\n" + "=" * 70)
print("  DATA CLEANING — SUMMARY REPORT")
print("=" * 70)

# Count output files
output_files = list(OUT_DIR.glob("*.csv"))
print(f"\n  Output directory: {OUT_DIR}")
print(f" Files created: {len(output_files)}")

for f in sorted(output_files):
    df_check = pd.read_csv(f)
    print(f"      ✔ {f.name:40s} {df_check.shape[0]:>8,} rows × {df_check.shape[1]} cols")

print(f"\n  Cleaning actions performed: {len(report)}")
for r in report:
    pass  # Already printed above

print(f"\n{'=' * 70}")
print("  DATA CLEANING COMPLETE ✅")
print(f"{'=' * 70}\n")
