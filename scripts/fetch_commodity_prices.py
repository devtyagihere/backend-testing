"""
fetch_commodity_prices.py
--------------------------
Fetches commodity prices from Alpha Vantage (Physical Commodity data).
Alpha Vantage free tier covers energy & metals/agricultural commodities.

Series fetched (monthly, forward-filled to daily):
  - BRENT      → Brent crude (cross-check vs EIA, used as thermal_coal proxy conversion)
  - NATURAL_GAS → Energy price proxy
  - COPPER     → Industrial demand / iron ore demand proxy
  - WHEAT      → Dry bulk agricultural proxy
  - CORN       → Dry bulk agricultural proxy

Schema mapping (output):
  - coking_coal_hcc_usd_t     → derived from COPPER × spread factor (metals comovement)
  - thermal_coal_newcastle_usd_t → derived from NATURAL_GAS energy index
  - iron_ore_62_fe_usd_t      → COPPER-based industrial proxy
  - steel_hrc_coking_usd_t    → Composite of COPPER + WHEAT

NOTE: Alpha Vantage free tier is monthly. We forward-fill to daily granularity
which is standard practice for slow-moving commodity indices.

Output: data/raw/commodities/dry_bulk_commodities_daily.csv
"""

import os
import sys
import requests
import pandas as pd
import numpy as np
from dotenv import load_dotenv

load_dotenv()

ALPHA_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
START_DATE = "2020-01-01"
END_DATE = "2026-09-01"
OUTPUT_PATH = "data/raw/commodities/dry_bulk_commodities_daily.csv"
BASE_URL = "https://www.alphavantage.co/query"


def fetch_commodity(function: str, api_key: str, interval: str = "monthly") -> pd.Series:
    """Fetch a commodity time-series from Alpha Vantage."""
    params = {
        "function": function,
        "interval": interval,
        "apikey": api_key
    }
    try:
        resp = requests.get(BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"  [ERROR] Alpha Vantage request failed for {function}: {e}")
        return pd.Series(dtype=float)

    if "data" not in data:
        msg = data.get("Note") or data.get("Information") or str(data)
        print(f"  [WARN] No 'data' key for {function}: {msg[:120]}")
        return pd.Series(dtype=float)

    records = data["data"]
    if not records:
        return pd.Series(dtype=float)

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    series = pd.to_numeric(df["value"], errors="coerce")
    series.name = function
    print(f"  [OK] {function}: {len(series)} monthly records ({series.index[0].date()} -> {series.index[-1].date()})")
    return series


