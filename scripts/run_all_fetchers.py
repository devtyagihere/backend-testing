"""
run_all_fetchers.py
--------------------
Master orchestrator: runs all real-data API fetchers in sequence, then
validates the complete data pipeline against M1->M2 quality criteria.

Fetcher order:
  1. fetch_oil_prices.py        → EIA   → data/raw/oil/
  2. fetch_commodity_prices.py  → Alpha Vantage → data/raw/commodities/
  3. fetch_weather_data.py      → Open-Meteo   → data/raw/weather/
  4. fetch_macro_indicators.py  → FRED  → data/raw/macro/
  5. fetch_market_proxies.py    → yfinance → data/raw/shipping/
  6. validate_data_quality.py   → audit all M2 delivery criteria

Usage:
  python scripts/run_all_fetchers.py
"""

import subprocess
import sys
import time
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
PYTHON = sys.executable

FETCHERS = [
    ("Oil & Fuel Prices",       "fetch_oil_prices.py",       "EIA API"),
    ("Commodity Prices",         "fetch_commodity_prices.py", "Alpha Vantage API"),
    ("Weather / Port Signals",   "fetch_weather_data.py",     "Open-Meteo API (free)"),
    ("Macro Indicators",         "fetch_macro_indicators.py", "FRED API"),
    ("Market Proxies",           "fetch_market_proxies.py",   "Yahoo Finance (yfinance)"),
]


def run_script(name: str, script: str, source: str) -> bool:
    """Run a fetcher script and return True on success."""
    print()
    print("─" * 60)
    print(f"  {name}")
    print(f"  Source: {source}")
    print(f"  Script: scripts/{script}")
    print("─" * 60)
    result = subprocess.run(
        [PYTHON, str(SCRIPTS_DIR / script)],
        capture_output=False,
        text=True
    )
    if result.returncode != 0:
        print(f"\n  [FAILED] {script} exited with code {result.returncode}")
        return False
    return True


def main():
    print("=" * 60)
    print("  SAIL FREIGHT FORECASTING — DATA PIPELINE REFRESH")
    print("  Running all real-data API fetchers")
    print("=" * 60)

    results = {}
    for name, script, source in FETCHERS:
        ok = run_script(name, script, source)
        results[name] = ok
        if not ok:
            print(f"  WARNING: {name} failed — existing data will remain in place.")
        # Small pause between fetchers to avoid API rate limits
        time.sleep(2)

    # Run data quality validation
    print()
    print("=" * 60)
    print("  RUNNING DATA QUALITY VALIDATION")
    print("=" * 60)
    val_result = subprocess.run(
        [PYTHON, str(SCRIPTS_DIR / "validate_data_quality.py")],
        capture_output=False,
        text=True
    )

    # Print final summary
    print()
    print("=" * 60)
    print("  PIPELINE REFRESH SUMMARY")
    print("=" * 60)
    for name, ok in results.items():
        status = "✓ OK" if ok else "✗ FAILED"
        print(f"  {status:<10} {name}")
    print(f"  {'✓ OK' if val_result.returncode == 0 else '✗ FAILED':<10} Data Quality Validation")

    failed = [n for n, ok in results.items() if not ok]
    if failed or val_result.returncode != 0:
        print("\n  Some fetchers failed. Check logs above for details.")
        sys.exit(1)
    else:
        print("\n  All fetchers completed successfully. Data pipeline is live.")


if __name__ == "__main__":
    main()
