import database
import discord
import psutil
import os
import time
from datetime import timedelta
from .currency import _add_money


async def view_stats(client, message, *args):
    app_info = await client.application_info()
    process = psutil.Process(os.getpid())
    embed = discord.Embed(
        title="Bot Stats", description="Running on a dedicated server with 32GB of RAM."
    )
    embed.add_field(name="**__General Info__**", inline=False, value="\u200b")
    embed.add_field(
        name="Owner", value=f"{app_info.owner.name}#{app_info.owner.discriminator}"
    )
    embed.add_field(name="Latency", value=f"{client.latency*1000:.03f} ms")
    embed.add_field(name="Guild Count", value=f"{len(client.guilds):,}")
    embed.add_field(name="User Count", value=f"{len(client.users):,}")
    embed.add_field(name="Current Shard", value=f"{message.guild.shard_id}")
    embed.add_field(name="**__Technical Info__**", inline=False, value="\u200b")
    embed.add_field(name="System CPU Usage", value=f"{psutil.cpu_percent():.02f}%")
    embed.add_field(
        name="System RAM Usage", value=f"{psutil.virtual_memory().used/1048576:.02f} MB"
    )
    embed.add_field(
        name="System Uptime",
        value=str(timedelta(seconds=int(time.time() - psutil.boot_time()))),
    )
    embed.add_field(name="Bot CPU Usage", value=f"{process.cpu_percent():.02f}%")
    embed.add_field(
        name="Bot RAM Usage", value=f"{process.memory_info().rss/1048576:.02f} MB"
    )
    embed.add_field(
        name="Bot Uptime",
        value=str(timedelta(seconds=int(time.time() - process.create_time()))),
    )
    embed.add_field(name="**__Links__**", inline=False, value="\u200b")
    embed.add_field(
        name="Donate",
        value="[https://patreon.com/RandomGhost](https://patreon.com/RandomGhost)",
    )
    embed.add_field(
        name="Website", value="[https://pinocchiobot.xyz](https://pinocchiobot.xyz)"
    )
    embed.add_field(
        name="Discord Bots",
        value="[https://dbots.pinocchiobot.xyz](https://dbots.pinocchiobot.xyz)",
    )
    embed.add_field(
        name="Support Server",
        value="[https://support.pinocchiobot.xyz](https://support.pinocchiobot.xyz)",
    )
    embed.add_field(
        name="Invite",
        value="[https://invite.pinocchiobot.xyz](https://invite.pinocchiobot.xyz)",
    )
    embed.add_field(
        name="Add Waifus",
        value="[https://waifu.pinocchiobot.xyz](https://waifu.pinocchiobot.xyz)",
    )
    embed.set_footer(
        text=f"Running on Node-Megumin • Made by {app_info.owner.name}#{app_info.owner.discriminator}",
        icon_url=app_info.owner.avatar_url_as(size=128),
    )
    await message.channel.send(embed=embed)


async def ping(client, message, *args):
    await message.channel.send(f"Pong! Ping is {client.latency*1000:.03f} ms")


async def repeater(client, message, *args):
    print(message.content)
    print(".".join(args))
    await message.channel.send(message.content)


async def get_money(client, message, *args):
    if len(args) == 0 or not args[0].isdigit():
        await message.channel.send("Correct command is: `!wallet <amount>`")
    else:
        amount = int(args[0])
        engine = await database.prepare_engine()
        balance = await _add_money(engine, message.author, amount)
        await message.channel.send(
            f"Gave `{amount}` coins. You now have `{balance}` coins in your wallet."
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
                await message.channel.send(
                    """
Beyond this lies something too valuable to be obtained by humans.
Careful, for all those who attempted to enter, never could exit.
                """
                )

    return f


async def whois_admin(client, message, *args):
    if len(args) != 1 or not args[0].isdigit():
        await message.channel.send("Usage: {PREFIX}awhois <user ID>. Developer only!")
        return
    user = client.get_user(int(args[0]))
    if not user:
        await message.channel.send("User not found!")
        return
    engine = await database.prepare_engine()
    async with engine.acquire() as conn:
        query = database.Member.select().where(database.Member.c.member == user.id)
        cursor = await conn.execute(query)
        dbuser = await cursor.fetchone()
    embed = discord.Embed(title=f"{user.name}#{user.discriminator}", color=user.colour)
    embed.set_thumbnail(url=user.avatar_url_as(size=4096))
    embed.add_field(name="User ID", value=user.id)
    embed.add_field(name="Is Bot", value=user.bot)
    embed.add_field(name="Wallet", value=dbuser[database.Member.c.wallet])
    embed.add_field(name="Tier", value=dbuser[database.Member.c.tier])
    last_dailies = dbuser[database.Member.c.last_dailies]
    if last_dailies:
        last_dailies = last_dailies.strftime("%A, %d %B, %Y - %I:%M:%S %p")
    last_reward = dbuser[database.Member.c.last_reward]
    if last_reward:
        last_reward = last_reward.strftime("%A, %d %B, %Y - %I:%M:%S %p")
    embed.add_field(name="Last Dailies", value=last_dailies)
    embed.add_field(name="Last Reward", value=last_reward)
    embed.add_field(
        name="Account Created On",
        inline=False,
        value=user.created_at.strftime("%A, %d %B, %Y - %I:%M:%S %p"),
    )
    guilds = []
    for i in client.guilds:
        if member := i.get_member(user.id):
            guilds.append(
                f"{'**[Owner]** ' if (member == i.owner) else ''}{i.name} ({len(i.members)})"
            )
    embed.add_field(name="In Guilds", inline=False, value=", ".join(guilds))
    await message.channel.send(embed=embed)


# TODO: Implement guild info/search + user search


devtest_functions = {
    "botstats": (wrapper(view_stats, 0), "`{P}botstats`: General stats about the bot."),
    "botinfo": (wrapper(view_stats, 0), "`{P}botinfo`: General stats about the bot."),
    "info": (wrapper(view_stats, 0), "`{P}info`: General stats about the bot."),
    "getmoney": (wrapper(get_money, 5), "Only for developer to use."),
    "repeater": (wrapper(repeater, 5), "Just a repeater. Ignore this. Dev-command."),
    "ping": (wrapper(ping, 0), "`{P}ping`: Get the bot pingrate."),
    "awhois": (
        wrapper(whois_admin, 5),
        "`{P}awhois`: Get details about an user. Dev only.",
    ),
}
