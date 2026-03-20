import pandas as pd
import asyncio
import logging
import time as ptime
from bot.executor import StrategyExecutor
from data.store import DataStore
from data.historical import CSVLoader
from backtest.metrics import calculate_metrics

logger = logging.getLogger(__name__)

class BacktestEngine:
    """
    Feeds historical CSV rows into the exact same DataStore and Strategy logic 
    as the live Websocket feed, ensuring 100% zero-drift testing.
    """
    def __init__(self, strategy_class, instrument_key, csv_path, pivot_levels):
        self.executor = StrategyExecutor(mode='backtest')
        self.strategy = strategy_class(instrument_key, pivot_levels, self.executor)
        self.store = DataStore(self.strategy, bucket_minutes=15)
        self.csv_path = csv_path
        
    async def run(self):
        loader = CSVLoader(self.csv_path)
        df = loader.get_data()
        
        logger.info("Starting Event-Driven Zero-Drift Backtest...")
        start_t = ptime.time()
        
        for ts, row in df.iterrows():
            ts_ms = int(ts.timestamp() * 1000)
            
            # Simulate intra-bar ticks (Open -> High -> Low -> Close)
            await self.store.process_tick(row['Open'], ts_ms)
            if not self.strategy.risk.can_trade(self.executor.state.realized_pnl): break
            
            await self.store.process_tick(row['High'], ts_ms)
            if not self.strategy.risk.can_trade(self.executor.state.realized_pnl): break
            
            await self.store.process_tick(row['Low'], ts_ms)
            if not self.strategy.risk.can_trade(self.executor.state.realized_pnl): break
            
            await self.store.process_tick(row['Close'], ts_ms)
            if not self.strategy.risk.can_trade(self.executor.state.realized_pnl): break
            
        logger.info(f"Backtest completed in {ptime.time() - start_t:.2f} seconds.")
        calculate_metrics(self.executor.state, logging)
