import datetime
import re

import discord
from discord.utils import snowflake_time

import database
import dborg
import variables
from variables import PREFIX, VOTE_REWARD

from .currency import _add_money
from .utils import num_to_emote, num_to_uni_emote


async def donate(client, message, *args):
    await message.channel.send(
        "Please go to this site to donate: https://www.patreon.com/RandomGhost (PayPal only)."
        "I also accept Bitcoin and other crypto payments. Please contact me (RandomGhost#0666) "
        f"or on the support server (`{PREFIX}support`) for other payment methods."
        "Thanks! <a:thanks:699004469610020964>"
    )


async def invite(client, message, *args):
    await message.channel.send(
        """
Bot invite link: https://top.gg/bot/506878658607054849 <:uwu:575372762583924757>
    """
    )


async def creator(client, message, *args):
    await message.channel.send(
        """
Bot created by RandomGhost#0666. Ask him for new features/bugs! <a:thanks:699004469610020964>
To join support server, use `=help` or go to https://support.pinocchiobot.xyz.
    """
    )


async def vote_bot(client, message, *args):
    await message.channel.send(
        f"""
Vote for this bot and then claim your reward with `{PREFIX}claimreward`.
Vote URL: https://top.gg/bot/506878658607054849/vote
You can vote once every 12 hours.
You get 2x rewards for voting on weekends.
    """
    )


async def claim_rewards(client, message, *args):
    voted = await dborg.DBL_API.has_voted(message.author.id)
    db_verified = False
    engine = await database.prepare_engine()
    fetch_query = database.Member.select().where(
        database.Member.c.member == message.author.id
    )
    member = await engine.fetch_one(query=fetch_query)
    member_tier = member[database.Member.c.tier]
    last_reward = member[database.Member.c.last_reward]
    if not last_reward:
        db_verified = True
    else:
        db_verified = bool(
            (datetime.datetime.now() - last_reward).total_seconds() > 3600 * 12
        )
    if voted and db_verified:
        msgtxts = ["Thanks for voting! Here, have some coins."]
        coins = VOTE_REWARD
        is_weekend = await dborg.DBL_API.is_weekend()
        if is_weekend:
            coins *= 2
            msgtxts.append("Thanks for voting on weekend! You get 2x coins.")
        if member_tier >= variables.DONATOR_TIER_2:
            coins *= 4
            msgtxts.append(
                "You get 4 times the usual amount for being a tier 2 donator! "
                "<:AilunaHug:575373643551473665>"
            )
        elif member_tier >= variables.DONATOR_TIER_1:
            coins *= 2
            msgtxts.append(
                "You get 2 times the usual amount for being a tier 1 donator! "
                "<:AilunaHug:575373643551473665>"
            )
        engine = await database.prepare_engine()
        update_query = (
            database.Member.update(None)
            .where(database.Member.c.member == message.author.id)
            .values(last_reward=datetime.datetime.now())
        )
        await engine.execute(update_query)
        await _add_money(message.author, coins)
        msgtxts.append(
            f"{message.author.name} has got {coins} coins. <:SataniaThumb:575384688714317824>"
        )
        await message.channel.send("\n".join(msgtxts))
    else:
        vote_string = (
            "You have not yet voted"
            if not voted
            else "You have voted but it has not been 12 hours since last claim"
        )
        await message.channel.send(
            f"{vote_string}\nVote with `{PREFIX}vote` and then claim your rewards every 12 hours!"
        )


async def poll(client, message, *args):
    if len(args) < 3:
        await message.channel.send(
            f"""
Usage: {PREFIX}poll \"Title of Poll\" \"Option 1\" \"Option 2\" ["Option 3"...]
Remember to keep number options below or equal to 10.
        """
        )
        return
    title = args[0].replace('"', "").replace("'", "")
    options = list([i.replace('"', "").replace("'", "") for i in args[1:]])
    if len(options) > 10:
        options[9] = " ".join(options[9:])
        options = options[:10]
    desc = ""
    for i, opt in enumerate(options):
        desc += ":{0}: : {1}\n".format(num_to_emote[i], opt)
    embed = discord.Embed(title=title, color=message.author.colour, description=desc)
    embed.set_footer(
        text=f"Poll made by: {message.author.name}#{message.author.discriminator}",
        icon_url=message.author.avatar_url,
    )
    msg = await message.channel.send(embed=embed)
    for i, _ in enumerate(options):
        await msg.add_reaction(num_to_uni_emote[i])


