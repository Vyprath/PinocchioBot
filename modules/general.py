import database
import dborg
import datetime
from .currency import _add_money
from variables import VOTE_REWARD, PREFIX


async def donate(client, message, *args):
    await message.channel.send("""
Please go to this site to donate: https://www.patreon.com/RandomGhost
Thanks!
    """)


async def invite(client, message, *args):
    await message.channel.send("""
Bot invite link: https://discordbots.org/bot/506878658607054849
    """)


async def creator(client, message, *args):
    await message.channel.send("""
Bot created by RandomGhost#5990. Ask him for new features/bugs!
    """)


async def vote_bot(client, message, *args):
    await message.channel.send("""
Vote for this bot and then claim your reward with `{0}claimreward`.
Vote URL: https://discordbots.org/bot/506878658607054849/vote
You can vote once every 12 hours.
You get 2x rewards for voting on weekends.
    """.format(PREFIX))


async def claim_rewards(client, message, *args):
    voted = await dborg.dbl_api.has_voted(message.author.id)
    db_verified = False
    engine = await database.prepare_engine()
    async with engine.acquire() as conn:
        fetch_query = database.Member.select().where(
            database.Member.c.member == message.author.id
        ).where(
            database.Member.c.guild == message.guild.id
        )
        cursor = await conn.execute(fetch_query)
        member = await cursor.fetchone()
        last_reward = member[database.Member.c.last_reward]
        if last_reward is None:
            db_verified = True
        else:
            if ((datetime.datetime.now() - last_reward).days > 1 or
                    (datetime.datetime.now() - last_reward).seconds//3600 > 12):
                db_verified = True
            else:
                db_verified = False
    if voted and db_verified:
        await message.channel.send("Thanks for voting! Here, have some coins.")
        coins = VOTE_REWARD
        is_weekend = await dborg.dbl_api.is_weekend()
        if is_weekend:
            coins *= 2
            await message.channel.send("Thanks for voting on weekend! You get 2x coins.")
        engine = await database.prepare_engine()
        async with engine.acquire() as conn:
            update_query = database.Member.update().where(
                database.Member.c.member == message.author.id
            ).where(
                database.Member.c.guild == message.guild.id
            ).values(last_reward=datetime.datetime.now().isoformat())
            await conn.execute(update_query)
        await _add_money(engine, message.author, coins)
        await message.channel.send(
            "{0} has got {1} coins. :thumbsup:".format(message.author.name, coins))
    else:
        await message.channel.send("""
You have not yet voted or it has not been 12 hours.
Vote with `{0}vote` and then claim your rewards.
        """.format(PREFIX))

general_functions = {
    'vote': (vote_bot, "Vote for this bot."),
    'claimreward': (claim_rewards, "Claim your voting rewards."),
    'donate': (donate, "Donate money to this bot to keep it running UwU."),
    'creator': (creator, "Get to know the creator of this bot. And annoy him to fix bugs."),
    'invite': (invite, "Get the invite link for the bot.")
}
