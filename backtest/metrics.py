def calculate_metrics(state, logging):
    logger = logging.getLogger(__name__)
    logger.info("-" * 50)
    logger.info("      EVENT-DRIVEN BACKTEST RESULTS")
    logger.info("-" * 50)
    logger.info(f"Total Trades   : {state.total_trades}")
    logger.info(f"Net Realized   : Rs. {state.realized_pnl:,.2f}")
    logger.info("-" * 50)
