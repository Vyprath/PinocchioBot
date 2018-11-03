import database
import random
import string
import asyncio
import time
# TODO: Handle in case profile not yet created.


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
    if len(args) == 0:
        wallet = await _fetch_wallet(engine, message.author)
        if wallet is None:
            await database.make_member_profile([message.author], client.user.id)
            wallet = await _fetch_wallet(engine, message.author)
        await message.channel.send(
            "Heya, {0}. You have `{1}` coins in your wallet."
            .format(message.author.mention, wallet)
            )


async def get_money(client, message, *args):
    if not message.author.guild_permissions.administrator:
        await message.channel.send("This command is restricted, to be used only by gods.")
        return
    if len(args) == 0 or not args[0].isdigit():
        await message.channel.send("Correct command is: `wallet <amount>`")
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
            "Corrent command is: `!transfer-money <@user mention> <amount>`")
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
            await _add_money(engine, message.author, random.randint(10, 40))
    else:
        passive_money_users.update({message.author.id: now})
    N = 50
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
    await message.channel.send(
        "{0} coins has appeared! To collect, enter `collect-coins {1}`. Hurry, 60s left."
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
        except asyncio.TimeoutError:
            await message.channel.send("Error: Timeout.")
            return
    engine = await database.prepare_engine()
    await _add_money(engine, coins_collector, amount)
    await message.channel.send(
        "User {0} has gained {1} coins!"
        .format(msg.author.mention, amount)
    )


currency_functions = {
    'wallet': (fetch_wallet, 'Check your wallet.'),
    'get-money': (get_money, 'Get yourself some coins.'),
    'transfer-money': (transfer_money, 'Transfer your money.'),
}
currency_handlers = [free_money_handler]
