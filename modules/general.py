import database
from .currency import _add_money
from variables import VOTE_REWARD


async def donate(client, message, *args):
    await message.channel.send("""
Donate feature not yet enabled. Thanks for asking!
    """)


async def creator(client, message, *args):
    await message.channel.send("""
Bot created by RandomGhost#5990. Ask him for new features/bugs!
    """)


async def vote_bot(client, message, *args):
    await message.channel.send("Feature disabled for now.")
    return
    await message.channel.send("""
Vote for this bot and then claim your reward with `p!claimreward`. Thanks for voting!
Vote URL: <todo: add url>
You can vote once every 24 hours.
    """)


async def claim_rewards(client, message, *args):
    await message.channel.send("Feature disabled for now.")
    return
    if False:
        coins = VOTE_REWARD
        await message.channel.send("Thanks for voting! Here, have some coins.")
        engine = await database.prepare_engine()
        await _add_money(engine, message.author, coins)
        await message.channel.send(
            "{0} has got {1} coins. :thumbsup:".format(message.author.name, coins))
    else:
        await message.channel.send("""
You have not yet voted or it has not been 24 hours.
Vote with `p!vote` and then claim your rewards.
        """)

general_functions = {
    'vote': (vote_bot, "Vote for this bot."),
    'claimreward': (claim_rewards, "Claim your voting rewards."),
    'donate': (donate, "Donate money to this bot to keep it running UwU."),
    'creator': (creator, "Get to know the creator of this bot. And annoy him to fix bugs.")
}
