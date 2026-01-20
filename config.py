import logging
from dotenv import load_dotenv
import os

load_dotenv()

# Telegram Bot Token
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Logging configuration
logging.basicConfig(level=logging.INFO)

# Constants
MIN_UTC_OFFSET = -12
MAX_UTC_OFFSET = 14
