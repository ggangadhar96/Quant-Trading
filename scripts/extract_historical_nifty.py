import json
import logging
from datetime import datetime, timedelta
import pandas as pd
import upstox_client
from upstox_client.rest import ApiException
import time
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

def fetch_nifty_resampled(months=6, target_interval_min=15):
    # Load Upstox access token from .env
    load_dotenv()
    token = os.getenv("UPSTOX_ACCESS_TOKEN")
    if not token:
        print("Error: UPSTOX_ACCESS_TOKEN not found in .env file")
        return

    # 1. Configure SDK
    configuration = upstox_client.Configuration()
    configuration.access_token = token
    api_client = upstox_client.ApiClient(configuration)
    history_api = upstox_client.HistoryApi(api_client)
    
    # instrument_key for NIFTY 50
    instrument_key = "NSE_INDEX|Nifty 50"
    api_version = "2.0"
    
    # 2. Date Ranges (Start from YESTERDAY to avoid 400 error with today's early timestamp)
    end_date = datetime.now() - timedelta(days=1)
    start_date = datetime.now() - timedelta(days=months * 30)
    
    print(f"Goal: Fetch {target_interval_min}min data for NIFTY 50 for past {months} months.")
    print(f"Range: {start_date.date()} to {end_date.date()}")
    
    all_candles = []
    current_end = end_date
    chunk_days = 7 # Use 7-day chunks for maximum reliability
    
    while current_end > start_date:
        current_start = max(start_date, current_end - timedelta(days=chunk_days))
        
        str_to = current_end.strftime("%Y-%m-%d")
        str_from = current_start.strftime("%Y-%m-%d")
        
        print(f"  Requesting 1min chunk: {str_from} to {str_to}...")
        
        try:
            response = history_api.get_historical_candle_data1(
                instrument_key=instrument_key,
                interval="1minute",
                to_date=str_to,
                from_date=str_from,
                api_version=api_version
            )
            
            if response.data and response.data.candles:
                all_candles.extend(response.data.candles)
                print(f"    Received {len(response.data.candles)} 1min candles.")
            else:
                print(f"    No data found for {str_from} to {str_to}")
            
            # Move back
            current_end = current_start - timedelta(days=1)
            time.sleep(0.3) # Rate limiting buffer
            
        except ApiException as e:
            print(f"API Error ({e.status}): {e.reason}")
            if e.status == 401:
                print("Token invalid or expired.")
                return
            break

    if not all_candles:
        print("\n❌ Final result: No data retrieved. Try checking if the index key or date depth is allowed.")
        return

    # 4. Process and Save
    df = pd.DataFrame(all_candles)
    # Mapping columns: 0=time, 1=open, 2=high, 3=low, 4=close, 5=vol, 6=oi
    df.columns = ["Timestamp", "Open", "High", "Low", "Close", "Volume", "OI"][:len(df.columns)]
    
    df["Timestamp"] = pd.to_datetime(df["Timestamp"]).dt.tz_convert('Asia/Kolkata')
    df.set_index("Timestamp", inplace=True)
    df = df.sort_index()

    # 4. Resample to 15-minute data
    # We aggregate 1-minute OHLC to 15-minute OHLC
    df_15min = df.resample(f"{target_interval_min}min").agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last"
    }).dropna()

    # 5. Save outputs to data/csv/
    # Save the aggregated data (original V1 format)
    v1_filename = f"data/csv/NIFTY50_15min_{months}months.csv"
    df_15min.to_csv(v1_filename)
    print(f"15-minute data saved to {v1_filename}")
    
    # Save the raw 1-minute data for V2 refined
    raw_filename = f"data/csv/NIFTY50_1min_{months}months.csv"
    df.to_csv(raw_filename)
    print(f"Raw 1-minute data saved to {raw_filename}")

    print(f"\n✅ SUCCESS! Extracted {len(df)} 1-minute candles and {len(df_15min)} 15-minute candles.")
    print(f"1-min samples:\n{df.head(2)}")
    print(f"15-min samples:\n{df_15min.head(2)}")


if __name__ == "__main__":
    # Ensure data/csv directory exists
    os.makedirs("data/csv", exist_ok=True)
    
    print("=" * 50)
    print("  NIFTY 50 Historical Data Extractor")
    print("=" * 50)
    
    try:
        months_input = input("Enter number of months to extract (e.g. 6 or 12) [default: 6]: ").strip()
        months = int(months_input) if months_input else 6
    except ValueError:
        print("Invalid input, using default: 6 months")
        months = 6
    
    try:
        interval_input = input("Enter target candle interval in minutes (e.g. 1, 5, 15) [default: 15]: ").strip()
        interval = int(interval_input) if interval_input else 15
    except ValueError:
        print("Invalid input, using default: 15 minutes")
        interval = 15
    
    print(f"\n▶ Extracting {months} months of data, resampled to {interval}-minute candles...")
    fetch_nifty_resampled(months=months, target_interval_min=interval)

