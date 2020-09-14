import logging

import dbl
import discord

import variables


class DiscordBotsOrgAPI:
    def __init__(self, bot):
        self.bot = bot
        self.token = variables.DBL_TOKEN
        self.dblpy = dbl.DBLClient(self.bot, self.token)
        self.bot.loop.create_task(self.update_stats())
        self.client_id = bot.user.id

    async def update_stats(self):
        try:
            await self.dblpy.post_guild_count()
            resp = await self.dblpy.get_guild_count()
            if "server_count" in resp:
                count = resp["server_count"]
            else:
                count = 0
            activity = discord.Game(
                name=f"{variables.PREFIX}help | Playing around in {count} servers"
            )
            await self.bot.change_presence(activity=activity)
        except Exception as e:
            logging.exception(
                "Failed to post server count\n%s: %s", type(e).__name__, e
            )

    async def has_voted(self, user_id):
        try:
            voted = await self.dblpy.get_user_vote(user_id)
            return voted
        except Exception as e:
            logging.exception(
                "Failed to get votes for %s \n%s: %s", user_id, type(e).__name__, e
            )

    async def is_weekend(self):
        try:
            weekend = await self.dblpy.get_weekend_status()
            return weekend
        except Exception as e:
            logging.exception(
                "Failed to check if weekend \n%s: %s", type(e).__name__, e
            )


DBL_API = None


def init_dbl(bot):

    global DBL_API
    DBL_API = DiscordBotsOrgAPI(bot)
