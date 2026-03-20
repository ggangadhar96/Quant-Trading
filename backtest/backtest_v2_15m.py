import pandas as pd
import numpy as np
from datetime import time
import matplotlib.pyplot as plt

def run_backtest_v2_15m(csv_path):
    print(f"Loading 15-minute data from {csv_path}...")
    df = pd.read_csv(csv_path)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df.set_index('Timestamp', inplace=True)
    df['date'] = df.index.date
    df['time'] = df.index.time
    
    # 1. Daily OHLC for Pivots
    daily = df.resample('1D').agg({
        'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'
    }).dropna()
    
    # 2. Parameters
    T_ANCHOR = time(9, 15)
    T_COUNT_START = time(9, 30)
    T_COUNT_END = time(10, 00)
    T_TRADE_START = time(10, 15)
    T_EXIT_LIMIT = time(14, 30)
    
    MIN_INSIDE = 3
    LOT_SIZE = 25
    BROKERAGE = 40
    
    trades = []
    
    # 3. Strategy Loop
    for tdate, day_df in df.groupby('date'):
        # Get Pivots
        prev = daily[daily.index.date < tdate]
        if prev.empty: continue
        prev = prev.iloc[-1]
        
        pp = (prev['High'] + prev['Low'] + prev['Close']) / 3
        pivot_levels = sorted([
            pp, 
            pp + (pp - prev['Low']), # R1
            pp - (prev['High'] - pp), # S1
            pp + (prev['High'] - prev['Low']), # R2
            pp - (prev['High'] - prev['Low']), # S2
            prev['High'] + 2 * (pp - prev['Low']), # R3
            prev['Low'] - 2 * (prev['High'] - pp), # S3
            prev['High'], # PDH
            prev['Low']   # PDL
        ])
        
        # Phase 1: Anchor Candle (09:15)
        anchor = day_df[day_df['time'] == T_ANCHOR]
        if anchor.empty: continue
        anchor_h = anchor['High'].iloc[0]
        anchor_l = anchor['Low'].iloc[0]
        
        # Phase 2: Inside Bar Count (09:30, 09:45, 10:00)
        inside_df = day_df[(day_df['time'] >= T_COUNT_START) & (day_df['time'] <= T_COUNT_END)]
        inside_count = 0
        for _, row in inside_df.iterrows():
            if row['High'] < anchor_h and row['Low'] > anchor_l:
                inside_count += 1
        
        if inside_count < MIN_INSIDE: continue
        
        # Phase 3: Trade Execution (Based on 15-min CLOSE)
        trade_df = day_df[day_df['time'] >= T_TRADE_START]
        pos = None
        entry_px, target_px, sl_px = 0, 0, 0
        entry_ts = None
        pending_entry = None
        
        for ts, row in trade_df.iterrows():
            if pos is None and pending_entry is None:
                # ENTRY CONFIRMATION: Wait for 15-MINUTE CLOSE
                if row['Close'] > anchor_h:
                    pending_entry = 'LONG'
                elif row['Close'] < anchor_l:
                    pending_entry = 'SHORT'
                    
            elif pending_entry:
                # EXECUTION: Enter at the OPEN of the next 15-min candle
                entry_px = row['Open']
                if pending_entry == 'LONG':
                    # Target selection
                    target_px = pivot_levels[-1]
                    for lvl in pivot_levels:
                        if lvl > entry_px: target_px = lvl; break
                    # SL matched to Pine Script anchor logic (low of anchor candle)
                    sl_px = anchor_l
                    pos, entry_ts = 'LONG', ts
                else:
                    # Target selection
                    target_px = pivot_levels[0]
                    for lvl in reversed(pivot_levels):
                        if lvl < entry_px: target_px = lvl; break
                    # SL matched to Pine Script anchor logic (high of anchor candle)
                    sl_px = anchor_h
                    pos, entry_ts = 'SHORT', ts
                    
                pending_entry = None
                
                # Check for same-candle Target / SL hit
                if pos == 'LONG':
                    if row['Low'] <= sl_px: # Pessimistic assumption - SL hit first
                        trades.append({'date': tdate, 'dir': 'LONG', 'res': 'SL', 'entry': entry_px, 'exit': sl_px, 'ts': ts})
                        break
                    elif row['High'] >= target_px:
                        trades.append({'date': tdate, 'dir': 'LONG', 'res': 'TARGET', 'entry': entry_px, 'exit': target_px, 'ts': ts})
                        break
                elif pos == 'SHORT':
                    if row['High'] >= sl_px: # Pessimistic assumption - SL hit first
                        trades.append({'date': tdate, 'dir': 'SHORT', 'res': 'SL', 'entry': entry_px, 'exit': sl_px, 'ts': ts})
                        break
                    elif row['Low'] <= target_px:
                        trades.append({'date': tdate, 'dir': 'SHORT', 'res': 'TARGET', 'entry': entry_px, 'exit': target_px, 'ts': ts})
                        break
                        
                if row['time'] >= T_EXIT_LIMIT:
                    trades.append({'date': tdate, 'dir': pos, 'res': 'EOD', 'entry': entry_px, 'exit': row['Close'], 'ts': ts})
                    break
            
            elif pos == 'LONG':
                # INTRA-CANDLE CHECKS using High/Low
                if row['Low'] <= sl_px:
                    trades.append({'date': tdate, 'dir': 'LONG', 'res': 'SL', 'entry': entry_px, 'exit': sl_px, 'ts': ts})
                    break
                elif row['High'] >= target_px:
                    trades.append({'date': tdate, 'dir': 'LONG', 'res': 'TARGET', 'entry': entry_px, 'exit': target_px, 'ts': ts})
                    break
                elif row['time'] >= T_EXIT_LIMIT:
                    trades.append({'date': tdate, 'dir': 'LONG', 'res': 'EOD', 'entry': entry_px, 'exit': row['Close'], 'ts': ts})
                    break
                    
            elif pos == 'SHORT':
                if row['High'] >= sl_px:
                    trades.append({'date': tdate, 'dir': 'SHORT', 'res': 'SL', 'entry': entry_px, 'exit': sl_px, 'ts': ts})
                    break
                elif row['Low'] <= target_px:
                    trades.append({'date': tdate, 'dir': 'SHORT', 'res': 'TARGET', 'entry': entry_px, 'exit': target_px, 'ts': ts})
                    break
                elif row['time'] >= T_EXIT_LIMIT:
                    trades.append({'date': tdate, 'dir': 'SHORT', 'res': 'EOD', 'entry': entry_px, 'exit': row['Close'], 'ts': ts})
                    break

    # 4. Summary
    if not trades: print("No trades triggered."); return
    res_df = pd.DataFrame(trades)
    res_df['pnl_pts'] = np.where(res_df['dir'] == 'LONG', res_df['exit'] - res_df['entry'], res_df['entry'] - res_df['exit'])
    res_df['pnl_inr'] = res_df['pnl_pts'] * LOT_SIZE - BROKERAGE
    res_df['cum_pnl'] = res_df['pnl_inr'].cumsum()
    
    # Calculate additional metrics
    gross_profit = res_df[res_df['pnl_inr'] > 0]['pnl_inr'].sum()
    gross_loss = abs(res_df[res_df['pnl_inr'] < 0]['pnl_inr'].sum())
    profit_factor = gross_profit / gross_loss if gross_loss != 0 else float('inf')
    
    peak = res_df['cum_pnl'].expanding(min_periods=1).max()
    drawdown = (res_df['cum_pnl'] - peak)
    max_drawdown = drawdown.min()
    
    print("-" * 50)
    print("      V2 STRATEGY BACKTEST (15-MIN DATA)")
    print("-" * 50)
    print(f"Total Trades  : {len(res_df)}")
    print(f"Win Rate      : {(len(res_df[res_df['pnl_inr'] > 0]) / len(res_df)) * 100:.2f}%")
    print(f"Net P&L       : Rs. {res_df['pnl_inr'].sum():,.2f}")
    print(f"Profit Factor : {profit_factor:.2f}")
    print(f"Max Drawdown  : Rs. {max_drawdown:,.2f}")
    print("-" * 50)
    print("Results Breakdown:")
    print(res_df.groupby('res')['pnl_inr'].count())
    
    plt.figure(figsize=(10,6)); plt.plot(res_df['cum_pnl'], marker='o'); plt.title('Equity Curve (15min V2)')
    plt.grid(True); plt.savefig('v2_15min_results.png')

if __name__ == "__main__":
    run_backtest_v2_15m('history/NIFTY50_15min_6months.csv')
