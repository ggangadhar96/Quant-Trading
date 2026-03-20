import logging
from datetime import time, date
from typing import Dict, Any, List, Optional
import pandas as pd
from bot.base_strategy import BaseStrategy
from bot.indicators import calculate_cpr

logger = logging.getLogger(__name__)

class CPRStrategy(BaseStrategy):
    """
    CPR Breakout Strategy:
    - Uses Daily CPR (Pivot, TC, BC) calculated from previous day.
    - Entry: Price breaks out of CPR range after 09:30.
    - Target: R1/S1 or 1:2 RR.
    """
    def __init__(self, instrument_key: str, pivot_levels: List[float], executor, config: Optional[Dict[str, Any]] = None):
        super().__init__("CPRBreakout", executor)
        self.instrument_key = instrument_key
        
        # CPR Levels
        self.daily_cpr: Optional[Dict[str, float]] = None
        self.current_day: Optional[date] = None
        self.prev_day_ohlc: Dict[str, float] = {'H': 0, 'L': 0, 'C': 0}
        
        # State
        self.pending_entry: Optional[str] = None

    async def on_bar(self, bar: Dict[str, Any]):
        candle_dt = bar['time']
        candle_time = candle_dt.time()
        # If it's the first bar of the day (09:15)
        if candle_time == time(9, 15):
            # Finalize previous day
            if self.prev_day_ohlc['C'] > 0:
                self.daily_cpr = calculate_cpr(
                    self.prev_day_ohlc['H'], 
                    self.prev_day_ohlc['L'], 
                    self.prev_day_ohlc['C']
                )
                logger.info(f"New CPR Set! Pivot: {self.daily_cpr['pivot']:.2f}")
            
            # Reset daily OHLC trackers with 9:15 candle
            self.prev_day_ohlc = {'H': bar['high'], 'L': bar['low'], 'C': bar['close']}
            self.pending_entry = None
            return

        # Update running OHLC for the current day
        self.prev_day_ohlc['H'] = max(self.prev_day_ohlc['H'], bar['high'])
        self.prev_day_ohlc['L'] = min(self.prev_day_ohlc['L'], bar['low'])
        self.prev_day_ohlc['C'] = bar['close']

        if not self.daily_cpr: return

        # Strategy Logic (Post 09:30)
        if time(9, 30) <= candle_time < time(15, 0) and self.state.position is None:
            # Long on breakout of TC
            if bar['close'] > self.daily_cpr['tc'] and bar['open'] <= self.daily_cpr['tc']:
                logger.info(f"[{candle_time}] CPR Bullish Breakout!")
                self.pending_entry = 'LONG'
            # Short on breakdown of BC
            elif bar['close'] < self.daily_cpr['bc'] and bar['open'] >= self.daily_cpr['bc']:
                logger.info(f"[{candle_time}] CPR Bearish Breakdown!")
                self.pending_entry = 'SHORT'

        # Execute
        if self.pending_entry:
            await self._execute_entry(bar['open'], candle_time)
            self.pending_entry = None

    async def on_tick(self, tick: Dict[str, Any]):
        if self.state.position is None: return
        price = tick['price']
        curr_time = tick['time']
        
        if self.state.position == 'LONG':
            if price >= self.state.target_px: self.executor.execute_exit(price, "TARGET", curr_time)
            elif price <= self.state.sl_px: self.executor.execute_exit(price, "SL", curr_time)
        elif self.state.position == 'SHORT':
            if price <= self.state.target_px: self.executor.execute_exit(price, "TARGET", curr_time)
            elif price >= self.state.sl_px: self.executor.execute_exit(price, "SL", curr_time)

        if curr_time >= time(15, 15):
            self.executor.execute_exit(price, "EOD", curr_time)

    async def _execute_entry(self, price: float, timestamp):
        # Target/SL based on CPR width or 1%
        dist = abs(self.daily_cpr['tc'] - self.daily_cpr['bc']) * 2
        if self.pending_entry == 'LONG':
            sl = self.daily_cpr['bc']
            target = price + dist
        else:
            sl = self.daily_cpr['tc']
            target = price - dist
            
        self.executor.execute_entry(
            symbol=self.instrument_key,
            side=self.pending_entry,
            qty=self.executor.risk.lot_size,
            price=price,
            target=target,
            sl=sl,
            timestamp=timestamp
        )
