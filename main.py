import discord
import logging
import asyncio
from modules import message_resolve
from variables import TOKEN
import database


logging.basicConfig(level=logging.INFO)
COMMAND_PREFIX = "!"
loop = asyncio.get_event_loop()
loop.create_task(database.prepare_tables())
client = discord.Client(loop=loop)


@client.event
async def on_ready():
    logging.info("Logged in as {0} - {1}.".format(client.user.name, client.user.id))
    await database.make_member_profile(client.get_all_members(), client.user.id)


@client.event
async def on_message(message):
    await message_resolve(client, message, COMMAND_PREFIX)


@client.event
async def on_member_join(member):
    await database.make_member_profile([member], client.user.id)

client.run(TOKEN)
