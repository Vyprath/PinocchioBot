import database
import discord
import psutil
import os
from .currency import _add_money


async def view_stats(client, message, *args):
    app_info = await client.application_info()
    process = psutil.Process(os.getpid())
    embed = discord.Embed(
        title="Bot Stats",
        description="Running on a dedicated server with 32GB of RAM.")
    embed.add_field(name="**__General Info__**", inline=False, value="\u200b")
    embed.add_field(
        name="Owner",
        value=f"{app_info.owner.name}#{app_info.owner.discriminator}")
    embed.add_field(name="Latency", value=f"{client.latency*1000:.03f} ms")
    embed.add_field(name="Guild Count", value=f"{len(client.guilds):,}")
    embed.add_field(name="User Count", value=f"{len(client.users):,}")
    embed.add_field(name="**__Technical Info__**", inline=False, value="\u200b")
    embed.add_field(name="Overall CPU Usage", value=f"{psutil.cpu_percent():.02f}%")
    embed.add_field(name="Overall RAM Usage",
                    value=f"{psutil.virtual_memory().used/1048576:.02f} MB")
    embed.add_field(name="Bot CPU Usage", value=f"{process.cpu_percent():.02f}%")
    embed.add_field(name="Bot RAM Usage", value=f"{process.memory_info().rss/1048576:.02f} MB")
    embed.add_field(name="**__Links__**", inline=False, value="\u200b")
    embed.add_field(name="Donate", value="[https://patreon.com/RandomGhost](https://patreon.com/RandomGhost)")
    embed.add_field(name="Website", value="[https://pinocchiobot.xyz](https://pinocchiobot.xyz)")
    embed.add_field(name="Discord Bots", value="[https://dbots.pinocchiobot.xyz](https://dbots.pinocchiobot.xyz)")
    embed.add_field(name="Support Server", value="[https://support.pinocchiobot.xyz](https://support.pinocchiobot.xyz)")
    embed.add_field(name="Invite", value="[https://invite.pinocchiobot.xyz](https://invite.pinocchiobot.xyz)")
    embed.add_field(name="Add Waifus", value="[https://waifu.pinocchiobot.xyz](https://waifu.pinocchiobot.xyz)")
    embed.set_footer(
        text=f"Running on Node-Megumin • Made by {app_info.owner.name}#{app_info.owner.discriminator}",
        icon_url=app_info.owner.avatar_url_as(size=128))
    await message.channel.send(embed=embed)


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
    'botstats': (wrapper(view_stats, 0), None),
    'getmoney': (wrapper(get_money, 4), None),
    'repeater': (wrapper(repeater, 5), None),
}
