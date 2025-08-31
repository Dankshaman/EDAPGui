import requests
from EDlogger import logger

EMOJI_MAP = {
    # General Status & Bot Control
    "Bot Online": "🟢",
    "Bot Offline": "🔴",
    "Session Started": "▶️",
    "Session Ended": "⏹️",
    "Warning:": "⚠️",
    "Error:": "❌",
    "CRITICAL FAILURE": "💀",
    "Info:": "ℹ️",
    "Thinking/Calculating": "🤔",
    "Waiting/Idle": "⏳",
    "Task Complete": "✅",
    "Goal Achieved": "🎉",
    "start": "▶️",
    "stop": "⏹️",
    "assist": "▶️",
    "success": "✅",
    "complete": "✅",

    # Travel & Navigation
    "Route Plotted": "🗺️",
    "Next Waypoint": "📍",
    "FSD Jump": "✨",
    "Exiting Hyperspace": "💫",
    "Supercruise": "⏩",
    "Approaching Star": "☀️",
    "Fuel Scooping": "⛽",
    "jump": "✨",
    "waypoint": "📍",
    "route": "🗺️",
    "disengage": "💫",
    "align": "🧭",


    # Station & Docking
    "Requesting Docking": "📡",
    "Docking Granted": "👍",
    "Docking Denied": "👎",
    "Docking": "🛬",
    "Landed": "⚓️",
    "Launching": "🛫",
    "Repairing": "🔧",
    "Refueling": "⛽",
    "Restocking": "🔫",
    "docking": "🛬",
    "undock": "🛫",
    "landed": "⚓️",
    "station": "🏟️",

    # Trading & Commerce
    "Analyzing Market": "📈",
    "Trade Found": "💡",
    "Buying Goods": "🛒",
    "Loading Cargo": "📥",
    "Selling Goods": "💵",
    "Unloading Cargo": "📤",
    "Cargo Hold Status": "📦",
    "market": "📈",
    "buy": "🛒",
    "sell": "💵",
    "trade": "💡",
    "cargo": "📦",

    # Ship Status & Events
    "Interdiction Detected": "🧲",
    "Escaped Interdiction": "💨",
    "Submitted to Interdiction": "🏳️",
    "interdiction": "🧲",

    # Missions & Contracts
    "Mission Accepted": "📜",
    "Target Acquired": "🎯",
    "Mission Complete": "🏁",
    "mission": "📜",

    # Sourcing, Delivery & Rewards
    "Commodity Sourced": "🎁",
    "Delivering Mission Cargo": "➡️",
    "commodity": "🎁",

    # Exploration & Cartography
    "Discovery Scan": "📢",
    "Full Spectrum Scan": "📡",
    "Detailed Surface Scan": "🌐",
    "scan": "📡",

    # Fleet Carrier Management
    "Fleet Carrier Jump": "🚢",
    "Refueling Carrier": "⛽",
    "Carrier Finances": "🏦",
    "Docked at Carrier": "⚓",
    "Managing Services": "⚙️",
    "fleet carrier": "🚢",
    "carrier": "🚢",
    
    # Wing Mining
    "Wing Mining": "⛏️",
    "mining": "⛏️",

    # Other
    "calibrate": "🛠️",
    "calibration": "🛠️",
    "config": "⚙️",
    "settings": "⚙️",
}

class DiscordBot:
    def __init__(self, webhook_url, user_id=None):
        self.webhook_url = webhook_url
        self.user_id = user_id
        self.mention_keywords = []
        try:
            with open("discord_mention_keywords.txt", "r") as f:
                self.mention_keywords = [line.strip().lower() for line in f if line.strip()]
        except FileNotFoundError:
            logger.warning("discord_mention_keywords.txt not found. No user mentions will be sent.")

    def add_emoji(self, message):
        lower_message = message.lower()
        # Sort keywords by length descending to match more specific keywords first
        sorted_keywords = sorted(EMOJI_MAP.keys(), key=len, reverse=True)
        for keyword in sorted_keywords:
            if keyword.lower() in lower_message:
                return f"{EMOJI_MAP[keyword]} {message}"
        return f"ℹ️ {message}"

    def send_message(self, message):
        if not self.webhook_url:
            return

        content = self.add_emoji(message)

        # Check for keywords to determine if a mention should be added
        lower_message = message.lower()
        
        should_mention = False
        for keyword in self.mention_keywords:
            if keyword in lower_message:
                should_mention = True
                break

        if self.user_id and should_mention:
            content = f"<@{self.user_id}> {content}"

        payload = {
            "content": content
        }

        try:
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()  # Raise an exception for bad status codes
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Discord message: {e}")
