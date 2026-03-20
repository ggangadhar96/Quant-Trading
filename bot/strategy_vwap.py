import logging
from datetime import time
from typing import Dict, Any, List, Optional
import pandas as pd
from bot.base_strategy import BaseStrategy
from bot.indicators import calculate_vwap, calculate_rsi, calculate_atr

logger = logging.getLogger(__name__)

class VWAPStrategy(BaseStrategy):
    """
    VWAP Trend Following Strategy:
    - Long: Price > VWAP and RSI > 55
    - Short: Price < VWAP and RSI < 45
    - Exit: 1.5 * ATR Stop-loss, 2.0 * RR Target
    """
    def __init__(self, instrument_key: str, pivot_levels: List[float], executor, config: Optional[Dict[str, Any]] = None):
        super().__init__("VWAPTrend", executor)
        self.instrument_key = instrument_key
        
        # Strategy State
        self.ohlc_history: List[Dict[str, Any]] = []
        self.pending_entry: Optional[str] = None
        
        # Selectable Params
        self.rsi_period = config.get('rsi_period', 14) if config else 14
        self.atr_period = config.get('atr_period', 14) if config else 14
        self.atr_mult = config.get('atr_multiplier', 1.5) if config else 1.5
        self.rr_ratio = config.get('risk_reward_ratio', 2.0) if config else 2.0

    async def on_bar(self, bar: Dict[str, Any]):
        self.ohlc_history.append(bar)
        if len(self.ohlc_history) > 300: self.ohlc_history.pop(0)
        if len(self.ohlc_history) < 30: return # Warmup
        
        df = pd.DataFrame(self.ohlc_history)
        df['vwap'] = calculate_vwap(df)
        df['rsi'] = calculate_rsi(df['close'], self.rsi_period)
        df['atr'] = calculate_atr(df['high'], df['low'], df['close'], self.atr_period)
        
        curr_price = df['close'].iloc[-1]
        curr_vwap = df['vwap'].iloc[-1]
        curr_rsi = df['rsi'].iloc[-1]
        curr_atr = df['atr'].iloc[-1]
        candle_dt = bar['time']
        candle_time = candle_dt.time()

        # Entry Logic (Must be at bar close)
        if self.state.position is None and self.pending_entry is None:
            # LONG Entry
            if curr_price > curr_vwap and curr_rsi > 55:
                logger.info(f"[{candle_time}] VWAP LONG Signal! RSI: {curr_rsi:.2f}")
                self.pending_entry = 'LONG'
            # SHORT Entry
            elif curr_price < curr_vwap and curr_rsi < 45:
                logger.info(f"[{candle_time}] VWAP SHORT Signal! RSI: {curr_rsi:.2f}")
                self.pending_entry = 'SHORT'
                
        # Trigger entry on NEXT bar open
        if self.pending_entry:
            await self._execute_entry(bar['open'], candle_time, curr_atr)
            self.pending_entry = None

    async def on_tick(self, tick: Dict[str, Any]):
        if self.state.position is None: return
        
        price = tick['price']
        curr_time = tick['time']
        
        # Risk Management
        if self.state.position == 'LONG':
            if price >= self.state.target_px:
                self.executor.execute_exit(price, "TARGET", curr_time)
            elif price <= self.state.sl_px:
                self.executor.execute_exit(price, "SL", curr_time)
        elif self.state.position == 'SHORT':
            if price <= self.state.target_px:
                self.executor.execute_exit(price, "TARGET", curr_time)
            elif price >= self.state.sl_px:
                self.executor.execute_exit(price, "SL", curr_time)
                
        # EOD Square-off
        if curr_time >= time(15, 15):
            self.executor.execute_exit(price, "EOD", curr_time)

    async def _execute_entry(self, price: float, timestamp, atr: float):
        sl_dist = self.atr_mult * atr
        if self.pending_entry == 'LONG':
            sl = price - sl_dist
            target = price + (self.rr_ratio * sl_dist)
        else:
            sl = price + sl_dist
            target = price - (self.rr_ratio * sl_dist)
            
        success = self.executor.execute_entry(
            symbol=self.instrument_key,
            side=self.pending_entry,
            qty=self.executor.risk.lot_size,
            price=price,
            target=target,
            sl=sl,
            timestamp=timestamp
        )
