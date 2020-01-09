import database
import random
import string
import asyncio
import aiohttp
import time
import datetime
import json
import discord
from variables import FREE_MONEY_SPAWN_LIMIT, DAILIES_AMOUNT, PREFIX
from discoin import InternalServerError, BadRequest, WebTimeoutError
import variables


async def _fetch_wallet(engine, member):
    async with engine.acquire() as conn:
        fetch_query = database.Member.select().where(
            database.Member.c.member == member.id)
        cursor = await conn.execute(fetch_query)
        resp = await cursor.fetchone()
        if resp is None:
            return None
        else:
            return resp[database.Member.c.wallet]


async def _add_money(engine, member, amount):
    current_balance = await _fetch_wallet(engine, member)
    if current_balance is None:
        return None
    async with engine.acquire() as conn:
        update_query = database.Member.update().where(
            database.Member.c.member == member.id
        ).values(wallet=current_balance + amount)
        await conn.execute(update_query)
    return current_balance + amount


async def _remove_money(engine, member, amount):
    current_balance = await _fetch_wallet(engine, member)
    if current_balance is None:
        return None
    if current_balance - amount < 0:
        return False
    async with engine.acquire() as conn:
        update_query = database.Member.update().where(
            database.Member.c.member == member.id
        ).values(wallet=current_balance - amount)
        await conn.execute(update_query)
    return current_balance + amount


async def fetch_wallet(client, message, *args):
    engine = await database.prepare_engine()
    if len(message.mentions) == 0:
        wallet = await _fetch_wallet(engine, message.author)
        await message.channel.send(
            "You have `{0}` coins in your wallet."
            .format(wallet)
            )
    else:
        member = message.mentions[0]
        wallet = await _fetch_wallet(engine, member)
        await message.channel.send(
            "{1} has `{0}` coins in their wallet."
            .format(wallet, member.name)
            )


async def transfer_money(client, message, *args):
    engine = await database.prepare_engine()
    if len(args) != 2 or not args[1].isdigit() or len(message.mentions) != 1:
        await message.channel.send(
            "Correct command is: `{0}transfer-money <@user mention> <amount>`".format(PREFIX))
        return
    amount = int(args[1])
    to_transfer = message.mentions[0]
    wallet = await _fetch_wallet(engine, message.author)
    if wallet - amount < 0:
        await message.channel.send(
            "You do not have enough money to transfer! :angry:")
        return
    await _remove_money(engine, message.author, amount)
    await _add_money(engine, to_transfer, amount)
    await message.channel.send(
        "Done. :thumbsup:"
    )


async def dailies(client, message, *args):
    global DAILIES_DATE
    engine = await database.prepare_engine()
    async with engine.acquire() as conn:
        fetch_query = database.Member.select().where(
            database.Member.c.member == message.author.id
        )
        cursor = await conn.execute(fetch_query)
        member = await cursor.fetchone()
        last_dailies = member[database.Member.c.last_dailies]
        if last_dailies is not None:
            last_dailies = datetime.datetime.fromisoformat(str(last_dailies))
        fetch_query = database.Member.select().where(
                database.Member.c.member == message.author.id
            )
        cursor = await conn.execute(fetch_query)
        resp = await cursor.fetchall()
        member_tier = 0
        for m in resp:
            _t = m[database.Member.c.tier]
            if _t > member_tier:
                member_tier = _t
        now = datetime.datetime.now()
        if last_dailies is None or (now - last_dailies).days >= 1:
            update_query = database.Member.update().where(
                database.Member.c.member == message.author.id
            ).values(last_dailies=now.isoformat())
            await conn.execute(update_query)
            if member_tier >= variables.DONATOR_TIER_2:
                await _add_money(engine, message.author, DAILIES_AMOUNT * 4)
                await message.channel.send(
                    "Recieved {0} coins. 4 times the usual amount for being a donator! :smile:".format(DAILIES_AMOUNT * 4))
            elif member_tier >= variables.DONATOR_TIER_1:
                await _add_money(engine, message.author, DAILIES_AMOUNT * 2)
                await message.channel.send(
                    "Recieved {0} coins. Twice the usual amount for being a donator! :smile:".format(DAILIES_AMOUNT * 2))
            else:
                await _add_money(engine, message.author, DAILIES_AMOUNT)
                await message.channel.send("Recieved {0} coins. :thumbsup:".format(DAILIES_AMOUNT))
        else:
            next_reset = last_dailies + datetime.timedelta(days=1) - now
            tdelta_hours = (next_reset.seconds)//3600
            tdelta_mins = (next_reset.seconds)//60 - (tdelta_hours * 60)
            await message.channel.send(
                "Please wait {0:>02d} hours and {1:>02d} minutes more to get dailies.".format(
                    tdelta_hours, tdelta_mins
                ))


