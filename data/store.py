from datetime import datetime, time
import logging

logger = logging.getLogger(__name__)

class DataStore:
    """
    In-memory OHLC cache.
    Aggregates raw ticks into time-bucketed candles (e.g., 15-minute bars)
    and dispatches them to the strategy.
    """
    def __init__(self, strategy, bucket_minutes=15):
        self.strategy = strategy
        self.bucket_minutes = bucket_minutes
        
        self.current_candle = None
        self.current_start = None
        
    async def process_tick(self, price: float, timestamp_ms: int):
        curr_datetime = datetime.fromtimestamp(timestamp_ms / 1000)
        curr_time = curr_datetime.time()
        
        minute = curr_datetime.minute
        bucket_start_min = (minute // self.bucket_minutes) * self.bucket_minutes
        bucket_start = curr_datetime.replace(minute=bucket_start_min, second=0, microsecond=0)
        
        if self.current_start is None or bucket_start > self.current_start:
            # We crossed into a new bucket. Publish the old candle if it exists.
            if self.current_candle:
                # Add the finalized time to the candle object
                self.current_candle['time'] = self.current_start.time()
                await self.strategy.on_bar(self.current_candle)
            
            # Start a new candle
            self.current_start = bucket_start
            self.current_candle = {'open': price, 'high': price, 'low': price, 'close': price}
        else:
            # Update the existing candle
            self.current_candle['high'] = max(self.current_candle['high'], price)
            self.current_candle['low'] = min(self.current_candle['low'], price)
            self.current_candle['close'] = price
        
        # Always dispatch the raw tick for intra-bar logic (like SL hits)
        await self.strategy.on_tick({'time': curr_time, 'price': price, 'candle': self.current_candle})
