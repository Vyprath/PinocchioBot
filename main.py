import asyncio
import logging

import discord
import uvloop
from discoin import Client as Discoin

import database
import dborg
import variables
from log import start_logging
from modules import message_resolve
from modules.special_handlers import (
    blacklist_updater,
    discoin_watcher,
    send_on_member_join,
    send_on_member_leave,
)
from music import functions

if not variables.DEV_MODE:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    logging.basicConfig(level=logging.INFO)
else:
    logging.basicConfig(level=logging.DEBUG)

loop = asyncio.get_event_loop()

client = discord.AutoShardedClient(
    loop=loop,
    proxy=variables.PROXY,
    proxy_auth=variables.PROXY_AUTH,
    activity=discord.Game(
        name=f"{variables.PREFIX}help | Playing around in 100 servers"
    ),
)

loop.create_task(database.prepare_tables())

one_time_done = False


async def on_start(client):
    global one_time_done
    if one_time_done:
        return
    one_time_done = True

    cors = [start_logging()]

    if variables.DISCOIN_TOKEN:
        variables.discoin_client = Discoin(
            f"{variables.DISCOIN_TOKEN}", variables.DISCOIN_SELF_CURRENCY, loop=loop
        )
        cors.append(discoin_watcher(client))

    if variables.NOFLYLIST_TOKEN:
        cors.append(blacklist_updater())

    await asyncio.gather(*cors)


@client.event
async def on_ready():
    logging.info(f"Logged in as {client.user} - {client.user.id}.")
    await database.make_member_profile(client.get_all_members(), client.user.id)
    if variables.DBL_TOKEN:
        dborg.init_dbl(client)
        await dborg.dbl_api.update_stats()

    await on_start(client)


@client.event
async def on_message(message):
    if variables.DEV_MODE:
        await database.make_member_profile([message.author], client.user.id)
    await message_resolve(client, message, variables.PREFIX)


@client.event
async def on_member_join(member):
    await database.make_member_profile([member], client.user.id)
    await send_on_member_join(member)


@client.event
async def on_member_remove(member):
    await database.make_member_profile([member], client.user.id)
    await send_on_member_leave(member)


@client.event
async def on_guild_join(guild):
    await database.make_guild_entry([guild])
    await database.make_member_profile(guild.members, client.user.id)
    await dborg.dbl_api.update_stats()


@client.event
async def on_guild_remove(guild):
    await dborg.dbl_api.update_stats()


@client.event
async def on_voice_state_update(member, before, after):
    await functions.on_voice_state_update(member, before, after)


if __name__ == "__main__":
    client.run(variables.TOKEN)
