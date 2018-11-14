import logging
import variables
import dbl
import discord
from urllib.parse import urlencode


class DiscordBotsOrgAPI:
    def __init__(self, bot):
        self.bot = bot
        self.token = variables.DBL_TOKEN
        self.dblpy = dbl.Client(self.bot, self.token)
        self.bot.loop.create_task(self.update_stats())
        self.client_id = variables.CLIENT_ID

    async def update_stats(self):
        try:
            await self.dblpy.http.post_server_count(
                self.client_id, len(self.bot.guilds), None, None)
            resp = await self.dblpy.get_server_count(self.client_id)
            if 'server_count' in resp:
                count = resp['server_count']
            else:
                count = 0
            activity = discord.Game(
                name="{0}help | Playing around in {1} servers".format(
                    variables.PREFIX, count))
            await self.bot.change_presence(activity=activity)
        except Exception as e:
            logging.exception('Failed to post server count\n{}: {}'.format(type(e).__name__, e))

    async def has_voted(self, user_id):
        try:
            params = {
                'userId': user_id
            }
            resp = await self.dblpy.http.request(
                'GET', '{0}/bots/{1}/check?'.format(self.dblpy.http.BASE, self.client_id)
                + urlencode(params))
            return bool(resp['voted'])
        except Exception as e:
            logging.exception('Failed to get votes\n{}: {}'.format(type(e).__name__, e))


dbl_api = None


def init_dbl(bot):

    global dbl_api
    dbl_api = DiscordBotsOrgAPI(bot)
