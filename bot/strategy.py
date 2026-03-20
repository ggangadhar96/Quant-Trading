from datetime import time
import logging
from bot.base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class ThreeCandleV2Live(BaseStrategy):
    def __init__(self, instrument_key, pivot_levels, executor):
        super().__init__(name="ThreeCandleV2Live", executor=executor)
        self.instrument_key = instrument_key
        self.pivot_levels = sorted(pivot_levels)
        
        self.anchor_h = None
        self.anchor_l = None
        self.inside_count = 0
        self.pending_entry = None
        self.entry_trigger_px = None

    async def on_bar(self, bar):
        """ Runs every 15 minutes when a candle fully closes. """
        candle_dt = bar['time']
        candle_time = candle_dt.time()
        
        # 1. Phase 1: Anchor (09:15-09:30)
        if candle_time == time(9, 15):
            self.anchor_h = bar['high']
            self.anchor_l = bar['low']
            logger.info(f"[{candle_time}] Anchor Set! H: {self.anchor_h}, L: {self.anchor_l}")
            return
            
        if self.anchor_h is None: return
        
        # Trigger Pending Entry
        if self.pending_entry:
            await self._execute_entry(bar['open'], candle_time)
            self.pending_entry = None
            
        # 2. Phase 2: Compression Count (09:30-10:15)
        if time(9, 30) <= candle_time < time(10, 15):
            if bar['high'] < self.anchor_h and bar['low'] > self.anchor_l:
                self.inside_count += 1
                logger.info(f"[{candle_time}] Inside Candle! Total: {self.inside_count}")
            return
            
        # 3. Phase 3: Breakout Monitoring (10:15+)
        if candle_time >= time(10, 15) and self.state.position is None and self.pending_entry is None:
            if self.inside_count < 3: return # Requirement for setup
            
            # Breakout Confirmation
            if bar['close'] > self.anchor_h:
                logger.info(f"[{candle_time}] LONG Breakout confirmed! Preparing entry...")
                self.pending_entry = 'LONG'
            elif bar['close'] < self.anchor_l:
                logger.info(f"[{candle_time}] SHORT Breakout confirmed! Preparing entry...")
                self.pending_entry = 'SHORT'
                
    async def on_tick(self, tick):
        """ Runs on every raw price tick to handle intra-bar execution checks. """
        curr_time = tick['time']
        candle = tick['candle'] # The current forming candle for intra-bar High/Low checks
        
        if self.state.position:
            await self._check_exit(candle, curr_time)

    async def _execute_entry(self, open_px, candle_time):
        side = 'LONG' if self.pending_entry == 'LONG' else 'SHORT'
        self.entry_trigger_px = open_px
        
        target_px = self._get_target(open_px, self.pending_entry)
        sl_px = self.anchor_l if self.pending_entry == 'LONG' else self.anchor_h
        
        self.executor.execute_entry(
            symbol=self.instrument_key,
            side=side, # E.g., 'LONG', which executes a BUY
            qty=self.risk.lot_size,
            price=open_px,
            target=target_px,
            sl=sl_px,
            timestamp=candle_time
        )
            
    async def _check_exit(self, candle, curr_time):
        if self.state.position == 'LONG':
            if candle['low'] <= self.state.sl_px:
                self.executor.execute_exit(self.state.sl_px, "SL HIT", curr_time)
                return
            elif candle['high'] >= self.state.target_px:
                self.executor.execute_exit(self.state.target_px, "TARGET HIT", curr_time)
                return
                
        elif self.state.position == 'SHORT':
            if candle['high'] >= self.state.sl_px:
                self.executor.execute_exit(self.state.sl_px, "SL HIT", curr_time)
                return
            elif candle['low'] <= self.state.target_px:
                self.executor.execute_exit(self.state.target_px, "TARGET HIT", curr_time)
                return
                
        if curr_time >= time(14, 30):
            # Square off
            self.executor.execute_exit(candle['close'], "EOD", curr_time)

    def _get_target(self, px, side):
        if side == 'LONG':
            for lvl in self.pivot_levels:
                if lvl > px: return lvl
            return self.pivot_levels[-1]
        else:
            for lvl in reversed(self.pivot_levels):
                if lvl < px: return lvl
            return self.pivot_levels[0]
