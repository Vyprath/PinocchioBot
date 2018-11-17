import database
import dborg
import datetime
import discord
from discord.utils import get
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


async def poll(client, message, *args):
    if len(args) < 3:
        await message.channel.send("""
Usage: {0}poll \"Title of Poll\" \"Option 1\" \"Option 2\" ["Option 3"...]
Remember to keep number options below or equal to 10.
        """.format(PREFIX))
        return
    title = args[0]
    options = list(args[1:])
    if len(options) > 10:
        options[9] = ' '.join(options[9:])
        options = options[:10]
    desc = ""
    num_to_emote = {
        0: 'zero', 1: 'one', 2: 'two', 3: 'three', 4: 'four',
        5: 'five', 6: 'six', 7: 'seven', 8: 'eight', 9: 'nine', 10: 'keycap_ten'}
    num_to_uni_emote = {
        0: '0⃣', 1: '1⃣', 2: '2⃣', 3: '3⃣', 4: '4⃣',
        5: '5⃣', 6: '6⃣', 7: '7⃣', 8: '8⃣', 9: '9⃣', 10: '🔟'}
    for i, opt in enumerate(options):
        desc += ":{0}: : {1}\n".format(num_to_emote[i], opt)
    embed = discord.Embed(title=title, color=0x325fa1, description=desc)
    embed.set_footer(
        text="Poll made by: {0}#{1}".format(message.author.name, message.author.discriminator),
        icon_url=message.author.avatar_url)
    msg = await message.channel.send(embed=embed)
    for i, _ in enumerate(options):
        await msg.add_reaction(num_to_uni_emote[i])


general_functions = {
    'vote': (vote_bot, "Vote for this bot."),
    'claimreward': (claim_rewards, "Claim your voting rewards."),
    'donate': (donate, "Donate money to this bot to keep it running UwU."),
    'creator': (creator, "Get to know the creator of this bot. And annoy him to fix bugs."),
    'invite': (invite, "Get the invite link for the bot."),
    'poll': (poll, "Create a reactions poll."),
}
