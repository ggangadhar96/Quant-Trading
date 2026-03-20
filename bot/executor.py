import logging
from bot.state import BotState
from bot.risk import RiskManager

logger = logging.getLogger(__name__)

class StrategyExecutor:
    """
    Routes orders from the Strategy to either the Live Broker, DryRun Logger, or Backtest Engine.
    Also seamlessly manages the BotState based on executed trades.
    """
    def __init__(self, mode: str, broker=None):
        self.mode = mode # 'live', 'dryrun', 'backtest'
        self.broker = broker
        self.state = BotState()
        self.risk = RiskManager()
        
    def execute_entry(self, symbol, side, qty, price, target, sl, timestamp):
        if not self.risk.can_trade(self.state.realized_pnl):
            return False
            
        # Build Upstox API standard payload
        upstox_payload = {
            "quantity": qty,
            "product": "I", # Intraday (or 'D' for Delivery)
            "validity": "DAY",
            "price": 0,
            "tag": "3CandleBot",
            "instrument_token": symbol,
            "order_type": "MARKET",
            "transaction_type": side.upper(), # 'BUY' or 'SELL'
            "disclosed_quantity": 0,
            "trigger_price": 0,
            "is_amo": False
        }
        
        if self.mode == 'live':
            logger.info(f"[LIVE] Executing Entry: {upstox_payload}")
            if self.broker:
                self.broker.place_order(upstox_payload)
        elif self.mode == 'dryrun':
            logger.info(f"[DRYRUN] Simulated Entry: {order_data}")
            
        self.state.open_position(side, price, target, sl, qty, symbol)
        return True

    def execute_exit(self, exit_px, exit_reason, timestamp):
        if self.state.position is None:
            return

        exit_side = 'SELL' if self.state.position == 'LONG' else 'BUY'
        
        upstox_payload = {
            "quantity": self.state.qty,
            "product": "I",
            "validity": "DAY",
            "price": 0,
            "tag": f"3CandleExit_{exit_reason}",
            "instrument_token": self.state.symbol,
            "order_type": "MARKET",
            "transaction_type": exit_side,
            "disclosed_quantity": 0,
            "trigger_price": 0,
            "is_amo": False
        }

        if self.mode == 'live':
            logger.info(f"[LIVE] EXIT ({exit_reason}) @ {exit_px}")
            if self.broker:
                self.broker.place_order(upstox_payload)
        elif self.mode == 'dryrun':
            logger.info(f"[DRYRUN] Simulated EXIT ({exit_reason}) @ {exit_px}")
            
        self.state.close_position(exit_px)
