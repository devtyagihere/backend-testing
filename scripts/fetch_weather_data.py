"""
fetch_weather_data.py
----------------------
Fetches historical weather data for Indian East Coast port coordinates
using the Open-Meteo Archive API (free, no API key required).

Ports and their coordinates:
  - Paradip (primary SAIL import port): lat=20.3167, lon=86.6167
  - Visakhapatnam (Vizag):              lat=17.6868, lon=83.2185
  - Haldia:                             lat=22.0257, lon=88.1050

Open-Meteo Archive API endpoint:
  https://archive-api.open-meteo.com/v1/archive

Variables fetched (daily):
  - windspeed_10m_max       → max daily wind speed (km/h)
  - precipitation_sum       → total daily rainfall (mm)
  - weathercode             → WMO weather code (storm, cyclone indicators)

Marine / Wave Data (Open-Meteo Marine API):
  https://marine-api.open-meteo.com/v1/marine
  - wave_height_max         → significant wave height (meters)
  - swell_wave_height_max   → swell height (meters)

Derived columns:
  - bay_of_bengal_wave_height_m → wave_height_max at Paradip offshore
  - monsoon_active_flag         → 1 if precipitation > 10mm OR month in [6,7,8,9]
  - cyclone_disruption_index    → 0.0-1.0 score based on windspeed extremes

Output: data/raw/weather/bay_of_bengal_weather_signals.csv
"""

import os
import sys
import requests
import pandas as pd
import numpy as np

START_DATE = "2020-01-01"
END_DATE = "2026-08-31"
OUTPUT_PATH = "data/raw/weather/bay_of_bengal_weather_signals.csv"

# Paradip port coordinates (primary SAIL East Coast import hub)
PARADIP_LAT = 20.3167
PARADIP_LON = 86.6167


def fetch_open_meteo_archive(lat: float, lon: float, variables: list, start: str, end: str) -> pd.DataFrame:
    """Fetch daily historical weather from Open-Meteo Archive API."""
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "daily": ",".join(variables),
        "timezone": "Asia/Kolkata"
    }
    try:
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"  [ERROR] Open-Meteo Archive request failed: {e}")
        return pd.DataFrame()

    if "daily" not in data:
        print(f"  [WARN] Unexpected response: {str(data)[:200]}")
        return pd.DataFrame()

    daily = data["daily"]
    df = pd.DataFrame(daily)
    df["time"] = pd.to_datetime(df["time"])
    df = df.set_index("time").sort_index()
    n = len(df)
    print(f"  [OK] Open-Meteo Archive: {n} daily records from {df.index[0].date()} -> {df.index[-1].date()}")
    return df


def fetch_open_meteo_marine(lat: float, lon: float, variables: list, start: str, end: str) -> pd.DataFrame:
    """Fetch daily marine / wave data from Open-Meteo Marine API."""
    url = "https://marine-api.open-meteo.com/v1/marine"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "daily": ",".join(variables),
        "timezone": "Asia/Kolkata"
    }
    try:
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"  [ERROR] Open-Meteo Marine request failed: {e}")
        return pd.DataFrame()

    if "daily" not in data:
        print(f"  [WARN] Marine API unexpected response: {str(data)[:200]}")
        return pd.DataFrame()

    daily = data["daily"]
    df = pd.DataFrame(daily)
    df["time"] = pd.to_datetime(df["time"])
    df = df.set_index("time").sort_index()
    n = len(df)
    print(f"  [OK] Open-Meteo Marine: {n} daily records from {df.index[0].date()} -> {df.index[-1].date()}")
    return df


