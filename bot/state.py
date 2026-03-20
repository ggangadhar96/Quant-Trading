from typing import Optional, List, Dict, Any

class BotState:
    """
    Tracks the current live state of the bot.
    Independent of strategy logic or mode (live/backtest).
    """
    def __init__(self):
        self.position: Optional[str] = None  # None, 'LONG', 'SHORT'
        self.entry_px: float = 0.0
        self.target_px: float = 0.0
        self.sl_px: float = 0.0
        self.qty: int = 0
        self.symbol: Optional[str] = None
        self.realized_pnl: float = 0.0
        self.total_trades: int = 0
        self.trade_history: List[Dict[str, Any]] = []
        
    def open_position(self, side: str, px: float, target: float, sl: float, qty: int = 0, symbol: Optional[str] = None):
        self.position = side
        self.entry_px = px
        self.target_px = target
        self.sl_px = sl
        self.qty = qty
        self.symbol = symbol
        
    def close_position(self, exit_px: float):
        pnl_pts = 0.0
        if self.position == 'LONG':
            pnl_pts = (exit_px - self.entry_px)
        elif self.position == 'SHORT':
            pnl_pts = (self.entry_px - exit_px)
            
        self.realized_pnl += pnl_pts
        self.total_trades += 1
        
        # Record trade for analysis
        self.trade_history.append({
            'side': self.position,
            'entry': self.entry_px,
            'exit': exit_px,
            'pnl': pnl_pts,
            'symbol': self.symbol
        })
        
        self.position = None
        self.entry_px = 0.0
        self.target_px = 0.0
        self.sl_px = 0.0
        self.qty = 0
        self.symbol = None
