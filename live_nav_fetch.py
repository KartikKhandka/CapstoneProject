"""
Live NAV Fetcher

"""

import requests
import pandas as pd
from pathlib import Path
import time
import sys


sys.stdout.reconfigure(encoding='utf-8', errors='replace')


# CONFIGURATION

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

SCHEMES = {
    125497: "HDFC_Top_100_Direct",
    119551: "SBI_Bluechip",
    120503: "ICICI_Bluechip",
    118632: "Nippon_Large_Cap",
    119092: "Axis_Bluechip",
    120841: "Kotak_Bluechip",
}

API_BASE = "https://api.mfapi.in/mf"



def fetch_nav(scheme_code: int, scheme_name: str) -> pd.DataFrame | None:
    """Fetch NAV history from mfapi.in and return as DataFrame."""
    url = f"{API_BASE}/{scheme_code}"
    print(f"\n  🌐 Fetching: {scheme_name} (code: {scheme_code})")
    print(f"     URL: {url}")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"     ❌ Request failed: {e}")
        return None
    except ValueError as e:
        print(f"     ❌ JSON parse failed: {e}")
        return None

    # Parse metadata
    meta = data.get("meta", {})
    print(f"     Fund House    : {meta.get('fund_house', 'N/A')}")
    print(f"     Scheme Type   : {meta.get('scheme_type', 'N/A')}")
    print(f"     Scheme Category: {meta.get('scheme_category', 'N/A')}")
    print(f"     Scheme Code   : {meta.get('scheme_code', 'N/A')}")
    print(f"     Scheme Name   : {meta.get('scheme_name', 'N/A')}")

    # Parse NAV data
    nav_data = data.get("data", [])
    if not nav_data:
        print("     ⚠ No NAV data returned")
        return None

    df = pd.DataFrame(nav_data)
    df.columns = ["date", "nav"]

    # Clean data
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    df = df.dropna(subset=["date", "nav"])
    df = df.sort_values("date").reset_index(drop=True)

    # Add metadata columns
    df["amfi_code"] = scheme_code
    df["scheme_name"] = meta.get("scheme_name", scheme_name)

    print(f"     ✅ Fetched {len(df):,} NAV records")
    print(f"     Date range: {df['date'].min().strftime('%Y-%m-%d')} → {df['date'].max().strftime('%Y-%m-%d')}")
    print(f"     Latest NAV: ₹{df['nav'].iloc[-1]:.4f}")

    return df



# MAIN

def main():
    print("=" * 70)
    print("  BLUESTOCK — LIVE NAV FETCHER (mfapi.in)")
    print("=" * 70)

    all_navs = []
    success_count = 0
    fail_count = 0

    for code, name in SCHEMES.items():
        df = fetch_nav(code, name)
        if df is not None:
            # Save individual CSV
            out_path = RAW_DIR / f"live_nav_{code}_{name}.csv"
            df.to_csv(out_path, index=False)
            print(f"     💾 Saved: {out_path}")
            all_navs.append(df)
            success_count += 1
        else:
            fail_count += 1

        # Be polite to the API
        time.sleep(1)

    # Save combined file
    if all_navs:
        combined = pd.concat(all_navs, ignore_index=True)
        combined_path = RAW_DIR / "live_nav_all_schemes.csv"
        combined.to_csv(combined_path, index=False)
        print(f"\n  💾 Combined file: {combined_path} ({len(combined):,} total records)")

    # Summary
    print(f"\n{'=' * 70}")
    print(f"  FETCH SUMMARY")
    print(f"{'=' * 70}")
    print(f"  ✅ Successful: {success_count}/{len(SCHEMES)}")
    if fail_count:
        print(f"  ❌ Failed    : {fail_count}/{len(SCHEMES)}")
    print(f"  📁 Output dir : {RAW_DIR.resolve()}")
    print(f"{'=' * 70}\n")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