async def exchange(client, message, *args):
    if len(args) != 2 or not args[0].isdigit():
        await message.channel.send(f"""
Usage: `{PREFIX}exchange <coins> <currency>`
If you want to know more about this and supported currencies, use `{PREFIX}discoin`.
        """)
        return
    processing_msg = await message.channel.send("Processing Transaction...")
    amount = int(args[0])
    to = args[1].upper()
    try:
        transaction = await variables.discoin_client.create_transaction(to, amount, message.author.id)
    except (BadRequest, InternalServerError, WebTimeoutError) as e:
        await processing_msg.edit(content=f"""
Hit an error :exploding_head: {type(e).__name__}
Message: {e}
        """)
        return
    engine = await database.prepare_engine()
    await _remove_money(engine, message.author, amount)
    embed = discord.Embed(
        title="<:Discoin:357656754642747403> Exchange Successful!",
        description=f"""
Your Pino-coins are being sent via the top-secret Agent Wumpus. He usually delivers the coins within 5 minutes.
See `{PREFIX}discoin` for more info.
        """)
    embed.add_field(name="Pinocchio Coins (PIC) Exchanged", value=amount)
    embed.add_field(name=f"{to} To Recieve", value=transaction.payout)
    embed.add_field(
        name="Transaction Receipt", inline=False,
        value=f"[```{transaction.id}```](https://dash.discoin.zws.im/#/transactions/{transaction.id}/show)Keep this code in case Agent Wumpus fails to deliver the coins.")
    embed.set_footer(
        text=f"{message.author.name}#{message.author.discriminator}",
        icon_url=message.author.avatar_url_as(size=128))
    await processing_msg.edit(content=None, embed=embed)


free_money_channels = {}
passive_money_users = {}


async def free_money_handler(client, message):
    if message.author.id == client.user.id or message.author.bot:
        return
    now = time.monotonic()
    if message.author.id in passive_money_users.keys():
        last = passive_money_users[message.author.id]
        if now - last > 60:
            passive_money_users[message.author.id] = now
            engine = await database.prepare_engine()
            await _add_money(engine, message.author, random.randint(1, 5))
    else:
        passive_money_users.update({message.author.id: now})
    engine = await database.prepare_engine()
    async with engine.acquire() as conn:
        fetch_query = database.Guild.select().where(
            database.Guild.c.guild == message.guild.id
        )
        cursor = await conn.execute(fetch_query)
        resp = await cursor.fetchone()
        if resp is None:
            return
        coin_drop_enabled = resp[database.Guild.c.coin_drops]
    if not coin_drop_enabled:
        return
    N = FREE_MONEY_SPAWN_LIMIT
    try:
        e = free_money_channels[message.channel.id]
        if e != random.randint(1, N):
            return
        free_money_channels[message.channel.id] = random.randint(1, N)
    except KeyError:
        free_money_channels.update({message.channel.id: random.randint(1, N)})
        return
    code = ''.join(random.choices(string.ascii_letters + string.digits, k=4))
    amount = random.randint(10, 200)
    msg_1 = await message.channel.send(
        "{0} coins has appeared! To collect, enter `collect-coins <code>`. Code is `{1}`. Hurry, 60s left."
        .format(amount, code)
    )
    coins_collector = None
    while not coins_collector:
        def check(m):
            return (m.channel == message.channel and
                    m.author.id != client.user.id and
                    m.content == 'collect-coins {0}'.format(code))
        try:
            msg = await client.wait_for('message', check=check, timeout=60)
            if msg.content == 'collect-coins {0}'.format(code):
                coins_collector = msg.author
                msg_4 = msg
        except asyncio.TimeoutError:
            msg_2 = await message.channel.send("Error: Timeout.")
            await asyncio.sleep(3)
            await message.channel.delete_messages([msg_1, msg_2])
            return
    await _add_money(engine, coins_collector, amount)
    msg_3 = await message.channel.send(
        "User {0} has gained {1} coins!"
        .format(msg.author.mention, amount)
    )
    await asyncio.sleep(3)
    await message.channel.delete_messages([msg_1, msg_3, msg_4])


currency_functions = {
    'wallet': (fetch_wallet, "`{P}wallet [optional: @user mention]`: Check your own wallet or others' wallet."),
    'transfer-money': (transfer_money, "`{P}transfer-money <@user mention> <amount>`: Transfer some money."),
    'transfermoney': (transfer_money, "`{P}transfer-money <@user mention> <amount>`: Transfer some money."),
    'dailies': (dailies, "`{P}dailies`: Get your daily money and become riiiich."),
    'exchange': (exchange, "`{P}exchange <Pinocchio Coins> <Currency>`: Exchange currency with other bots with <:Discoin:357656754642747403> Discoin."),
}
currency_handlers = [free_money_handler]