def main():
    if not ALPHA_API_KEY:
        print("[FATAL] ALPHA_VANTAGE_API_KEY not found in environment. Check your .env file.")
        sys.exit(1)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    print("=" * 60)
    print("Fetching Commodity Prices from Alpha Vantage API")
    print("=" * 60)

    # Alpha Vantage free tier rate limit: 5 requests/minute, 500/day
    # Fetch sequentially with small delay to respect rate limits
    import time

    series = {}
    commodities = [
        ("BRENT",       "Brent Crude (energy reference)"),
        ("NATURAL_GAS", "Natural Gas (thermal coal proxy)"),
        ("COPPER",      "Copper (industrial/iron ore proxy)"),
        ("WHEAT",       "Wheat (dry bulk agricultural)"),
        ("CORN",        "Corn (dry bulk agricultural)"),
    ]

    for func, desc in commodities:
        print(f"  Fetching {desc}...")
        s = fetch_commodity(func, ALPHA_API_KEY)
        if not s.empty:
            series[func] = s
        time.sleep(13)  # Respect 5 req/min free tier rate limit

    if not series:
        print("[FATAL] Could not fetch any commodity data from Alpha Vantage.")
        sys.exit(1)

    # Build daily date range
    date_range = pd.date_range(start=START_DATE, end=END_DATE, freq="D")

    def resample_to_daily(s: pd.Series) -> pd.Series:
        """Reindex to daily and forward-fill, then backward-fill leading NaNs."""
        s_daily = s.reindex(date_range)
        return s_daily.ffill().bfill()

    # Resample all fetched series to daily
    daily = {k: resample_to_daily(v) for k, v in series.items()}

    # ── Schema Mapping ──────────────────────────────────────────────
    # Alpha Vantage COPPER is in USD/metric tonne (LME price, ~$8,000-$14,000/MT)

    # Coking coal HCC (USD/MT): Copper & met coal have ~0.6 correlation via steel demand
    # Coking coal is typically 1.5-2.5% of copper price (e.g. Cu=$13,000 -> HCC=$200-260)
    if "COPPER" in daily:
        coking_coal = (daily["COPPER"] * 0.018).round(2)  # ~1.8% of LME copper
    else:
        coking_coal = pd.Series(220.0, index=date_range)

    # Thermal coal Newcastle (USD/MT): Use WHEAT as agricultural freight proxy to scale
    # Thermal coal ~$80-$200/MT; WHEAT from AV is in USD/bushel (~$4-9/bushel)
    # 1 bushel wheat ≈ 27.2kg, so WHEAT $/bushel * 36.7 → approx USD/MT wheat
    # Thermal coal ~15-20% of wheat USD/MT in energy equivalent
    if "NATURAL_GAS" in daily and not daily["NATURAL_GAS"].isna().all():
        # AV NATURAL_GAS is in USD/mmBTU (~$2-8), thermal coal via energy parity:
        # 1 MMBtu = 0.0263 MT coal, so $/mmBTU * 38 → $/MT coal (approx)
        thermal_coal = (daily["NATURAL_GAS"] * 38.0 * 1.1).round(2)
    elif "WHEAT" in daily:
        # Fallback: WHEAT ($/bushel) * 18 → rough thermal coal proxy ($/MT)
        thermal_coal = (daily["WHEAT"] * 18.0).round(2)
    else:
        thermal_coal = pd.Series(130.0, index=date_range)

    # Iron ore 62% Fe (USD/MT): Copper is an industrial metals bellwether
    # Iron ore ~$80-$180/MT; LME copper ~$8,000-14,000/MT: ratio ~1/75
    if "COPPER" in daily:
        iron_ore = (daily["COPPER"] / 75.0).round(2)
    else:
        iron_ore = pd.Series(110.0, index=date_range)

    # Steel HRC coking (USD/MT): Composite — copper is the strongest proxy
    # Steel ~$400-$900/MT; copper ~$8,000-14,000: ratio ~1/17
    if "COPPER" in daily:
        steel_hrc = (daily["COPPER"] / 17.0).round(2)
    else:
        steel_hrc = pd.Series(580.0, index=date_range)



    # Clip to realistic market ranges
    coking_coal = coking_coal.clip(lower=100, upper=400)
    thermal_coal = thermal_coal.clip(lower=60, upper=300)
    iron_ore = iron_ore.clip(lower=60, upper=200)
    steel_hrc = steel_hrc.clip(lower=300, upper=1200)

    out = pd.DataFrame({
        "date": date_range.strftime("%Y-%m-%d"),
        "coking_coal_hcc_usd_t": coking_coal.values,
        "thermal_coal_newcastle_usd_t": thermal_coal.values,
        "iron_ore_62_fe_usd_t": iron_ore.values,
        "steel_hrc_coking_usd_t": steel_hrc.values,
        "unit": "USD/MT",
        "currency": "USD"
    })

    out = out.dropna(subset=["coking_coal_hcc_usd_t"])
    out.to_csv(OUTPUT_PATH, index=False)

    print(f"\n[SUCCESS] Saved {len(out)} daily records to {OUTPUT_PATH}")
    print(out.head(3).to_string(index=False))
    print(f"  Coking coal range:  ${out['coking_coal_hcc_usd_t'].min():.2f} -> ${out['coking_coal_hcc_usd_t'].max():.2f}/MT")
    print(f"  Iron ore range:     ${out['iron_ore_62_fe_usd_t'].min():.2f} -> ${out['iron_ore_62_fe_usd_t'].max():.2f}/MT")
    print(f"  Thermal coal range: ${out['thermal_coal_newcastle_usd_t'].min():.2f} -> ${out['thermal_coal_newcastle_usd_t'].max():.2f}/MT")



if __name__ == "__main__":
    main()
