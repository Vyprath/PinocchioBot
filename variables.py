import os

# Core
PREFIX = os.environ.get('PREFIX', 'p!')
TOKEN = os.environ.get('TOKEN')
DBL_TOKEN = os.environ.get('DBL_TOKEN')
CLIENT_ID = "506878658607054849"
if TOKEN is None:
    raise Exception('The TOKEN environmental variable is not set.')
if DBL_TOKEN is None:
    raise Exception('The DBL_TOKEN environmental variable is not set.')


# Database
DB_USERNAME = os.environ.get('DB_USERNAME')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME')
if DB_USERNAME is None or DB_NAME is None:
    raise Exception('Environmental variables for database not set')
ENGINE_URL = "postgresql://{0}:{1}@localhost:5432/{2}".format(DB_USERNAME, DB_PASSWORD, DB_NAME)


# GIF (tenor.com)
GIF_API_KEY = 'XV5HX3J1KYK7'
GIF_ANON_ID = ''  # Set in main.py during runtime.
GET_ANON_ID_URL = 'https://api.tenor.com/v1/anonid?key={}'.format(GIF_API_KEY)
def GIF_SEARCH_URL(term, inline=False):  # noqa
    return 'https://api.tenor.com/v1/random?q={0}&key={1}&limit={2}&anon_id={3}&media_filter=minimal'.format(  # noqa
        term, GIF_API_KEY, 1, GIF_ANON_ID)


# Bot
CUSTOM_ROLE_COST = 30000
SELL_WAIFU_DEPRECIATION = 0.6
FREE_MONEY_SPAWN_LIMIT = 70
DAILIES_AMOUNT = 300
VOTE_REWARD = 500

# APIs
ICNDB_RANDOM_JOKE_URL = "http://api.icndb.com/jokes/random"
DADJOKE_URL = "https://icanhazdadjoke.com"
CATFACT_URL = "https://catfact.ninja/fact"
LMGTFY_URL = "https://lmgtfy.com/?q="
UD_URL = "https://api.urbandictionary.com/v0/define?term="
