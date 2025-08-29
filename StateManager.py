import json
import os
from EDlogger import logger

STATE_FILE = 'wing_mining_state.json'

def save_state(state):
    """Saves the current state of the wing mining to a file."""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=4)
        logger.info(f"Wing mining state saved to {STATE_FILE}")
    except Exception as e:
        logger.error(f"Error saving wing mining state: {e}")

def load_state():
    """Loads the wing mining state from a file."""
    if not os.path.exists(STATE_FILE):
        return None
    
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        logger.info(f"Wing mining state loaded from {STATE_FILE}")
        return state
    except Exception as e:
        logger.error(f"Error loading wing mining state: {e}")
        return None

def clear_state():
    """Clears the saved wing mining state."""
    if os.path.exists(STATE_FILE):
        try:
            os.remove(STATE_FILE)
            logger.info(f"Cleared wing mining state file: {STATE_FILE}")
        except Exception as e:
            logger.error(f"Error clearing wing mining state: {e}")
