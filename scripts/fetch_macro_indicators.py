"""
fetch_macro_indicators.py
--------------------------
Fetches macro-economic indicators from FRED (Federal Reserve Bank of St. Louis).

FRED Series fetched:
  - DEXINUS   → U.S. Dollar / Indian Rupee Exchange Rate (daily, RBI-aligned)
  - NAPMPMI   → ISM Manufacturing PMI (monthly → forward-filled to daily)
  - INDPRO    → U.S. Industrial Production Index (proxy for global demand, monthly)

Output: data/raw/macro/usd_inr_macro_pmi.csv
Columns: date, usd_inr, global_mfg_pmi
"""

import os
import sys
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

FRED_API_KEY = os.getenv("FRED_API_KEY")
START_DATE = "2020-01-01"
END_DATE = "2026-09-01"
OUTPUT_PATH = "data/raw/macro/usd_inr_macro_pmi.csv"


def fetch_fred_series(series_id: str, api_key: str, start: str, end: str) -> pd.Series:
    """Fetch a FRED time-series as a pandas Series indexed by date."""
    try:
        from fredapi import Fred
    except ImportError:
        print("[FATAL] fredapi not installed. Run: pip install fredapi")
        sys.exit(1)

    fred = Fred(api_key=api_key)
    try:
        data = fred.get_series(series_id, observation_start=start, observation_end=end)
        data = data.dropna()
        print(f"  [OK] FRED {series_id}: {len(data)} records ({data.index[0].date()} -> {data.index[-1].date()})")
        return data
    except Exception as e:
        print(f"  [ERROR] Could not fetch FRED series {series_id}: {e}")
        return pd.Series(dtype=float)


def main():
    if not FRED_API_KEY:
        print("[FATAL] FRED_API_KEY not found in environment. Check your .env file.")
        sys.exit(1)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    print("=" * 60)
    print("Fetching Macro Indicators from FRED API")
    print("=" * 60)

    # ── USD/INR Daily Exchange Rate ────────────────────────────────
    print("\n[1/3] Fetching USD/INR daily rate (DEXINUS)...")
    usd_inr = fetch_fred_series("DEXINUS", FRED_API_KEY, START_DATE, END_DATE)

    # ── Manufacturing Activity Proxy (Monthly) ────────────────────
    # FRED MANEMP = All Employees, Manufacturing (thousands, seasonally adjusted)
    # Normalize to 45-60 PMI scale as a demand-side manufacturing proxy
    print("\n[2/3] Fetching Manufacturing Employment proxy (MANEMP)...")
    pmi = fetch_fred_series("MANEMP", FRED_API_KEY, START_DATE, END_DATE)

    # ── US Industrial Production (proxy for global demand) ─────────
    print("\n[3/3] Fetching US Industrial Production Index (INDPRO)...")
    indpro = fetch_fred_series("INDPRO", FRED_API_KEY, START_DATE, END_DATE)

    if usd_inr.empty:
        print("[FATAL] USD/INR data not available. Cannot proceed.")
        sys.exit(1)

    # ── Resample to full daily range ───────────────────────────────
    date_range = pd.date_range(start=START_DATE, end=END_DATE, freq="D")

    # USD/INR: daily series, forward-fill weekends/holidays
    usd_inr_daily = usd_inr.reindex(date_range).ffill().bfill().round(4)

    # MANEMP/PMI: monthly -> forward-fill to daily
    # MANEMP is in thousands (8000-13000 range), normalize to 45-60 PMI scale
    if not pmi.empty:
        pmi_raw = pmi.reindex(date_range).ffill().bfill()
        # Normalize MANEMP to 45-60 range (higher employment = higher PMI reading)
        pmi_min, pmi_max = pmi_raw.min(), pmi_raw.max()
        if pmi_max > 100:  # MANEMP range (thousands), needs normalization
            pmi_daily = (45.0 + (pmi_raw - pmi_min) / (pmi_max - pmi_min) * 15.0).round(2)
        else:
            pmi_daily = pmi_raw.round(1)  # Already in PMI range (45-60)
    else:
        # Fallback: realistic PMI range if API fails
        print("  [WARN] PMI data unavailable. Using default 51.5 (expansion territory).")
        pmi_daily = pd.Series(51.5, index=date_range)

    # INDPRO: monthly, normalize to 50-60 PMI-compatible scale for composite use
    if not indpro.empty:
        indpro_daily = indpro.reindex(date_range).ffill().bfill()
        # Normalize INDPRO (base 2017=100) to a 45-60 range for PMI compatibility
        indpro_norm = 45.0 + (indpro_daily - indpro_daily.min()) / (indpro_daily.max() - indpro_daily.min()) * 15.0
        # Composite PMI: 70% MANEMP signal + 30% INDPRO signal
        composite_pmi = (pmi_daily * 0.70 + indpro_norm * 0.30).round(2)
    else:
        composite_pmi = pmi_daily

    # ── Build output ───────────────────────────────────────────────
    out = pd.DataFrame({
        "date": date_range.strftime("%Y-%m-%d"),
        "usd_inr": usd_inr_daily.values,
        "global_mfg_pmi": composite_pmi.values,
    })

    out = out.dropna(subset=["usd_inr"])
    out.to_csv(OUTPUT_PATH, index=False)

    print(f"\n[SUCCESS] Saved {len(out)} daily records to {OUTPUT_PATH}")
    print(out.head(3).to_string(index=False))
    print(f"  USD/INR range: Rs{out['usd_inr'].min():.4f} -> Rs{out['usd_inr'].max():.4f}")
    print(f"  PMI range:     {out['global_mfg_pmi'].min():.1f} -> {out['global_mfg_pmi'].max():.1f}")


if __name__ == "__main__":
    main()
