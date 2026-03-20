import upstox_client
import json

def test():
    with open("config.json", "r") as f:
        token = json.load(f).get("access_token")
    
    config = upstox_client.Configuration()
    config.access_token = token
    api_client = upstox_client.ApiClient(config)
    
    # Try different instrument keys
    keys = ["NSE_INDEX|Nifty 50", "NSE_INDEX|NIFTY 50", "NSE_EQ|INE002A01018"]
    
    history_api = upstox_client.HistoryApi(api_client)
    
    for key in keys:
        print(f"Testing key: {key}")
        try:
            res = history_api.get_historical_candle_data1(
                instrument_key=key,
                interval="15minute",
                to_date="2026-03-18",
                from_date="2026-03-18",
                api_version="2.0"
            )
            if res.data and res.data.candles:
                print(f"  SUCCESS! Found {len(res.data.candles)} candles.")
                return key
            else:
                print(f"  FAILED: Empty data for {key}")
        except Exception as e:
            print(f"  ERROR for {key}: {e}")
    return None

if __name__ == "__main__":
    correct_key = test()
    print(f"Correct key is: {correct_key}")
