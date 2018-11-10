import database


async def hello_world(client, message, *args):
    await message.channel.send("Heya, {0}. N(args) = {2}. Your args: \"{1}\"".format(
        message.author, args, len(args),
    ))
    perms = message.author.guild_permissions
    admin = perms.administrator
    await message.channel.send(
        "Your guild permissions: \n```{0}```. Admin: {1}".format(perms, admin)
    )


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


def wrapper(func, tier):
    async def f(client, message, *args):
        engine = await database.prepare_engine()
        member = message.author
        async with engine.acquire() as conn:
            fetch_query = database.Member.select().where(
                database.Member.c.member == member.id
            )
            cursor = await conn.execute(fetch_query)
            conn = await cursor.fetchall()
            member_tier = 0
            for m in conn:
                _t = m[database.Member.c.tier]
                if _t > member_tier:
                    member_tier = _t
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
    'helloworld': (wrapper(hello_world, 1), None),
    'botstats': (wrapper(view_stats, 3), None),
}
