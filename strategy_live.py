import sys
import os
import asyncio
import json
import logging
from datetime import datetime, time

# Add parent directory to path to import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from broker.upstox_api import UpstoxAPI
from data.upstox_websocket import UpstoxMarketData
from engine.core import TradingEngine
from strategy.base_strategy import BaseStrategy

# --- LIVE 15-MINUTE PIVOT-TO-PIVOT STRATEGY ---
class ThreeCandleV2Live(BaseStrategy):
    def __init__(self, instrument_key, pivot_levels, lot_size=25):
        super().__init__(name="ThreeCandleV2Live")
        self.instrument_key = instrument_key
        self.pivot_levels = sorted(pivot_levels)
        self.lot_size = lot_size
        
        # State
        self.anchor_h = None
        self.anchor_l = None
        self.inside_count = 0
        self.position = None # None, 'LONG', 'SHORT'
        self.entry_trigger_px = None
        
        # Candle Aggregator (15-min)
        self.current_15m_candle = None
        self.current_15m_start = None
        
    async def on_tick(self, tick_event):
        # 1. Aggregation Logic
        # tick_event = {"instrument": key, "data": feed}
        if tick_event['instrument'] != self.instrument_key:
            return
            
        data = tick_event['data']
        # Extract LTP from Upstox v3 Feed structure (ltpc = Last Trade Price/Change)
        # Structure varies slightly based on feed mode. Assuming full mode 'ff'.
        try:
            price = data['ff']['marketFF']['ltpc']['cp']
            timestamp = int(data['ff']['marketFF']['ltpc']['ltt']) # Last Trade Time
        except KeyError:
            # Fallback for different feed structures (e.g. index/LTP mode)
            try:
                price = data['ltpc']['cp']
                timestamp = int(data['ltpc']['ltt'])
            except:
                return

        curr_datetime = datetime.fromtimestamp(timestamp / 1000)
        curr_time = curr_datetime.time()
        
        # 15-minute bucket logic
        minute = curr_datetime.minute
        bucket_start_min = (minute // 15) * 15
        bucket_start = curr_datetime.replace(minute=bucket_start_min, second=0, microsecond=0)
        
        if self.current_15m_start is None or bucket_start > self.current_15m_start:
            if self.current_15m_candle:
                await self._on_15m_close(self.current_15m_candle, self.current_15m_start.time())
            
            # Start new candle
            self.current_15m_start = bucket_start
            self.current_15m_candle = {'open': price, 'high': price, 'low': price, 'close': price}
        else:
            # Update existing candle
            self.current_15m_candle['high'] = max(self.current_15m_candle['high'], price)
            self.current_15m_candle['low'] = min(self.current_15m_candle['low'], price)
            self.current_15m_candle['close'] = price

    async def _on_15m_close(self, candle, candle_time):
        # 2. Phase 1: Anchor (09:15-09:30)
        if candle_time == time(9, 15):
            self.anchor_h = candle['high']
            self.anchor_l = candle['low']
            print(f"[{candle_time}] Anchor Set! H: {self.anchor_h}, L: {self.anchor_l}")
            return
            
        if self.anchor_h is None: return
        
        # 3. Phase 2: Compression Count (09:30-10:15)
        if time(9, 30) <= candle_time < time(10, 15):
            if candle['high'] < self.anchor_h and candle['low'] > self.anchor_l:
                self.inside_count += 1
                print(f"[{candle_time}] Inside Candle! Total: {self.inside_count}")
            return
            
        # 4. Phase 3: Breakout Monitoring (10:15+)
        if candle_time >= time(10, 15) and self.position is None:
            if self.inside_count < 3: return # Requirement for setup
            
            # LONG Breakout Confirmation
            if candle['close'] > self.anchor_h:
                entry_px = candle['high'] # Stop order at High
                target_px = self._get_target(entry_px, 'LONG')
                sl_px = self._get_sl(entry_px, 'LONG')
                
                print(f"[{candle_time}] 🚀 LONG BREAKOUT! Trigger Stop-Buy @ {entry_px}")
                self.place_order({'symbol': self.instrument_key, 'side': 'BUY', 'qty': self.lot_size, 'price': entry_px, 'target': target_px, 'sl': sl_px})
                self.position = 'LONG'
                
            # SHORT Breakout Confirmation
            elif candle['close'] < self.anchor_l:
                entry_px = candle['low'] # Stop order at Low
                target_px = self._get_target(entry_px, 'SHORT')
                sl_px = self._get_sl(entry_px, 'SHORT')
                
                print(f"[{candle_time}] 📉 SHORT BREAKOUT! Trigger Stop-Sell @ {entry_px}")
                self.place_order({'symbol': self.instrument_key, 'side': 'SELL', 'qty': self.lot_size, 'price': entry_px, 'target': target_px, 'sl': sl_px})
                self.position = 'SHORT'

    def _get_target(self, px, side):
        if side == 'LONG':
            for lvl in self.pivot_levels:
                if lvl > px: return lvl
            return self.pivot_levels[-1]
        else:
            for lvl in reversed(self.pivot_levels):
                if lvl < px: return lvl
            return self.pivot_levels[0]
            
    def _get_sl(self, px, side):
        if side == 'LONG':
            for lvl in reversed(self.pivot_levels):
                if lvl < px: return lvl
            return self.pivot_levels[0]
        else:
            for lvl in self.pivot_levels:
                if lvl > px: return lvl
            return self.pivot_levels[-1]

# --- LIVE EXECUTION WRAPPER ---
async def start_live_bot():
    # Load Config
    with open('../config.json', 'r') as f:
        config = json.load(f)
        
    api = UpstoxAPI(config['access_token'])
    
    # 1. Fetch Yesterday's Data for Pivots
    print("Fetching yesterday's data for pivot calculation...")
    # (Implementation for history fetch omitted for brevity, using demo pivots)
    demo_pivots = [23800, 23900, 24000, 24100, 24200] 
    
    # 2. Init Strategy
    instr = "NSE_INDEX|Nifty 50"
    strategy = ThreeCandleV2Live(instr, demo_pivots)
    
    # 3. Start Engine
    engine = TradingEngine(api, config['access_token'])
    engine.add_strategy(strategy)
    
    print(f"Live Bot Started for {instr}. Waiting for 09:15...")
    await engine.run([instr])

if __name__ == "__main__":
    asyncio.run(start_live_bot())
