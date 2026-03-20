import asyncio
from broker.upstox_api import UpstoxAPI
from data.upstox_websocket import UpstoxMarketData
import logging

logging.basicConfig(level=logging.INFO)

import json

async def test_ws():
    print("Initializing Upstox API and Market Data clients...")
    with open("config.json", "r") as f:
        token = json.load(f).get("access_token")
    api = UpstoxAPI(access_token=token)
    ws_client = UpstoxMarketData(api_client=api)
    
    def handle_tick(message):
        print(f"Received raw tick data: {message[:50]}...")
        # NOTE: Upstox sends binary Protobuf strings. You will need to decode them 
        # using the Upstox MarketDataFeed protobuf definitions.
        
    ws_client.on_tick(handle_tick)
    
    print("Attempting to connect to WebSocket...")
    # Run the connection in a background task
    connection_task = asyncio.create_task(ws_client.connect())
    
    # Wait a bit for connection to establish
    await asyncio.sleep(2)
    
    # Subscribe to an example instrument token (e.g., Reliance NSE EQ)
    try:
        await ws_client.subscribe(["NSE_EQ|INE002A01018"])
    except Exception as e:
        print(f"Subscription failed: {e}")
        
    # Listen for 10 seconds then stop
    print("Listening for 10 seconds...")
    await asyncio.sleep(10)
    
    print("Stopping client...")
    ws_client.stop()
    
    # Wait for the connection task to cleanly exit
    await connection_task
    print("Test finished.")

if __name__ == "__main__":
    # If using Jupyter, you might need nest_asyncio to run asyncio.run()
    # import nest_asyncio
    # nest_asyncio.apply()
    try:
        asyncio.run(test_ws())
    except Exception as e:
        print(f"Failed to run test: {e}")
