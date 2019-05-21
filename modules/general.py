import database
import dborg
import datetime
import discord
from discord.utils import snowflake_time
from .currency import _add_money
from variables import VOTE_REWARD, PREFIX
import variables


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
Bot created by RandomGhost#0666. Ask him for new features/bugs!
To join support server, use `=help` or go to https://support.pinocchiobot.xyz.
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
        )
        cursor = await conn.execute(fetch_query)
        member = await cursor.fetchone()
        fetch_query = database.Member.select().where(
                database.Member.c.member == message.author.id
            )
        cursor = await conn.execute(fetch_query)
        resp = await cursor.fetchone()
        member_tier = resp[database.Member.c.tier]
        last_reward = member[database.Member.c.last_reward]
        if last_reward is None:
            db_verified = True
        else:
            if ((datetime.datetime.now() - last_reward).days > 1 or
                    (datetime.datetime.now() - last_reward).seconds//3600 >= 12):
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
        if member_tier >= variables.DONATOR_TIER_2:
            coins *= 4
            await message.channel.send(
                "You get 4 times the usual amount for being a tier 2 donator! :smile:")
        elif member_tier >= variables.DONATOR_TIER_1:
            coins *= 2
            await message.channel.send(
                "You get 2 times the usual amount for being a tier 1 donator! :smile:")
        engine = await database.prepare_engine()
        async with engine.acquire() as conn:
            update_query = database.Member.update().where(
                database.Member.c.member == message.author.id
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
    embed = discord.Embed(title=title, color=message.author.colour, description=desc)
    embed.set_footer(
        text="Poll made by: {0}#{1}".format(message.author.name, message.author.discriminator),
        icon_url=message.author.avatar_url)
    msg = await message.channel.send(embed=embed)
    for i, _ in enumerate(options):
        await msg.add_reaction(num_to_uni_emote[i])


async def whois(client, message, *args):
    if len(message.mentions) == 0:
        await message.channel.send("Usage: {0}whois <@user mention>".format(PREFIX))
        return
    user = message.mentions[0]
    embed = discord.Embed(
        title="{0}#{1}".format(user.name, user.discriminator), color=user.colour)
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
    embed.add_field(
        name="Roles", inline=False, value=role_str)
    embed.add_field(
        name="Account Created On", inline=False,
        value=snowflake_time(user.id).strftime("%A, %d %B, %Y. %I:%M:%S %p"))
    embed.add_field(
        name="In Server For", inline=False,
        value="{0} days, {1} hours".format(tdelta.days, tdelta.seconds//3600))
    PERMS_LIST = [
        'kick_members', 'ban_members', 'manage_channels', 'manage_guild', 'add_reactions',
        'view_audit_log', 'priority_speaker', 'send_messages', 'send_tts_messages',
        'manage_messages', 'attach_files', 'read_message_history', 'mention_everyone',
        'embed_links', 'external_emojis', 'connect', 'speak', 'mute_members', 'deafen_members',
        'move_members', 'use_voice_activation', 'change_nickname', 'manage_nicknames',
        'manage_roles', 'manage_webhooks', 'manage_emojis'
    ]
    perms = []
    for i in PERMS_LIST:
        if getattr(_perms, i):
            perms += [i.replace('_', ' ').capitalize()]
    if perms == []:
        perms = ["No special permissions."]
    perms_str = ', '.join(perms)
    embed.add_field(name="Permissions", value=perms_str, inline=False)
    embed.set_thumbnail(url=user.avatar_url)
    await message.channel.send(embed=embed)


async def discoin(client, message, *args):
    embed = discord.Embed(title="<:Discoin:357656754642747403> Discoin Information", description=f"""
Discoin is a platform with which participating bots can exchange money with each other.
Supported Discord bots and their commands are found here: [https://discoin.gitbook.io/docs/users-guide].
The conversion rates are found here: [http://discoin.sidetrip.xyz/rates].

For **Pinocchio Coins (PIC)**, conversion rate is __1.00 PIC => 0.20 Discoin => 0.80 PIC__.

**You need to verify your discord account first (http://discoin.sidetrip.xyz/verify) in order to use discoin functionality on any participating bot!**

Usage: `{PREFIX}exchange <Pinocchio Coins> <Currency>`
where `currency` is the receiving bot's currency name.
        """)
    await message.channel.send(embed=embed)


async def world_leaderboard(client, message, *args):
    engine = await database.prepare_engine()
    async with engine.acquire() as conn:
        # TODO: Un-hardcode this SQL query?
        query = """
SELECT id,M.member,tier,COALESCE(wsum,0) as waifu_sum,wallet,(COALESCE(wsum, 0)+wallet) as total
FROM members M
LEFT JOIN (select member_id, sum(purchased_for) as wsum from purchased_waifu group by member_id) PW
ON (M.id = PW.member_id)
WHERE wallet > 0 OR COALESCE(wsum, 0) > 0
ORDER BY total DESC
LIMIT 20;
        """
        cursor = await conn.execute(query)
        results = await cursor.fetchall()
    rtxt = []
    top_user = client.get_user(results[0][1])
    for i, j in enumerate(results):
        user = client.get_user(j[1])
        if i < 3:
            rtxt.append(
                f"**[{str(i+1).zfill(2)}] __{user.name}__**\nWallet: {j[4]}, Waifu Value: {j[3]}, **Total: {j[5]}**")  # noqa
        else:
            rtxt.append(
                f"[{str(i+1).zfill(2)}] {user.name}\nWallet: {j[4]}, Waifu Value: {j[3]}, __Total: {j[5]}__")  # noqa
    txt = '\n'.join(rtxt)
    embed = discord.Embed(
        title="World Leaderboards", colour=message.author.colour,
        description=txt)
    embed.set_footer(
        text=f"Current World Champion is {top_user.name}.",
        icon_url=str(top_user.avatar_url_as(size=64)))
    await message.channel.send(embed=embed)


general_functions = {
    'vote': (vote_bot, "Vote for this bot."),
    'claimreward': (claim_rewards, "Claim your voting rewards."),
    'donate': (donate, "Donate money to this bot to keep it running UwU."),
    'creator': (creator, "Get to know the creator of this bot. And annoy him to fix bugs."),
    'invite': (invite, "Get the invite link for the bot."),
    'poll': (poll, "Create a reactions poll."),
    'whois': (whois, "Get info about an user."),
    'discoin': (discoin, "Get info about <:Discoin:357656754642747403> Discoin."),
    'worldleaderboard': (world_leaderboard, "Get this world's leaderboard."),
    'wlb': (world_leaderboard, "Get this world's leaderboard."),
    'worldlb': (world_leaderboard, "Get this world's leaderboard."),
}
