import logging

logger = logging.getLogger(__name__)

class Notifier:
    """
    Subsystem for external alerts (Telegram, Discord, Slack)
    """
    def __init__(self):
        pass
        
    def send(self, message: str):
        # Stub for actual webhook logic
        logger.info(f"🔔 [NOTIFICATION]: {message}")
