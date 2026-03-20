import pandas as pd
import matplotlib.pyplot as plt
import sys
import os
import argparse
import asyncio
import yaml

# Add current dir to path
sys.path.append(os.getcwd())

from main import STRATEGY_MAP
from backtest.engine import BacktestEngine

async def generate_plot(strategy_name, csv_path):
    print(f"Running backtest for {strategy_name} to generate plot...")
    
    with open("config.yaml", "r") as f:
        full_config = yaml.safe_load(f)
    
    str_cfg = full_config['strategy']
    selected_strategy = STRATEGY_MAP[strategy_name]
    
    engine = BacktestEngine(selected_strategy, str_cfg['instrument'], csv_path, str_cfg['pivot_levels'])
    # Pass config to backtest strategy
    engine.strategy = selected_strategy(str_cfg['instrument'], str_cfg['pivot_levels'], engine.executor, config=str_cfg)
    await engine.run()
    
    history = engine.executor.state.trade_history
    if not history:
        print("No trades found to plot.")
        return

    df_trades = pd.DataFrame(history)
    print(f"Trade history sample 'exit_time' types: {type(df_trades['exit_time'].iloc[0])}")
    
    # Use exit_time for plotting the PnL curve
    # Use errors='coerce' to avoid crashing, and handle mixed types
    df_trades['exit_time_dt'] = pd.to_datetime(df_trades['exit_time'], errors='coerce')
    
    # If coercion failed, it might be because they were already time objects 
    # (though in backtest they should be datetime). Let's be extra safe:
    if df_trades['exit_time_dt'].isna().any():
        print("Warning: Some exit_times could not be converted. Using index as proxy.")
        df_trades['plot_time'] = df_trades.index
    else:
        df_trades['plot_time'] = df_trades['exit_time_dt']

    df_trades['cumulative_pnl'] = df_trades['pnl'].cumsum()
    
    plt.figure(figsize=(12, 6))
    plt.plot(df_trades['plot_time'], df_trades['cumulative_pnl'], marker='o', linestyle='-', color='blue', label='Equity Curve')
    plt.title(f"Equity Curve - {strategy_name.upper()} Strategy")
    plt.xlabel("Time")
    plt.ylabel("Cumulative PnL (Points)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    output_path = f"backtest_{strategy_name}_plot.png"
    plt.savefig(output_path)
    print(f"Graph saved to {output_path}")
    plt.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", default="vwap")
    parser.add_argument("--csv", default="data/csv/NIFTY50_15min_6months.csv")
    args = parser.parse_args()
    
    asyncio.run(generate_plot(args.strategy, args.csv))
