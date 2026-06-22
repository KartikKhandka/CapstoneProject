"""
Bluestock Fintech — Day 1: Data Ingestion & Exploration
=========================================================
Loads all 10 CSV datasets from data/raw/, prints schema info
(.shape, .dtypes, .head()), explores fund_master dimensions,
validates AMFI codes across datasets, and outputs a data-quality summary.
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Fix Windows console encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

RAW_DIR = Path("dataset")

DATASETS = {
    "fund_master":           "01_fund_master.csv",
    "nav_history":           "02_nav_history.csv",
    "aum_by_fund_house":     "03_aum_by_fund_house.csv",
    "monthly_sip_inflows":   "04_monthly_sip_inflows.csv",
    "category_inflows":      "05_category_inflows.csv",
    "industry_folio_count":  "06_industry_folio_count.csv",
    "scheme_performance":    "07_scheme_performance.csv",
    "investor_transactions": "08_investor_transactions.csv",
    "portfolio_holdings":    "09_portfolio_holdings.csv",
    "benchmark_indices":     "10_benchmark_indices.csv",
}


# LOAD ALL DATASETS

print("=" * 80)
print("  BLUESTOCK FINTECH — DATA INGESTION REPORT")
print("=" * 80)

dataframes = {}

for name, filename in DATASETS.items():
    filepath = RAW_DIR / filename
    print(f"\n{'─' * 70}")
    print(f"📂  Loading: {filename}")
    print(f"{'─' * 70}")

    df = pd.read_csv(filepath)
    dataframes[name] = df

    # Shape
    print(f"   Shape : {df.shape[0]:,} rows × {df.shape[1]} columns")

    # Dtypes
    print(f"\n   Data Types:")
    for col, dtype in df.dtypes.items():
        null_count = df[col].isnull().sum()
        null_pct = null_count / len(df) * 100 if len(df) > 0 else 0
        null_info = f"  ⚠ {null_count:,} nulls ({null_pct:.1f}%)" if null_count > 0 else ""
        print(f"      {col:<35} {str(dtype):<15}{null_info}")

    # Head
    print(f"\n   First 3 rows:")
    print(df.head(3).to_string(index=False, max_colwidth=40))


# 3. ANOMALY DETECTION

print(f"\n\n{'=' * 80}")
print("  ANOMALY SCAN")
print("=" * 80)

anomalies = []

for name, df in dataframes.items():
    null_cols = df.columns[df.isnull().any()].tolist()
    if null_cols:
        for col in null_cols:
            n = df[col].isnull().sum()
            anomalies.append(f"[{name}] Column '{col}' has {n:,} missing values ({n/len(df)*100:.1f}%)")

for name, df in dataframes.items():
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        anomalies.append(f"[{name}] {dup_count:,} duplicate rows detected")

#NAV history — check for negative NAVs
nav = dataframes["nav_history"]
neg_nav = (nav["nav"] < 0).sum()
if neg_nav > 0:
    anomalies.append(f"[nav_history] {neg_nav:,} negative NAV values found")

#SIP inflows — check for the Apr-2025 spike in new_sip_accounts
sip = dataframes["monthly_sip_inflows"]
if "new_sip_accounts_lakh" in sip.columns:
    median_new_sip = sip["new_sip_accounts_lakh"].median()
    max_new_sip = sip["new_sip_accounts_lakh"].max()
    if max_new_sip > median_new_sip * 3:
        spike_row = sip.loc[sip["new_sip_accounts_lakh"] == max_new_sip]
        anomalies.append(
            f"[monthly_sip_inflows] Anomalous spike in 'new_sip_accounts_lakh': "
            f"{max_new_sip} (median: {median_new_sip:.1f}) at month "
            f"{spike_row['month'].values[0]}"
        )

#Investor transactions — check for future dates
txn = dataframes["investor_transactions"]
txn_dates = pd.to_datetime(txn["transaction_date"], errors="coerce")
future_dates = (txn_dates > pd.Timestamp.today()).sum()
if future_dates > 0:
    anomalies.append(f"[investor_transactions] {future_dates:,} transactions have future dates")

#Portfolio weights should sum to ~100%
holdings = dataframes["portfolio_holdings"]
weight_sums = holdings.groupby("amfi_code")["weight_pct"].sum()
bad_weights = weight_sums[(weight_sums < 95) | (weight_sums > 105)]
if len(bad_weights) > 0:
    anomalies.append(
        f"[portfolio_holdings] {len(bad_weights)} schemes have portfolio weights "
        f"summing outside 95-105% range"
    )

if anomalies:
    for i, a in enumerate(anomalies, 1):
        print(f"  ⚠ {i}. {a}")
else:
    print("  ✅ No anomalies detected")


# 4. FUND MASTER EXPLORATION

print(f"\n\n{'=' * 80}")
print("  FUND MASTER EXPLORATION")
print("=" * 80)

fm = dataframes["fund_master"]

print(f"\n  📊 Total schemes: {len(fm)}")
print(f"\n  🏢 Unique Fund Houses ({fm['fund_house'].nunique()}):")
for fh in sorted(fm["fund_house"].unique()):
    count = (fm["fund_house"] == fh).sum()
    print(f"      • {fh:<35} ({count} schemes)")

print(f"\n  📁 Unique Categories ({fm['category'].nunique()}):")
for cat in sorted(fm["category"].unique()):
    count = (fm["category"] == cat).sum()
    print(f"      • {cat:<25} ({count} schemes)")

print(f"\n  📂 Unique Sub-Categories ({fm['sub_category'].nunique()}):")
for sub in sorted(fm["sub_category"].unique()):
    count = (fm["sub_category"] == sub).sum()
    print(f"      • {sub:<25} ({count} schemes)")

print(f"\n  ⚠️  Risk Grades ({fm['risk_category'].nunique()}):")
for risk in sorted(fm["risk_category"].unique()):
    count = (fm["risk_category"] == risk).sum()
    print(f"      • {risk:<20} ({count} schemes)")

# AMFI scheme code structure analysis
print(f"\n  🔢 AMFI Code Structure:")
codes = fm["amfi_code"]
print(f"      Range      : {codes.min()} — {codes.max()}")
print(f"      Digits     : {codes.astype(str).str.len().unique().tolist()}")
print(f"      Unique     : {codes.nunique()} codes (out of {len(codes)} rows)")


if "sebi_category_code" in fm.columns:
    print(f"\n  🏛  SEBI Category Codes ({fm['sebi_category_code'].nunique()}):")
    for code in sorted(fm["sebi_category_code"].unique()):
        matching = fm[fm["sebi_category_code"] == code]["sub_category"].unique()
        print(f"      • {code:<8} → {', '.join(matching)}")


# 5. AMFI CODE VALIDATION

print(f"\n\n{'=' * 80}")
print("  AMFI CODE CROSS-VALIDATION")
print("=" * 80)

fm_codes = set(fm["amfi_code"].unique())
nav_codes = set(nav["amfi_code"].unique())

# Fund master codes present in nav_history
fm_in_nav = fm_codes & nav_codes
fm_not_in_nav = fm_codes - nav_codes
nav_not_in_fm = nav_codes - fm_codes

print(f"\n  Fund Master codes     : {len(fm_codes)}")
print(f"  NAV History codes     : {len(nav_codes)}")
print(f"  Match (FM ∩ NAV)      : {len(fm_in_nav)}")
print(f"  FM only (not in NAV)  : {len(fm_not_in_nav)}")
if fm_not_in_nav:
    for code in sorted(fm_not_in_nav):
        scheme = fm[fm["amfi_code"] == code]["scheme_name"].values[0]
        print(f"      ❌ {code} — {scheme}")
print(f"  NAV only (not in FM)  : {len(nav_not_in_fm)}")
if nav_not_in_fm:
    for code in sorted(nav_not_in_fm):
        print(f"      ❌ {code}")

# Cross-validate with other AMFI-keyed datasets
amfi_keyed = {
    "scheme_performance":    dataframes["scheme_performance"],
    "investor_transactions": dataframes["investor_transactions"],
    "portfolio_holdings":    dataframes["portfolio_holdings"],
}

for ds_name, ds_df in amfi_keyed.items():
    ds_codes = set(ds_df["amfi_code"].unique())
    only_in_ds = ds_codes - fm_codes
    only_in_fm = fm_codes - ds_codes
    print(f"\n  vs {ds_name}:")
    print(f"      Common  : {len(ds_codes & fm_codes)}")
    print(f"      Only FM : {len(only_in_fm)}")
    print(f"      Only {ds_name[:15]:<15}: {len(only_in_ds)}")


# 6. DATA QUALITY SUMMARY

print(f"\n\n{'=' * 80}")
print("  DATA QUALITY SUMMARY")
print("=" * 80)

summary_rows = []
for name, df in dataframes.items():
    summary_rows.append({
        "Dataset": name,
        "Rows": f"{df.shape[0]:,}",
        "Columns": df.shape[1],
        "Nulls": f"{df.isnull().sum().sum():,}",
        "Null%": f"{df.isnull().sum().sum() / (df.shape[0] * df.shape[1]) * 100:.2f}%",
        "Duplicates": df.duplicated().sum(),
        "Memory_KB": f"{df.memory_usage(deep=True).sum() / 1024:.1f}",
    })

summary_df = pd.DataFrame(summary_rows)
print(f"\n{summary_df.to_string(index=False)}")

print(f"\n  ✅ AMFI code integrity: {'PASS — All fund_master codes exist in nav_history' if len(fm_not_in_nav) == 0 else f'FAIL — {len(fm_not_in_nav)} codes missing from nav_history'}")
print(f"  ✅ Total datasets loaded: {len(dataframes)}")
print(f"  ✅ Total records: {sum(df.shape[0] for df in dataframes.values()):,}")
print(f"  {'⚠' if anomalies else '✅'}  Anomalies found: {len(anomalies)}")

print(f"\n{'=' * 80}")
print("  DATA INGESTION COMPLETE ✅")
print(f"{'=' * 80}\n")
