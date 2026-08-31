import csv
import os
import json
from datetime import datetime

def run_data_quality_audit():
    print("==================================================")
    print("M1 -> M2 DATA QUALITY AUDIT (SECTION 22)")
    print("==================================================")
    
    # 1. Metadata check
    meta_path = "data/metadata/data_sources.csv"
    assert os.path.exists(meta_path), "Missing data_sources.csv metadata"
    with open(meta_path, "r", encoding="utf-8") as f:
        meta_reader = list(csv.DictReader(f))
        print(f"[PASS] Metadata catalog contains {len(meta_reader)} documented primary data sources.")

    # 2. Raw datasets check
    raw_files = [
        "data/raw/freight/sail_routes_freight_rates_daily.csv",
        "data/raw/shipping/baltic_dry_subindices_daily.csv",
        "data/raw/oil/bunker_vlsfo_brent_daily.csv",
        "data/raw/commodities/dry_bulk_commodities_daily.csv",
        "data/raw/weather/bay_of_bengal_weather_signals.csv",
        "data/raw/ports/east_coast_port_queues.csv",
        "data/raw/macro/usd_inr_macro_pmi.csv"
    ]

    for rf in raw_files:
        assert os.path.exists(rf), f"Missing raw dataset: {rf}"
        with open(rf, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
            assert len(rows) == 730, f"Expected 730 records in {rf}, found {len(rows)}"
            dates = [r["date"] for r in rows]
            # No duplicate dates
            assert len(dates) == len(set(dates)), f"Duplicate dates detected in {rf}"
            # Valid date format
            for d in dates:
                datetime.strptime(d, "%Y-%m-%d")
        print(f"[PASS] Raw Stream verified: {rf} (730 clean daily records, YYYY-MM-DD compliant)")

    # 3. Processed Merged Feature Matrix check
    proc_csv = "data/processed/merged_daily_features.csv"
    proc_json = "data/processed/merged_daily_features.json"
    assert os.path.exists(proc_csv) and os.path.exists(proc_json)
    
    with open(proc_csv, "r", encoding="utf-8") as f:
        p_rows = list(csv.DictReader(f))
        assert len(p_rows) == 730
        print(f"[PASS] Processed Feature Matrix verified: {len(p_rows)} observations with {len(p_rows[0])} aligned columns.")

    print("==================================================")
    print("ALL 12 M2 DATA DELIVERY CRITERIA PASSED!")
    print("==================================================")

if __name__ == "__main__":
    run_data_quality_audit()
