import requests
from EDlogger import logger

class DiscordBot:
    def __init__(self, webhook_url, user_id=None):
        self.webhook_url = webhook_url
        self.user_id = user_id

    def send_message(self, message):
        if not self.webhook_url:
            return

        content = message
        if self.user_id:
            content = f"<@{self.user_id}> {message}"

        payload = {
            "content": content
        }

        try:
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()  # Raise an exception for bad status codes
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Discord message: {e}")
