class RiskManager:
    """
    Handles trading risk parameters like max daily loss and dynamic lot sizing.
    """
    def __init__(self, lot_size=25, max_daily_loss_inr=5000):
        self.lot_size = lot_size
        self.max_daily_loss_inr = max_daily_loss_inr
        
    def can_trade(self, realized_pnl_pts: float):
        """
        Check if we haven't hit the max daily loss circuit breaker.
        """
        current_pnl_inr = realized_pnl_pts * self.lot_size
        if current_pnl_inr <= -self.max_daily_loss_inr:
            print(f"[CIRCUIT BREAKER] Max Daily Loss Hit ({current_pnl_inr:.0f}). Trading Halted.")
            return False
        return True
