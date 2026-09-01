import os
import pandas as pd
import yfinance as yf

def fetch_market_proxies():
    # Define proxies for Dry Bulk Index (P2) and Crude Oil (P3)
    tickers = {
        "dry_bulk_etf": "BDRY",     # Breakwave Dry Bulk Shipping ETF
        "oil_brent": "BZ=F",        # Brent Crude Oil Futures
        "oil_wti": "CL=F",          # WTI Crude Oil Futures
        "usd_inr": "USDINR=X"       # USD to INR Exchange Rate
    }

    output_dir = "data/raw/shipping"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "yfinance_market_proxies.csv")

    print("Downloading historical market data from 2020-01-01 to 2026-09-01...")
    
    # Download with threads=False or per ticker to prevent sqlite cache lock issues
    data_dict = {}
    for name, ticker in tickers.items():
        try:
            print(f"Fetching {name} ({ticker})...")
            df = yf.download(ticker, start="2020-01-01", end="2026-09-01", progress=False)["Close"]
            if isinstance(df, pd.DataFrame):
                df = df.iloc[:, 0]
            data_dict[name] = df
        except Exception as e:
            print(f"Error downloading {ticker}: {e}")

    raw_data = pd.DataFrame(data_dict)

    # Save raw dataset without modifying or dropping NaN values
    raw_data.to_csv(output_path)


    print(f"Saved raw market proxy data to {output_path}")
    print(raw_data.head())
    print(f"Total rows: {len(raw_data)}")

if __name__ == "__main__":
    fetch_market_proxies()
