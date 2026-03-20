import logging
import os
import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class Notifier:
    """
    Subsystem for external alerts (Telegram, Discord, Slack)
    """
    def __init__(self):
        load_dotenv()
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = all([self.bot_token, self.chat_id])
        
        if not self.enabled:
            logger.warning("Telegram NOT enabled (Missing tokens in .env)")

    def send(self, message: str):
        logger.info(f"🔔 [NOTIFICATION]: {message}")
        if not self.enabled: return
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        try:
            response = requests.post(url, json=payload, timeout=5)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
