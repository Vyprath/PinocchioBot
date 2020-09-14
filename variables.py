import os

from aiohttp import BasicAuth
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Core
TOKEN = os.getenv("TOKEN")
assert TOKEN is not None, "The TOKEN environmental variable is not set."
PREFIX = os.getenv("PREFIX", "p!")
LOG_BUFFER = os.getenv("LOG_BUFFER", 30)
LOG_WAIT_MAX_SEC = os.getenv("LOG_WAIT_MAX_SEC", 30.0)
LOG_FILE = os.getenv("LOG_FILE")  # None to disable.
DEV_MODE = os.getenv("DEV_MODE", False)

# Proxy
PROXY = None
PROXY_AUTH = None
proxy_str = os.getenv("PROXY")
if proxy_str:
    proxy_parts = proxy_str.split("@")
    PROXY = proxy_parts[0]
    if len(proxy_parts) == 2:
        username, password = proxy_parts[1].split(":")
        PROXY_AUTH = BasicAuth(username, password)

# Database
DATABASE_URL = os.getenv("DATABASE_URL")
assert DATABASE_URL is not None, "The DATABASE_URL environmental variable is not set."

# Bot
SELL_WAIFU_DEPRECIATION = os.getenv("SELL_WAIFU_DEPRECIATION", 0.6)
FREE_MONEY_SPAWN_LIMIT = os.getenv("FREE_MONEY_SPAWN_LIMIT", 70)
DAILIES_AMOUNT = os.getenv("DAILIES_AMOUNT", 300)
VOTE_REWARD = os.getenv("VOTE_REWARD", 500)
DAILIES_DATE = os.getenv("DAILIES_DATE")
DONATOR_TIER_1 = os.getenv("DONATOR_TIER_1", 1)
DONATOR_TIER_2 = os.getenv("DONATOR_TIER_2", 2)
DEV_TIER = os.getenv("DEV_TIER", 5)
ROLL_INTERVAL = os.getenv("ROLL_INTERVAL", 3 * 3600)  # seconds
PRICE_CUT = os.getenv("PRICE_CUT", 0.08)  # TODO: what?

# Music
MUSIC_CACHE_DIR = os.getenv("MUSIC_CACHE_DIR", "./cache/")

# APIs
DBL_TOKEN = os.getenv("DBL_TOKEN")  # None to disable.
FILE_UPLOAD_TOKEN = os.getenv("FILE_UPLOAD_TOKEN")  # None to disable.
NOFLYLIST_TOKEN = os.getenv("NOFLYLIST_TOKEN")  # None to disable.
TRACE_MOE_TOKEN = os.getenv("TRACE_MOE_TOKEN")  # None to disable.
TENOR_API_TOKEN = os.getenv("TENOR_API_TOKEN")
DISCOIN_TOKEN = os.getenv("DISCOIN_TOKEN")  # None to disable.
DISCOIN_SELF_CURRENCY = os.getenv("DISCOIN_SELF_CURRENCY", "PIC")


# Dynamic (loaded/modified during runtime)
noflylist = []
DISCOIN_CLIENT = None
