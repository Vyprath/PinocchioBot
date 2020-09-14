import asyncio
import datetime
import random
import string
import time
import traceback

import discord
from discoin import BadRequest, InternalServerError, WebTimeoutError

import database
import variables
from log import log
from variables import DAILIES_AMOUNT, FREE_MONEY_SPAWN_LIMIT, PREFIX


async def _fetch_wallet(member):
    fetch_query = database.Member.select().where(database.Member.c.member == member.id)
    engine = await database.prepare_engine()
    resp = await engine.fetch_one(query=fetch_query)
    if resp is None:
        return None
    else:
        return resp[database.Member.c.wallet]


async def _add_money(member, amount):
    current_balance = await _fetch_wallet(member)
    if current_balance is None:
        return None
    stacktrace = "LOWAMT"
    if amount > 500000:
        stacktrace = "\n" + "\n".join([i.rstrip() for i in traceback.format_stack()])
    logamt = (
        f"ADDMONEY WALLET={current_balance} AMOUNT={amount} STACKTRACE={stacktrace}"
    )
    await log(member, member.guild if hasattr(member, "guild") else None, logamt)
    engine = await database.prepare_engine()
    update_query = (
        database.Member.update(None)
        .where(database.Member.c.member == member.id)
        .values(wallet=current_balance + amount)
    )
    await engine.execute(update_query)
    return current_balance + amount


async def _remove_money(member, amount):
    current_balance = await _fetch_wallet(member)
    if current_balance is None:
        return None
    if current_balance - amount < 0:
        return False
    stacktrace = "LOWAMT"
    if amount > 500000:
        stacktrace = "\n" + "\n".join([i.rstrip() for i in traceback.format_stack()])
    logamt = (
        f"REMMONEY WALLET={current_balance} AMOUNT={amount} STACKTRACE={stacktrace}"
    )
    await log(member, member.guild if hasattr(member, "guild") else None, logamt)
    engine = await database.prepare_engine()
    update_query = (
        database.Member.update(None)
        .where(database.Member.c.member == member.id)
        .values(wallet=current_balance - amount)
    )
    await engine.execute(update_query)
    return current_balance + amount


async def fetch_wallet(client, message, *args):
    if len(message.mentions) == 0:
        wallet = await _fetch_wallet(message.author)
        await message.channel.send(
            f"You have {wallet:,} <:PIC:668725298388271105> in your wallet."
        )
    else:
        member = message.mentions[0]
        wallet = await _fetch_wallet(member)
        await message.channel.send(
            f"{member.name} has {wallet:,} <:PIC:668725298388271105> in their wallet."
        )


async def transfer_money(client, message, *args):
    if len(args) != 2 or not args[1].isdigit() or len(message.mentions) != 1:
        await message.channel.send(
            f"Correct command is: `{PREFIX}transfer <@user mention> <amount>`"
        )
        return
    amount = int(args[1])
    to_transfer = message.mentions[0]
    wallet = await _fetch_wallet(message.author)
    if wallet - amount < 0:
        await message.channel.send(
            "You do not have enough money to transfer! <:smug:575373306715439151>"
        )
        return
    await _remove_money(message.author, amount)
    await _add_money(to_transfer, amount)
    await message.channel.send("Done <:SataniaThumb:575384688714317824>")


async def dailies(client, message, *args):
    engine = await database.prepare_engine()
    fetch_query = database.Member.select().where(
        database.Member.c.member == message.author.id
    )
    member = await engine.fetch_one(fetch_query)
    last_dailies = member[database.Member.c.last_dailies]
    if last_dailies is not None:
        last_dailies = datetime.datetime.fromisoformat(str(last_dailies))
    fetch_query = database.Member.select().where(
        database.Member.c.member == message.author.id
    )
    resp = await engine.fetch_all(fetch_query)
    member_tier = 0
    for m in resp:
        _t = m[database.Member.c.tier]
        if _t > member_tier:
            member_tier = _t
    now = datetime.datetime.now()
    if last_dailies is None or (now - last_dailies).days >= 1:
        update_query = (
            database.Member.update(None)
            .where(database.Member.c.member == message.author.id)
            .values(last_dailies=now)
        )
        await engine.execute(update_query)
        if member_tier >= variables.DONATOR_TIER_2:
            await _add_money(message.author, DAILIES_AMOUNT * 4)
            await message.channel.send(
                f"Recieved {DAILIES_AMOUNT * 4} <:PIC:668725298388271105>! 4 times the usual amount "
                "for being a Tier 2 donator! <:uwu:575372762583924757>"
            )
        elif member_tier >= variables.DONATOR_TIER_1:
            await _add_money(message.author, DAILIES_AMOUNT * 2)
            await message.channel.send(
                f"Recieved {DAILIES_AMOUNT * 2} <:PIC:668725298388271105>! Twice the usual amount "
                "for being a Tier 1 donator! <:uwu:575372762583924757>"
            )
        else:
            await _add_money(message.author, DAILIES_AMOUNT)
            await message.channel.send(
                f"Recieved {DAILIES_AMOUNT} <:PIC:668725298388271105>! <:SataniaThumb:575384688714317824>"
            )
    else:
        next_reset = last_dailies + datetime.timedelta(days=1) - now
        tdelta_hours = (next_reset.seconds) // 3600
        tdelta_mins = (next_reset.seconds) // 60 - (tdelta_hours * 60)
        await message.channel.send(
            f"Please wait {tdelta_hours:>02d} hours and "
            f"{tdelta_mins:>02d} minutes more to get dailies."
        )


