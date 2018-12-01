import database
import random
import string
import asyncio
import time
import datetime
from variables import FREE_MONEY_SPAWN_LIMIT, DAILIES_AMOUNT, PREFIX, DAILIES_DATE


async def _fetch_wallet(engine, member):
    async with engine.acquire() as conn:
        fetch_query = database.Member.select().where(
            database.Member.c.member == member.id
        ).where(
            database.Member.c.guild == member.guild.id
        )
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
        ).where(
            database.Member.c.guild == member.guild.id
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
        ).where(
            database.Member.c.guild == member.guild.id
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


async def get_money(client, message, *args):
    if not message.author.guild_permissions.administrator:
        await message.channel.send("This command is restricted, to be used only by gods.")
        return
    if len(args) == 0 or not args[0].isdigit():
        await message.channel.send("Correct command is: `{0}wallet <amount>`".format(PREFIX))
    else:
        amount = int(args[0])
        engine = await database.prepare_engine()
        balance = await _add_money(engine, message.author, amount)
        await message.channel.send(
            "Gave `{0}` coins. You now have `{1}` coins in your wallet."
            .format(amount, balance)
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
        ).where(
            database.Member.c.guild == message.guild.id
        )
        cursor = await conn.execute(fetch_query)
        member = await cursor.fetchone()
        last_dailies = member[database.Member.c.last_dailies]
        if last_dailies is not None:
            last_dailies = datetime.datetime.fromisoformat(str(last_dailies))
        now = datetime.datetime.now()
        if last_dailies is None or (now - last_dailies).days >= 1:
            update_query = database.Member.update().where(
                database.Member.c.member == message.author.id
            ).where(
                database.Member.c.guild == message.guild.id
            ).values(last_dailies=now.isoformat())
            await conn.execute(update_query)
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
            await _add_money(engine, message.author, random.randint(1, 20))
    else:
        passive_money_users.update({message.author.id: now})
    engine = await database.prepare_engine()
    async with engine.acquire() as conn:
        fetch_query = database.Guild.select().where(
            database.Guild.c.guild == message.guild.id
        )
        cursor = await conn.execute(fetch_query)
        resp = await cursor.fetchone()
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
    'wallet': (fetch_wallet, 'Check your wallet.'),
    'get-money': (get_money, 'Get yourself some coins.'),
    'transfer-money': (transfer_money, 'Transfer your money.'),
    'dailies': (dailies, 'Come, collect your free money.'),
}
currency_handlers = [free_money_handler]
