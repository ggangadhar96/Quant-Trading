import pandas as pd
import numpy as np

def calculate_pivots(df: pd.DataFrame, high_col='High', low_col='Low', close_col='Close'):
    """
    Calculates Floor/Standard Camarilla Pivot variants.
    """
    pp = (df[high_col] + df[low_col] + df[close_col]) / 3
    r1 = pp + (pp - df[low_col])
    s1 = pp - (df[high_col] - pp)
    r2 = pp + (df[high_col] - df[low_col])
    s2 = pp - (df[high_col] - df[low_col])
    r3 = df[high_col] + 2 * (pp - df[low_col])
    s3 = df[low_col] - 2 * (df[high_col] - pp)
    
    return [pp.iloc[-1], r1.iloc[-1], s1.iloc[-1], r2.iloc[-1], s2.iloc[-1], r3.iloc[-1], s3.iloc[-1], df[high_col].iloc[-1], df[low_col].iloc[-1]]

def calculate_ema(df: pd.DataFrame, period: int, col='Close'):
    return df[col].ewm(span=period, adjust=False).mean()

def calculate_atr(df: pd.DataFrame, period=14):
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    return true_range.rolling(period).mean()
