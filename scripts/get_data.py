import json
import logging
from broker.upstox_api import UpstoxAPI

logging.basicConfig(level=logging.INFO)

def get_stock_data():
    try:
        with open("config.json", "r") as f:
            token = json.load(f).get("access_token")
    except Exception as e:
        print(f"Failed to load config: {e}")
        return
        
    client = UpstoxAPI(access_token=token)
    
    instrument_key = "NSE_EQ|INE002A01018"
    print(f"Attempting to fetch Market Quote for: {instrument_key}")
    
    try:
        response = client._request('GET', '/market-quote/quotes', params={'instrument_key': instrument_key})
        print("\nSUCCESS! Market Quote Data:")
        print(json.dumps(response, indent=2))
    except Exception as e:
        print(f"Error fetching market quote: {e}")
        
    print(f"\nAttempting to fetch Historical Data for: {instrument_key}")
    try:
        # GET /historical-data/NSE_EQ|INE002A01018/day/2023-11-01/2023-10-01
        res = client._request('GET', f'/historical-data/{instrument_key}/day/2024-03-01/2024-02-01')
        print("\nSUCCESS! Historical Data:")
        print(json.dumps(res, indent=2))
    except Exception as e:
        print(f"Error fetching historical data: {e}")

if __name__ == "__main__":
    get_stock_data()
