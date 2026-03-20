import pandas as pd
import numpy as np

def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average."""
    return prices.ewm(span=period, adjust=False).mean()

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_cpr(high_prev: float, low_prev: float, close_prev: float) -> dict:
    """Calculate Central Pivot Range (CPR) levels."""
    pivot = (high_prev + low_prev + close_prev) / 3
    bc = (high_prev + low_prev) / 2
    tc = (pivot - bc) + pivot
    
    # Ensure TC is top and BC is bottom (they can swap)
    return {
        'pivot': pivot,
        'tc': max(tc, bc),
        'bc': min(tc, bc)
    }

def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """Calculate VWAP. Resets daily if 'date' or 'time' with date is available."""
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    volume = df['volume'] if 'volume' in df.columns else pd.Series(1, index=df.index)
    
    # If we have dates, group by day to reset VWAP
    if 'time' in df.columns:
        dates = pd.to_datetime(df['time']).dt.date
        pv = typical_price * volume
        return pv.groupby(dates).cumsum() / volume.groupby(dates).cumsum()
    
    return (typical_price * volume).cumsum() / volume.cumsum()

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Average True Range."""
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr
