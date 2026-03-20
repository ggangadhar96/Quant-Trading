def calculate_metrics(state, logging, lot_size=1):
    logger = logging.getLogger(__name__)
    logger.info("-" * 50)
    logger.info("      EVENT-DRIVEN BACKTEST RESULTS")
    logger.info("-" * 50)
    logger.info(f"Total Trades   : {state.total_trades}")
    logger.info(f"Net Points     : {state.realized_pnl:,.2f}")
    logger.info(f"Net PnL (Rs.)  : {state.realized_pnl * lot_size:,.2f}")
    logger.info("-" * 50)
