# 📈 Quant Trading Bot - God-Tier Architecture

A modular, zero-drift trading bot for Nifty 50, supporting Backtesting, Dry-Running, and Live Execution via Upstox API V3.

## 🚀 Quick Start

### 1. Requirements
Ensure you have the dependencies installed:
```bash
pip install -r requirements.txt
```

### 2. Configuration
Update `config.yaml` to set your instrument and strategy parameters.
Update `.env` with your Upstox API keys and Telegram tokens.

### 3. Running the Bot

**Backtest Mode (6 Months Nifty Data):**
```bash
python main.py --mode backtest --strategy v2.1
```

**Dry-Run Mode (Live Data, No Real Money):**
```bash
python main.py --mode dryrun --strategy v2.1
```

**Live Mode (⚠️ Use with Caution):**
```bash
python main.py --mode live --strategy v2.1
```

### 2. Strategy Selection
You can choose which logic the bot follows:
*   `v2`: Original Three-Candle Pivot Breakout (Fixed SL).
*   `v2.1`: **(Recommended)** Optimized Three-Candle with 200 EMA + ATR Risk.
*   `vwap`: Trend-following based on VWAP crossings and RSI confirmation.
*   `cpr`: Structural trading using Central Pivot Range (CPR) breakouts.

Run with:
```bash
python main.py --mode dryrun --strategy vwap
```
## 🔔 Notifications
Enable Telegram notifications by adding these to your `.env`:
- `TELEGRAM_BOT_TOKEN`: Get this from [@BotFather](https://t.me/BotFather) by using `/newbot`.
- `TELEGRAM_CHAT_ID`: Get this from [@userinfobot](https://t.me/userinfobot) by sending any message to it.

## 📊 Analysis
Open `notebooks/backtest_analysis.ipynb` in Cursor/VSCode for visual PnL charts and detailed trade tracking.
