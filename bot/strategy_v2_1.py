import logging
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import time
from bot.base_strategy import BaseStrategy
from bot.indicators import calculate_ema, calculate_atr

logger = logging.getLogger(__name__)

class ThreeCandleV2_1(BaseStrategy):
    """
    Optimized version of Three-Candle Breakout.
    Features:
    - 200 EMA Trend Filter
    - ATR-based dynamic Stop-Loss
    - 1:2 Risk-Reward Target
    """
    def __init__(self, instrument_key: str, pivot_levels: List[float], executor, config: Optional[Dict[str, Any]] = None):
        super().__init__("ThreeCandleV2.1", executor)
        self.instrument_key = instrument_key
        self.pivot_levels = sorted(pivot_levels)
        
        # Strategy State
        self.ohlc_history: List[Dict[str, Any]] = []
        self.inside_count: int = 0
        self.anchor_h: float = 0.0
        self.anchor_l: float = 0.0
        self.pending_entry: Optional[str] = None
        
        # Indicator params (Configurable)
        self.ema_period = config.get('ema_period', 200) if config else 200
        self.atr_period = config.get('atr_period', 14) if config else 14
        self.atr_mult = config.get('atr_multiplier', 1.5) if config else 1.5
        self.rr_ratio = config.get('risk_reward_ratio', 2.0) if config else 2.0
        
    async def on_bar(self, bar: Dict[str, Any]):
        self.ohlc_history.append(bar)
        if len(self.ohlc_history) > 250: self.ohlc_history.pop(0)
        if len(self.ohlc_history) < self.ema_period: return
        
        df = pd.DataFrame(self.ohlc_history)
        df['ema'] = calculate_ema(df['close'], self.ema_period)
        df['atr'] = calculate_atr(df['high'], df['low'], df['close'], self.atr_period)
        
        curr_ema = df['ema'].iloc[-1]
        curr_atr = df['atr'].iloc[-1]
        candle_dt = bar['time']
        candle_time = candle_dt.time()

        # 1. Phase 1: Anchor (09:15-09:30)
        if candle_time == time(9, 15):
            self.anchor_h, self.anchor_l = bar['high'], bar['low']
            self.inside_count = 0
            self.pending_entry = None
            return

        if self.anchor_h == 0.0: return # No anchor yet for today

        # 2. Trigger Pending Entry (from previous bar's confirmation)
        if self.pending_entry:
            await self._execute_entry(bar['open'], candle_time, curr_atr)
            self.pending_entry = None

        # 3. Phase 2: Compression (09:30-10:15)
        if time(9, 30) <= candle_time < time(10, 15):
            if bar['high'] < self.anchor_h and bar['low'] > self.anchor_l:
                self.inside_count += 1
            return

        # 4. Phase 3: Breakout Confirmation (10:15+)
        if candle_time >= time(10, 15) and self.state.position is None:
            if self.inside_count >= 3:
                # LONG: Breakout + Above EMA
                if bar['close'] > self.anchor_h and bar['close'] > curr_ema:
                    logger.info(f"[{candle_time}] LONG Optimized Breakout confirmed!")
                    self.pending_entry = 'LONG'
                # SHORT: Breakout + Below EMA
                elif bar['close'] < self.anchor_l and bar['close'] < curr_ema:
                    logger.info(f"[{candle_time}] SHORT Optimized Breakout confirmed!")
                    self.pending_entry = 'SHORT'

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
        if success:
            logger.info(f"Entered {self.pending_entry} @ {price} | SL: {sl:.2f} | Tgt: {target:.2f}")

    async def on_tick(self, tick: Dict[str, Any]):
        if self.state.position is None: return
        
        price = tick['price']
        curr_time = tick['time']
        
        # Risk Management: Exit checks
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
        if curr_time >= time(14, 30):
            self.executor.execute_exit(price, "EOD", curr_time)
