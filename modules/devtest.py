from variables import CMD_POPULARITY
import database
from .currency import _add_money


async def view_stats(client, message, *args):
    guilds = client.guilds
    app_info = await client.application_info()
    await message.channel.send("""
Stats for this bot: **(Classified Information, kek)**
**Latency:** {0}
**Number of Guilds In:** {1}
**Owner:** {2}
    """.format(
        client.latency,
        len(guilds),
        app_info.owner.mention
    ))


async def famous_cmd(client, message, *args):
    resp = []
    for k, v in CMD_POPULARITY.items():
        resp.append("`{0}`: {1}".format(k, v))
    await message.channel.send(", ".join(resp))


async def repeater(client, message, *args):
    print(message.content)
    print(".".join(args))


async def get_money(client, message, *args):
    if len(args) == 0 or not args[0].isdigit():
        await message.channel.send("Correct command is: `!wallet <amount>`")
    else:
        amount = int(args[0])
        engine = await database.prepare_engine()
        balance = await _add_money(engine, message.author, amount)
        await message.channel.send(
            "Gave `{0}` coins. You now have `{1}` coins in your wallet."
            .format(amount, balance)
            )


def wrapper(func, tier):
    async def f(client, message, *args):
        engine = await database.prepare_engine()
        member = message.author
        async with engine.acquire() as conn:
            fetch_query = database.Member.select().where(
                database.Member.c.member == member.id
            )
            cursor = await conn.execute(fetch_query)
            conn = await cursor.fetchone()
            member_tier = conn[database.Member.c.tier]
            if member_tier >= tier:
                await func(client, message, *args)
            else:
                await message.channel.send("""
They say, curiosity killed the cat.
But, I hate what they say.
But still, what lies beyond, is beyond your current level.
Maybe try contacting the ghost for an upgrade?
                """)
    return f


devtest_functions = {
    'botstats': (wrapper(view_stats, 3), None),
    'famouscmds': (wrapper(famous_cmd, 4), None),
    'getmoney': (wrapper(get_money, 4), None),
    'repeater': (wrapper(repeater, 5), None),
}
