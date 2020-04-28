import discord
import logging
import asyncio
import variables
import database
import requests
import json
import dborg
from modules import message_resolve
from modules.special_handlers import (
    send_on_member_join,
    send_on_member_leave,
    discoin_watcher,
)
from music import functions
from discoin import Discoin
from log import start_logging
import uvloop


logging.basicConfig(level=logging.DEBUG)
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
loop = asyncio.get_event_loop()
loop.create_task(database.prepare_tables())

client = discord.AutoShardedClient(
    loop=loop,
    proxy=variables.PROXY,
    proxy_auth=variables.PROXY_AUTH,
    activity=discord.Game(
        name="{0}help | Playing around in 100 servers".format(variables.PREFIX)
    ),
)

tenor_anon_id_request = requests.get(variables.GET_ANON_ID_URL)
if tenor_anon_id_request.status_code == 200:
    variables.GIF_ANON_ID = json.loads(tenor_anon_id_request.content)["anon_id"]
else:
    raise Exception("Tenor not working.")


started = False


@client.event
async def on_ready():
    global started
    logging.info("Logged in as {0} - {1}.".format(client.user.name, client.user.id))
    # await database.make_member_profile(client.get_all_members(), client.user.id)
    if variables.DBL_TOKEN:
        dborg.init_dbl(client)
        await dborg.dbl_api.update_stats()

    if started:
        return
    started = True

    variables.discoin_client = Discoin(
        f"{variables.DISCOIN_AUTH_KEY}", "PIC", loop=loop
    )
    cors = [start_logging(), discoin_watcher(client)]
    await asyncio.gather(*cors)


@client.event
async def on_message(message):
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


client.run(variables.TOKEN)
