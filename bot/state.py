class BotState:
    """
    Tracks the current live state of the bot.
    Independent of strategy logic or mode (live/backtest).
    """
    def __init__(self):
        self.position = None  # None, 'LONG', 'SHORT'
        self.entry_px = 0.0
        self.target_px = 0.0
        self.sl_px = 0.0
        self.qty = 0
        self.symbol = None
        self.realized_pnl = 0.0
        self.total_trades = 0
        
    def open_position(self, side: str, px: float, target: float, sl: float, qty: int = 0, symbol: str = None):
        self.position = side
        self.entry_px = px
        self.target_px = target
        self.sl_px = sl
        self.qty = qty
        self.symbol = symbol
        
    def close_position(self, exit_px: float):
        if self.position == 'LONG':
            self.realized_pnl += (exit_px - self.entry_px)
        elif self.position == 'SHORT':
            self.realized_pnl += (self.entry_px - exit_px)
            
        self.total_trades += 1
        self.position = None
        self.entry_px = 0.0
        self.target_px = 0.0
        self.sl_px = 0.0
        self.qty = 0
        self.symbol = None
