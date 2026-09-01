"""
fetch_oil_prices.py
-------------------
Fetches Brent Crude Oil spot prices from EIA API v2.
Derives Singapore VLSFO bunker price using a market-standard spread multiplier.

EIA Series used:
  - PET.RBRTE.D  → Brent Crude spot price (USD/barrel), daily

VLSFO derivation:
  VLSFO (USD/MT) ≈ Brent (USD/bbl) × 7.11 (barrels per MT for heavy fuel oil)
  with a refining/blending margin premium of ~12% to reflect 0.5%S bunker market.

Output: data/raw/oil/bunker_vlsfo_brent_daily.csv
"""

import os
import sys
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

EIA_API_KEY = os.getenv("EIA_API_KEY")
START_DATE = "2020-01-01"
END_DATE = "2026-09-01"
OUTPUT_PATH = "data/raw/oil/bunker_vlsfo_brent_daily.csv"

# Barrels per metric tonne for heavy fuel oil (industry standard: 6.35 bbl/MT for HFO 380)
# VLSFO is lighter — use ~7.11 bbl/MT with 12% refining margin premium
BBL_PER_MT_VLSFO = 7.11
VLSFO_PREMIUM_FACTOR = 1.12


def fetch_eia_series(series_id: str, api_key: str) -> pd.Series:
    """Fetch a daily EIA time-series via EIA API v2."""
    url = "https://api.eia.gov/v2/seriesid/{series_id}"
    url = f"https://api.eia.gov/v2/seriesid/{series_id}"
    params = {
        "api_key": api_key,
        "frequency": "daily",
        "data[0]": "value",
        "start": START_DATE,
        "end": END_DATE,
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
        "offset": 0,
        "length": 5000
    }

    all_data = []
    offset = 0
    while True:
        params["offset"] = offset
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  [ERROR] EIA request failed for {series_id}: {e}")
            return pd.Series(dtype=float)

        payload = resp.json()
        records = payload.get("response", {}).get("data", [])
        if not records:
            break
        all_data.extend(records)
        total = payload.get("response", {}).get("total", 0)
        offset += len(records)
        if offset >= total:
            break

    if not all_data:
        print(f"  [WARN] No data returned for EIA series {series_id}")
        return pd.Series(dtype=float)

    df = pd.DataFrame(all_data)
    df["period"] = pd.to_datetime(df["period"])
    df = df.set_index("period").sort_index()
    series = pd.to_numeric(df["value"], errors="coerce")
    series.name = series_id
    print(f"  [OK] EIA {series_id}: {len(series)} records ({series.index[0].date()} -> {series.index[-1].date()})")
    return series


def main():
    if not EIA_API_KEY:
        print("[FATAL] EIA_API_KEY not found in environment. Check your .env file.")
        sys.exit(1)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    print("=" * 60)
    print("Fetching Oil & Fuel Prices from EIA API v2")
    print("=" * 60)

    # Fetch Brent Crude daily spot price
    brent = fetch_eia_series("PET.RBRTE.D", EIA_API_KEY)

    if brent.empty:
        print("[FATAL] Could not fetch Brent crude. Check API key and quota.")
        sys.exit(1)

    # Build full date range and reindex (markets are closed on weekends/holidays)
    date_range = pd.date_range(start=START_DATE, end=END_DATE, freq="D")
    brent = brent.reindex(date_range)

    # Forward-fill weekends/holidays (standard practice for commodity pricing)
    brent_filled = brent.ffill().bfill()

    # Derive VLSFO from Brent: convert USD/bbl → USD/MT and apply 0.5%S premium
    vlsfo = (brent_filled * BBL_PER_MT_VLSFO * VLSFO_PREMIUM_FACTOR).round(2)

    # Build output DataFrame
    out = pd.DataFrame({
        "date": date_range.strftime("%Y-%m-%d"),
        "vlsfo_singapore_usd_t": vlsfo.values,
        "brent_crude_usd_bbl": brent_filled.round(2).values,
        "unit_vlsfo": "USD/MT",
        "unit_brent": "USD/bbl"
    })

    # Remove any rows where brent is still NaN (insufficient coverage)
    out = out.dropna(subset=["brent_crude_usd_bbl"])
    out.to_csv(OUTPUT_PATH, index=False)

    print(f"\n[SUCCESS] Saved {len(out)} records to {OUTPUT_PATH}")
    print(out.head(3).to_string(index=False))
    print(f"  Brent range: ${out['brent_crude_usd_bbl'].min():.2f} -> ${out['brent_crude_usd_bbl'].max():.2f}/bbl")
    print(f"  VLSFO range: ${out['vlsfo_singapore_usd_t'].min():.2f} -> ${out['vlsfo_singapore_usd_t'].max():.2f}/MT")


if __name__ == "__main__":
    main()
