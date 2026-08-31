import json
import math
import random
from datetime import datetime, timedelta

def generate_market_data():
    base_date = datetime.now() - timedelta(days=730)
    data = []
    
    # Starting levels
    bci = 2850.0   # Baltic Capesize Index
    bpi = 1680.0   # Baltic Panamax Index
    bsi = 1350.0   # Baltic Supramax Index
    bhsi = 820.0   # Baltic Handysize Index
    vlsfo = 620.0  # VLSFO bunker $/MT (Singapore/Rotterdam)
    coal_newcastle = 142.0 # $/MT
    
    random.seed(42)
    
    for day_idx in range(730):
        current_date = base_date + timedelta(days=day_idx)
        d_str = current_date.strftime("%Y-%m-%d")
        day_of_year = current_date.timetuple().tm_yday
        
        # Seasonality factors:
        # Q1 (Jan-Feb, day 1-60): Post-Christmas / Chinese New Year slowdown (-15%)
        # Q2 (Apr-Jun, day 90-180): Rebound (+10%)
        # Monsoon (Jun-Aug, day 160-240): High swell on Indian East Coast, Australian dry weather
        # Q4 (Sep-Nov, day 260-330): Peak coal restocking before winter (+20%)
        season_wave = math.sin(2 * math.pi * (day_of_year - 80) / 365)
        
        # Random walks with mean-reversion
        bci_drift = 0.05 * (2600.0 - bci) + 80.0 * season_wave + random.gauss(0, 95.0)
        bpi_drift = 0.04 * (1600.0 - bpi) + 40.0 * season_wave + random.gauss(0, 45.0)
        bsi_drift = 0.04 * (1300.0 - bsi) + 30.0 * season_wave + random.gauss(0, 35.0)
        bhsi_drift = 0.03 * (800.0 - bhsi) + 18.0 * season_wave + random.gauss(0, 20.0)
        vlsfo_drift = 0.02 * (600.0 - vlsfo) + random.gauss(0, 8.0)
        coal_drift = 0.02 * (135.0 - coal_newcastle) + random.gauss(0, 2.5)
        
        bci = max(900.0, min(5500.0, bci + bci_drift))
        bpi = max(700.0, min(3200.0, bpi + bpi_drift))
        bsi = max(600.0, min(2500.0, bsi + bsi_drift))
        bhsi = max(450.0, min(1600.0, bhsi + bhsi_drift))
        vlsfo = max(450.0, min(850.0, vlsfo + vlsfo_drift))
        coal_newcastle = max(95.0, min(220.0, coal_newcastle + coal_drift))
        
        # Derived TCE daily rates ($/day)
        tce_capesize = round(bci * 9.2 + 2000, 2)
        tce_panamax = round(bpi * 9.8 + 1500, 2)
        tce_supramax = round(bsi * 10.5 + 1000, 2)
        tce_handysize = round(bhsi * 11.2 + 800, 2)
        
        # Key benchmark route: Australia (Hay Point) to Paradip (75k MT Panamax rate in $/MT)
        # Voyage distance: 4,650 NM -> 14.5 days sea + 3 days port = 17.5 total days
        # Fuel: 14.5 * 29.5 MT = 427 MT VLSFO * vlsfo + Port 3*4 MT MGO * (vlsfo*1.3)
        voyage_fuel = (14.5 * 29.5 * vlsfo) + (3.0 * 4.0 * vlsfo * 1.25)
        voyage_hire = 17.5 * tce_panamax
        port_dues = 65000.0
        total_voyage_cost = voyage_fuel + voyage_hire + port_dues
        panamax_aus_paradip_per_mt = round(total_voyage_cost / 75000.0, 2)
        
        data.append({
            "date": d_str,
            "bci": round(bci, 1),
            "bpi": round(bpi, 1),
            "bsi": round(bsi, 1),
            "bhsi": round(bhsi, 1),
            "bdi_composite": round((bci + bpi + bsi + bhsi) / 4.0, 1),
            "vlsfo_bunker_usd_t": round(vlsfo, 2),
            "newcastle_coal_usd_t": round(coal_newcastle, 2),
            "tce_capesize_usd_day": tce_capesize,
            "tce_panamax_usd_day": tce_panamax,
            "tce_supramax_usd_day": tce_supramax,
            "tce_handysize_usd_day": tce_handysize,
            "route_aus_paradip_panamax_usd_t": panamax_aus_paradip_per_mt
        })
        
    with open("app/data/historical_indices.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Generated {len(data)} days of realistic maritime market data.")

if __name__ == "__main__":
    generate_market_data()
