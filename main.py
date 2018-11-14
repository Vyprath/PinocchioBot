import discord
import logging
import asyncio
import variables
import database
import requests
import json
from modules import message_resolve
from music import functions


logging.basicConfig(level=logging.INFO)
loop = asyncio.get_event_loop()
loop.create_task(database.prepare_tables())
client = discord.Client(
    loop=loop,
    activity=discord.Game(name="idk what"))
tenor_anon_id_request = requests.get(variables.GET_ANON_ID_URL)
if tenor_anon_id_request.status_code == 200:
    variables.GIF_ANON_ID = json.loads(tenor_anon_id_request.content)['anon_id']
else:
    raise Exception("Tenor not working.")


@client.event
async def on_ready():
    logging.info("Logged in as {0} - {1}.".format(client.user.name, client.user.id))
    await database.make_member_profile(client.get_all_members(), client.user.id)


@client.event
async def on_message(message):
    await database.make_guild_entry(client.guilds)
    await message_resolve(client, message, variables.PREFIX)


@client.event
async def on_member_join(member):
    await database.make_member_profile([member], client.user.id)


@client.event
async def on_guild_join(guild):
    await database.make_guild_entry([guild])
    await database.make_member_profile(guild.members, client.user.id)


@client.event
async def on_voice_state_update(member, before, after):
    await functions.on_voice_state_update(member, before, after)

client.run(variables.TOKEN)