async def exchange(client, message, *args):
    if len(args) != 2 or not args[0].isdigit():
        await message.channel.send(
            f"""
Usage: `{PREFIX}exchange <coins> <currency>`
If you want to know more about this and supported currencies, use `{PREFIX}discoin`.
        """
        )
        return
    processing_msg = await message.channel.send("Processing Transaction...")
    amount = int(args[0])
    to = args[1].upper()
    res = await _remove_money(message.author, amount)
    if not res:
        await processing_msg.edit(content="You don't have enough balance!")
        return
    try:
        transaction = await variables.discoin_client.create_transaction(
            to, amount, message.author.id
        )
    except (BadRequest, InternalServerError, WebTimeoutError) as e:
        await processing_msg.edit(
            content=f"""
Hit an error :exploding_head: {type(e).__name__}
Message: {e}
        """
        )
        return
    embed = discord.Embed(
        title="<:Discoin:357656754642747403> Exchange Successful!",
        description=f"""
Your Pino-coins <:PIC:668725298388271105> are being sent via the top-secret Agent Wumpus. He usually delivers the coins within 5 minutes.
See `{PREFIX}discoin` for more info.
        """,
    )
    embed.add_field(
        name="Pinocchio Coins <:PIC:668725298388271105> (PIC) Exchanged", value=amount
    )
    embed.add_field(name=f"{to} To Recieve", value=transaction.payout)
    embed.add_field(
        name="Transaction Receipt",
        inline=False,
        value=(
            f"[```{transaction.id}```](https://dash.discoin.zws.im/#/transactions/{transaction.id}/show)"
            "Keep this code in case Agent Wumpus fails to deliver the coins.",
        ),
    )
    embed.set_footer(
        text=f"{message.author.name}#{message.author.discriminator}",
        icon_url=message.author.avatar_url_as(size=128),
    )
    await processing_msg.edit(content=None, embed=embed)


free_money_channels = {}
passive_money_users = {}


async def free_money_handler(client, message):
    if (
        message.author.id == client.user.id
        or message.author.bot
        or message.guild is None
    ):
        return
    now = time.monotonic()
    if message.author.id in passive_money_users.keys():
        last = passive_money_users[message.author.id]
        if now - last > 60:
            passive_money_users[message.author.id] = now
            await _add_money(message.author, random.randint(1, 5))
    else:
        passive_money_users.update({message.author.id: now})
    engine = await database.prepare_engine()
    fetch_query = database.Guild.select().where(
        database.Guild.c.guild == message.guild.id
    )
    resp = await engine.fetch_one(fetch_query)
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
    code = "".join(random.choices(string.ascii_letters + string.digits, k=4))
    amount = random.randint(10, 200)
    msg_1 = await message.channel.send(
        f"{amount} <:PIC:668725298388271105> has appeared <:AilunaHug:575373643551473665>! To collect, enter `collect-coins <code>`. Code is `{code}`. Hurry, 60s left."
    )
    coins_collector = None
    while not coins_collector:

        def check(m):
            return (
                m.channel == message.channel
                and m.author.id != client.user.id
                and m.content == f"collect-coins {code}"
            )

        try:
            msg = await client.wait_for("message", check=check, timeout=60)
            if msg.content == f"collect-coins {code}":
                coins_collector = msg.author
                msg_4 = msg
        except asyncio.TimeoutError:
            msg_2 = await message.channel.send("Error: Timeout.")
            await asyncio.sleep(3)
            await message.channel.delete_messages([msg_1, msg_2])
            return
    await _add_money(coins_collector, amount)
    msg_3 = await message.channel.send(
        f"User {msg.author.mention} has gained {amount} <:PIC:668725298388271105>!"
    )
    await asyncio.sleep(3)
    await message.channel.delete_messages([msg_1, msg_3, msg_4])


currency_functions = {
    "wallet": (
        fetch_wallet,
        "`{P}wallet [optional: @user mention]`: Check your own wallet or others' wallet.",
    ),
    "transfer": (
        transfer_money,
        "`{P}transfer <@user mention> <amount>`: Transfer some money.",
    ),
    "transfermoney": (
        transfer_money,
        "`{P}transfer-money <@user mention> <amount>`: Transfer some money.",
    ),
    "daily": (dailies, "`{P}daily`: Get your daily money and become riiiich."),
    "dailies": (dailies, "`{P}dailies`: Get your daily money and become riiiich."),
    "exchange": (
        exchange,
        "`{P}exchange <Pinocchio Coins> <Currency>`: Exchange currency with other bots with <:Discoin:357656754642747403> Discoin.",
    ),
}
currency_handlers = [free_money_handler]