async def whois(client, message, *args):
    if len(message.mentions) == 0:
        await message.channel.send(f"Usage: {PREFIX}whois <@user mention>")
        return
    user = message.mentions[0]
    embed = discord.Embed(title=f"{user.name}#{user.discriminator}", color=user.colour)
    tdelta = datetime.datetime.now() - user.joined_at
    embed.add_field(name="User ID", value=user.id)
    if user.nick:
        embed.add_field(name="Nickname", value=user.nick)
    if user.top_role:
        embed.add_field(name="Top Role", value=user.top_role)
    embed.add_field(name="Status", value=user.status)
    embed.add_field(name="Is Bot", value=user.bot)
    _perms = user.guild_permissions
    embed.add_field(name="Is Administrator", value=_perms.administrator)
    roles = user.roles[1:]
    if len(roles) > 0:
        role_str = ", ".join([i.name for i in roles])
    else:
        role_str = "No roles set."
    embed.add_field(name="Roles", inline=False, value=role_str)
    embed.add_field(
        name="Account Created On",
        inline=False,
        value=snowflake_time(user.id).strftime("%A, %d %B, %Y. %I:%M:%S %p"),
    )
    embed.add_field(
        name="In Server For",
        inline=False,
        value=f"{tdelta.days} days, {tdelta.seconds//3600} hours",
    )
    perms_list = [
        "kick_members",
        "ban_members",
        "manage_channels",
        "manage_guild",
        "add_reactions",
        "view_audit_log",
        "priority_speaker",
        "send_messages",
        "send_tts_messages",
        "manage_messages",
        "attach_files",
        "read_message_history",
        "mention_everyone",
        "embed_links",
        "external_emojis",
        "connect",
        "speak",
        "mute_members",
        "deafen_members",
        "move_members",
        "use_voice_activation",
        "change_nickname",
        "manage_nicknames",
        "manage_roles",
        "manage_webhooks",
        "manage_emojis",
    ]
    perms = []
    for i in perms_list:
        if getattr(_perms, i):
            perms += [i.replace("_", " ").capitalize()]
    if perms == []:
        perms = ["No special permissions."]
    perms_str = ", ".join(perms)
    embed.add_field(name="Permissions", value=perms_str, inline=False)
    embed.set_thumbnail(url=user.avatar_url)
    await message.channel.send(embed=embed)


async def discoin(client, message, *args):
    embed = discord.Embed(
        title="<:Discoin:357656754642747403> Discoin Information",
        description=f"""
Discoin is a platform with which participating bots can exchange money with each other.
Dashboard for Discoin is here: https://dash.discoin.zws.im
Usage: `{PREFIX}exchange <Pinocchio Coins> <Currency>`
where `currency` is the receiving bot's currency name.
        """,
    )
    currencies = await variables.DISCOIN_CLIENT.fetch_currencies()
    currencies = [
        f"{i.name:<19}({i.id}) - {float(i.value):07.4f} - {i.reserve}"
        for i in currencies
    ]
    txt = f"{'Name':<19}{'(ID)':<3}  - {'Value':<7} - Reserve"
    currencies.insert(0, txt)
    currencies.insert(1, max([len(i) for i in currencies]) * "-")
    embed.add_field(
        name="**Discoin Currency Table**",
        inline=False,
        value="```" + "\n".join(currencies) + "```",
    )
    await message.channel.send(embed=embed)


def _leaderboard_text(client, results):
    rtxt = []
    i = 1
    for j in results:
        user = client.get_user(j["member"])
        if user is None:
            continue
        if i <= 3:
            if i == 1:
                medal = ":first_place:"
            elif i == 2:
                medal = ":second_place:"
            elif i == 3:
                medal = ":third_place:"
            rtxt.append(
                f"**[{str(i).zfill(2)}] __{user.name}__ {medal}**\nWallet: "
                "{j['wallet']}, Waifu Value: {j['waifu_sum']}, **Total: {j['total']}**"
            )  # noqa
        else:
            rtxt.append(
                f"**[{str(i).zfill(2)}] {user.name}**\nWallet: {j['wallet']}, "
                "Waifu Value: {j['waifu_sum']}, **Total: {j['total']}**"
            )  # noqa
        i += 1
        if i == 11:
            break
    return "\n".join(rtxt)


async def world_leaderboard(client, message, *args):
    engine = await database.prepare_engine()
    query = """
SELECT id,M.member,tier,COALESCE(wsum,0) as waifu_sum,wallet,(COALESCE(wsum, 0)+wallet) as total
FROM members M
LEFT JOIN (select member_id, sum(purchased_for) as wsum from purchased_waifu group by member_id) PW
ON (M.id = PW.member_id)
WHERE wallet > 0 OR COALESCE(wsum, 0) > 0
ORDER BY total DESC
LIMIT 80;
    """
    results = await engine.fetch_all(query=query)
    txt = _leaderboard_text(client, results)
    embed = discord.Embed(
        title=":trophy: World Leaderboards",
        colour=message.author.colour,
        description=txt,
    )
    top_user = client.get_user(results[0]["member"])
    embed.set_footer(
        text=f"Current World Champion is {top_user.name if top_user else results[0]['member']}.",
        icon_url=str(top_user.avatar_url_as(size=64))
        if top_user
        else "https://cdn.pixabay.com/photo/2016/08/08/09/17/avatar-1577909_960_720.png",
    )
    await message.channel.send(embed=embed)


