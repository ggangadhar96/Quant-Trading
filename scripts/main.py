import asyncio
import json
import os
from engine.core import TradingEngine
from strategy.three_candle_strategy import ThreeCandleStrategy
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def main():
    # --- 1. CONFIGURATION ---
    config_path = "config.json"
    UPSTOX_TOKEN = ""
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            UPSTOX_TOKEN = json.load(f).get("access_token", "")
            
    if not UPSTOX_TOKEN:
        print("WARNING: No UPSTOX_TOKEN found in config.json. Please run 'python login.py' or provide a sandbox token.")
    
    # Example: Nifty 50 Futures symbol token
    INSTRUMENT_TOKENS = ["NSE_FO|123456"] 
    
    # --- 2. INITIALIZE STRATEGY ---
    # In a real environment, query these Previous Day values from the historic data API.
    # We pass dummy previous day statistics for NIFTY to test the pivots.
    my_strategy = ThreeCandleStrategy(
        previous_day_high=24500.0,
        previous_day_low=24200.0,
        previous_day_close=24400.0
    )
    
    # --- 3. INITIALIZE ENGINE ---
    # The engine binds the strategy to the API client and data feed
    engine = TradingEngine(api_token=UPSTOX_TOKEN, strategies=[my_strategy])
    
    # --- 4. START ---
    print("Starting algorithmic trading application...")
    await engine.start(instrument_tokens=INSTRUMENT_TOKENS)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Application cleanly stopped.")
