import database
import discord


async def _search(client, message, *args):
    engine = await database.prepare_engine()
    search_string = '%' + ' '.join(args[1:]).lower().strip() + '%'
    async with engine.acquire() as conn:
        query = database.Waifu.select().where(
            database.Waifu.c.name.ilike(search_string))
        cursor = await conn.execute(query)
        resp = await cursor.fetchall()
    if resp is None or len(resp) == 0:
        await message.channel.send(
            "Waifu not found! Contact developer, he will add it.")
        return
    resp_string = "{0} found in the dungeon:\n".format(len(resp))
    for row in resp:
        resp_string += (
            "**{0}**: ID is {1}, from *{2}*. Costs **{3}** coins.\n".
            format(row[1], row[0], row[2], row[3])
        )
        if len(resp_string) > 1600:
            await message.channel.send(resp_string)
            resp_string = ""
    resp_string += "\nTo view details, do `!waifu details <name/id>`"
    await message.channel.send(resp_string)


async def _details(client, message, *args):
    engine = await database.prepare_engine()
    async with engine.acquire() as conn:
        if len(args) == 2 and args[1].isdigit():
            search_id = int(args[1])
            query = database.Waifu.select().where(
                database.Waifu.c.id == search_id)
        else:
            search_string = '%' + ' '.join(args[1:]).lower().strip() + '%'
            query = database.Waifu.select().where(
                database.Waifu.c.name.ilike(search_string))
        cursor = await conn.execute(query)
        resp = await cursor.fetchone()
    if resp is None:
        await message.channel.send(
            "Waifu not found! Contact developer, he will add it.")
        return
    waifu_description = (
        "Hi! I am a waifu from {0}. You need {1} to buy me!"
        .format(resp[2], resp[3]))
    embed = discord.Embed(
        title=resp[1], description=waifu_description,
        type='rich', color=0x000000)
    if resp[4] is not None:
        embed.set_image(url=resp[4])
    embed.add_field(name="From", value=resp[2])
    embed.add_field(name="Cost", value=resp[3])
    await message.channel.send(embed=embed)


async def waifu(client, message, *args):
    if len(args) > 1 and args[0] == 'search':
        return await _search(client, message, *args)
    elif len(args) > 1 and args[0] == 'details':
        return await _details(client, message, *args)
    else:
        await message.channel.send("""Usage:
!waifu search <name>
!waifu details <name/id>
!waifu buy <name/id>
!waifu sell <name/id>
!waifu trade <user to trade with> <waifu name/id> <price>
""")
        return


waifu_functions = {
    'waifu': (waifu, "For your loneliness.")
}