def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    print("=" * 60)
    print("Fetching Weather Data from Open-Meteo Archive API")
    print(f"  Location: Paradip Port ({PARADIP_LAT}°N, {PARADIP_LON}°E)")
    print("=" * 60)

    # ── Fetch atmospheric weather ──────────────────────────────────
    print("\n[1/2] Fetching atmospheric weather (wind, precipitation)...")
    atm_df = fetch_open_meteo_archive(
        lat=PARADIP_LAT,
        lon=PARADIP_LON,
        variables=["windspeed_10m_max", "precipitation_sum", "weathercode"],
        start=START_DATE,
        end=END_DATE
    )

    # ── Fetch marine / wave data ────────────────────────────────────
    print("\n[2/2] Fetching marine wave data...")
    marine_df = fetch_open_meteo_marine(
        lat=PARADIP_LAT,
        lon=PARADIP_LON,
        variables=["wave_height_max", "swell_wave_height_max"],
        start=START_DATE,
        end=END_DATE
    )

    if atm_df.empty and marine_df.empty:
        print("[FATAL] Both weather and marine APIs returned no data.")
        sys.exit(1)

    # ── Build combined daily dataset ────────────────────────────────
    date_range = pd.date_range(start=START_DATE, end=END_DATE, freq="D")

    # Windspeed (km/h), default 0 where missing
    if "windspeed_10m_max" in atm_df.columns:
        wind = atm_df["windspeed_10m_max"].reindex(date_range).ffill().bfill().fillna(15.0)
    else:
        wind = pd.Series(15.0, index=date_range)

    # Precipitation (mm)
    if "precipitation_sum" in atm_df.columns:
        precip = atm_df["precipitation_sum"].reindex(date_range).ffill().bfill().fillna(0.0)
    else:
        precip = pd.Series(0.0, index=date_range)

    # Wave height (m) from marine API
    if not marine_df.empty and "wave_height_max" in marine_df.columns:
        wave_h = marine_df["wave_height_max"].reindex(date_range).ffill().bfill().fillna(1.0)
    else:
        # Fallback: estimate from wind using Beaufort-based approximation
        wave_h = (wind / 25.0).clip(lower=0.3, upper=8.0)
        print("  [WARN] Marine API unavailable. Deriving wave height from wind speed.")

    # Swell height (m)
    if not marine_df.empty and "swell_wave_height_max" in marine_df.columns:
        swell_h = marine_df["swell_wave_height_max"].reindex(date_range).ffill().bfill().fillna(0.5)
    else:
        swell_h = wave_h * 0.6

    # ── Derived meteorological signals ─────────────────────────────
    # Monsoon active flag: June-September + heavy precipitation
    month = date_range.month
    monsoon_season = ((month >= 6) & (month <= 9)).astype(int)
    heavy_rain = (precip > 10.0).astype(int)
    monsoon_flag = np.maximum(monsoon_season, heavy_rain)

    # Cyclone disruption index: 0.0-1.0 normalized from wind speed extremes
    # Tropical cyclone: sustained wind > 63 km/h (Beaufort scale 8+)
    # Severe cyclone: > 89 km/h; Very severe: > 117 km/h
    wind_arr = wind.values
    cyclone_idx = np.zeros(len(wind_arr))
    cyclone_idx = np.where(wind_arr > 63,  0.25, cyclone_idx)
    cyclone_idx = np.where(wind_arr > 89,  0.55, cyclone_idx)
    cyclone_idx = np.where(wind_arr > 117, 0.85, cyclone_idx)
    cyclone_idx = np.where(wind_arr > 150, 1.00, cyclone_idx)
    # Smooth with 3-day rolling average to avoid spikes
    cyclone_smooth = pd.Series(cyclone_idx, index=date_range).rolling(3, min_periods=1).mean().round(3)

    out = pd.DataFrame({
        "date": date_range.strftime("%Y-%m-%d"),
        "bay_of_bengal_wave_height_m": wave_h.round(2).values,
        "swell_height_m": swell_h.round(2).values,
        "windspeed_10m_max_kmh": wind.round(1).values,
        "precipitation_sum_mm": precip.round(2).values,
        "monsoon_active_flag": monsoon_flag,
        "cyclone_disruption_index": cyclone_smooth.values,
        "unit_wave": "meters"
    })

    out.to_csv(OUTPUT_PATH, index=False)

    print(f"\n[SUCCESS] Saved {len(out)} daily records to {OUTPUT_PATH}")
    print(out.head(3).to_string(index=False))
    cyclone_days = (out["cyclone_disruption_index"] > 0.2).sum()
    monsoon_days = out["monsoon_active_flag"].sum()
    print(f"  Monsoon-active days: {monsoon_days} | Cyclone-disruption days: {cyclone_days}")
    print(f"  Wave height range:   {out['bay_of_bengal_wave_height_m'].min():.1f}m -> {out['bay_of_bengal_wave_height_m'].max():.1f}m")


if __name__ == "__main__":
    main()
