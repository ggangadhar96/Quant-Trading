import sys
import os
import argparse
import asyncio
import yaml
import logging
from dotenv import load_dotenv

# Windows terminals default to cp1252 — force UTF-8 so emoji log messages don't crash
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from infra.broker import UpstoxAPI
from bot.strategy import ThreeCandleV2Live
from bot.strategy_v2_1 import ThreeCandleV2_1
from bot.executor import StrategyExecutor

from backtest.engine import BacktestEngine
from data.feed import UpstoxMarketData
from data.store import DataStore

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)

async def run_live(config, mode, strategy_class):
    access_token = os.getenv("UPSTOX_ACCESS_TOKEN")
    if not access_token:
        raise ValueError("Missing UPSTOX_ACCESS_TOKEN in .env")
        
    api = UpstoxAPI(access_token)
    
    # 1. Core Bot Initialization
    executor = StrategyExecutor(mode=mode, broker=api)
    strategy = strategy_class(config['instrument'], config['pivot_levels'], executor, config=config)
    
    # 2. Time Bucket / Market Data Store
    store = DataStore(strategy, bucket_minutes=15)
    
    # 3. Live WebSocket Feed
    feed = UpstoxMarketData(api_client=api)
    
    def on_tick_callback(tick_json):
        if 'feeds' not in tick_json: return
        for instrument_key, feed_data in tick_json['feeds'].items():
            if instrument_key != config['instrument']: continue
            try:
                # Assuming v3 full mode standard structure
                price = feed_data['ff']['marketFF']['ltpc']['cp']
                ts = int(feed_data['ff']['marketFF']['ltpc']['ltt'])
                
                # We can't await directly inside a sync callback unless we create a task
                # In production, a proper async queue or event emitter is better
                asyncio.create_task(store.process_tick(price, ts))
            except Exception as e:
                logger.debug(f"Tick parse error: {e}")
                
    feed.on_tick(on_tick_callback)
    
    logger.info(f"Starting {mode.upper()} mode for {config['instrument']}...")
    await feed.connect_and_subscribe([config['instrument']])

async def main():
    parser = argparse.ArgumentParser(description="Three-Candle Zero Drift Bot")
    parser.add_argument("--mode", choices=['live', 'dryrun', 'backtest'], default='dryrun', help="Execution mode")
    parser.add_argument("--strategy", choices=['v2', 'v2.1'], default='v2.1', help="Strategy version")
    args = parser.parse_args()

    load_dotenv()
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    str_cfg = config['strategy']
    
    # Strategy Selection
    strategies = {
        'v2': ThreeCandleV2Live,
        'v2.1': ThreeCandleV2_1
    }
    selected_strategy = strategies[args.strategy]

    if args.mode == 'backtest':
        csv_path = "data/csv/NIFTY50_15min_6months.csv"
        engine = BacktestEngine(selected_strategy, str_cfg['instrument'], csv_path, str_cfg['pivot_levels'])
        # Pass config to backtest strategy
        engine.strategy = selected_strategy(str_cfg['instrument'], str_cfg['pivot_levels'], engine.executor, config=str_cfg)
        await engine.run()
    else:
        await run_live(str_cfg, args.mode, selected_strategy)

if __name__ == "__main__":
    asyncio.run(main())
