import database
import discord
import psutil
import os
import time
import aiohttp
import aiofiles
import variables
from datetime import timedelta, datetime
from .currency import _add_money


async def upload_data(content, extension="txt"):
    send_data = aiohttp.FormData()
    send_data.add_field("auth", variables.FILE_UPLOAD_AUTH)
    send_data.add_field("file", content, filename=f"file.{extension}")
    async with aiohttp.ClientSession() as sess:
        async with sess.post("https://f.sed.lol/upload", data=send_data) as resp:
            url = await resp.text()
    return url


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


async def process_logs(client, message, *args):
    msg = await message.channel.send("Please wait, processing log files...")
    huge_transactions = []
    commands_freq = {}
    guild_freq = {}
    user_freq = {}
    file_size = 0
    async with aiofiles.open(variables.LOG_FILE) as f:
        async for line in f:
            if line.startswith("$"):
                if "LOWAMT" in line:
                    pass
                elif "MONEY WALLET=" in line:
                    huge_transactions.append(line)
                else:
                    thirdsep = line.rfind("-")
                    secondsep = line.rfind("-", 0, thirdsep)
                    firstsep = line.rfind("-", 0, secondsep)
                    userstr = " ".join(
                        line[firstsep + 2 : secondsep - 1].strip().split()
                    )
                    guildstr = " ".join(
                        line[secondsep + 2 : thirdsep - 1].strip().split()
                    )
                    cmd = line[thirdsep + 2 :].strip().split(" ")[0].strip()
                    commands_freq[cmd] = commands_freq.get(cmd, 0) + 1
                    if guildstr not in guild_freq:
                        guild_freq[guildstr] = {}
                    guild_freq[guildstr][cmd] = guild_freq[guildstr].get(cmd, 0) + 1
                    user_freq[userstr] = user_freq.get(userstr, 0) + 1
            else:
                huge_transactions[-1] += "\n\t" + line.strip()
        file_size = await f.tell()
    if len(huge_transactions) > 0:
        transactions_txt = (
            f"All the suspicious transactions (value over 500,000 PIC):\n{'-'*50}\n"
            + f"{'-'*50}\n".join(huge_transactions) + "\n"
        )
        transactions_url = await upload_data(transactions_txt)
        embed_trans_txt = f"[Suspicious Transactions]({transactions_url})"
    else:
        embed_trans_txt = f"No suspicious transactions, yay!"
    general_stats_txt = (
        f"Pinocchio Bot Statistics (Dump Date: {str(datetime.now())}, File Size: {file_size} bytes)\n\n"
    )
    general_stats_txt += "Command Frequency (Universal):\n"
    cmd_freq_items = list(commands_freq.items())
    cmd_freq_items.sort(reverse=True, key=lambda x: x[1])
    for cmd, cnt in cmd_freq_items:
        general_stats_txt += f"\t- {cmd} | {cnt} time{'s' if cnt > 1 else ''}\n"
    general_stats_txt += f"\nCommand Frequency (Per Guild):\n"
    guild_freq_items = list(guild_freq.items())
    guild_freq_items.sort(reverse=True, key=lambda x: len(x[1]))
    for guild, data in guild_freq_items:
        cmd_freq_items = list(data.items())
        cmd_freq_items.sort(reverse=True, key=lambda x: x[1])
        total = sum([x[1] for x in cmd_freq_items])
        general_stats_txt += f"\t- {guild} | Total: {total}\n"
        for cmd, cnt in cmd_freq_items:
            general_stats_txt += f"\t\t- {cmd} | {cnt} time{'s' if cnt > 1 else ''}\n"
    general_stats_txt += f"\nUser Frequency:\n"
    usr_freq_items = list(user_freq.items())
    usr_freq_items.sort(reverse=True, key=lambda x: x[1])
    for usr, cnt in usr_freq_items:
        general_stats_txt += f"\t- {usr} | {cnt} time{'s' if cnt > 1 else ''}\n"
    general_stats_txt += "\n-----------------DUMP OVER-----------------\n"
    general_stats_url = await upload_data(general_stats_txt)

    embed = discord.Embed(
        title="Bot Logs (Dev-Only)",
        description=f"[General Statistics]({general_stats_url})",
        color=0x0,
    )
    embed.add_field(name="Suspicious Transactions", value=embed_trans_txt)
    embed.set_footer(
        text="Pinocchio Bot powered by RandomGhost#0666",
        icon_url=client.user.avatar_url_as(size=32),
    )
    await msg.edit(content=None, embed=embed)


# TODO: Implement guild info/search + user search


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
    "processlogs": (wrapper(process_logs, 5), "`{P}processlogs`: Dev-only command."),
}