async def guild_leaderboard(client, message, *args):
    engine = await database.prepare_engine()
    mlist = tuple([m.id for m in message.guild.members])
    query = f"""
SELECT id,M.member,tier,COALESCE(wsum,0) as waifu_sum,wallet,(COALESCE(wsum, 0)+wallet) as total
FROM members M LEFT JOIN (
SELECT member_id,sum(purchased_for) as wsum FROM purchased_waifu
WHERE guild = {message.guild.id} GROUP BY member_id) PW ON (M.id = PW.member_id)
WHERE (wallet > 0 OR COALESCE(wsum, 0) > 0) AND M.member in {mlist}
ORDER BY total DESC LIMIT 10;
    """
    results = await engine.fetch_all(query=query)
    txt = _leaderboard_text(client, results)
    embed = discord.Embed(
        title=":trophy: Guild Leaderboards",
        colour=message.author.colour,
        description=txt,
    )
    top_user = client.get_user(results[0]["member"])
    embed.set_footer(
        text=f"Current Guild Champion is {top_user.name}.",
        icon_url=str(top_user.avatar_url_as(size=64)),
    )
    await message.channel.send(embed=embed)


async def say(client, message, *args):
    if (
        len(args) >= 2
        and len(message.channel_mentions) >= 1
        and re.match(r"^<#\d{18}>", args[0])
    ):
        channel = message.channel_mentions[0]
        text = message.content
        text = text.replace(" ", "x", 1)[text.find(" ") + 1 :]  # Whatever works /shrug
    elif len(args) >= 1:
        channel = message.channel
        text = message.content
        text = text[text.find(" ") + 1 :]
    else:
        await message.channel.send(
            f"Usage: `{PREFIX}say [channel, default: current] <text>`"
        )
        return
    if not channel.permissions_for(message.author).send_messages:
        await message.channel.send(
            "Cannot send message in that channel with your privileges!"
        )
        return
    if ("@everyone" in text or "@here" in text) and not channel.permissions_for(
        message.author
    ).mention_everyone:  # noqa
        await message.channel.send(
            "Cannot send messages with @mentions with your privileges!"
        )
        return
    await channel.send(text)
    await message.delete()


general_functions = {
    "vote": (
        vote_bot,
        "`{P}vote`: Vote for this bot! Isn't Pinocchio kawaii? Vote for her and make her happy.",
    ),
    "claimreward": (
        claim_rewards,
        "`{P}claimreward`: Pinocchio is happy now! Thanks for voting. Here, collect your reward.",
    ),
    "donate": (donate, "`{P}donate`: Donate to this bot UwU."),
    "creator": (
        creator,
        "`{P}creator`: Get to know the creator of this bot, "
        "so you can annoy him to fix the damned bugs.",
    ),
    "support": (creator, "`{P}support`: Support server link. You can add waifus here!"),
    "invite": (invite, "`{P}invite`: Get the invite link for this server."),
    "poll": (
        poll,
        '`{P}poll "Title of Poll" "Option 1" "Option 2" '
        '["Option 3"...]`: Create a reaction poll.',
    ),
    "whois": (whois, "`{P}whois <@user mention>`: Get information about a user."),
    "discoin": (
        discoin,
        "`{P}discoin`: Get information about how to exchange currency "
        "with other bots using <:Discoin:357656754642747403> Discoin.",
    ),
    "guildleaderboard": (
        guild_leaderboard,
        "`{P}guildleaderboard`: Get this guild's leaderboard.",
    ),
    "leaderboard": (
        guild_leaderboard,
        "`{P}leaderboard`: Get this guild's leaderboard.",
    ),
    "glb": (guild_leaderboard, "`{P}glb`: Get this guild's leaderboard."),
    "guildlb": (guild_leaderboard, "`{P}guildlb`: Get this guild's leaderboard."),
    "worldleaderboard": (
        world_leaderboard,
        "`{P}worldleaderboard`: Get this world's leaderboard.",
    ),
    "wlb": (world_leaderboard, "`{P}wlb`: Get this world's leaderboard."),
    "worldlb": (world_leaderboard, "`{P}worldlb`: Get this world's leaderboard."),
    "say": (say, "`{P}say [channel, default: current] <text>`: Speak as Pinocchio!"),
    "pinosay": (
        say,
        "`{P}pinosay [channel, default: current] <text>`: Speak as Pinocchio!",
    ),
}
