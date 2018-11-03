import database
import discord
from .currency import _fetch_wallet, _remove_money, _add_money


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
        query = database.PurchasedWaifu.select().where(
            database.PurchasedWaifu.c.waifu_id == resp[database.Waifu.c.id]
        ).where(
            database.PurchasedWaifu.c.guild == message.guild.id)
        cursor = await conn.execute(query)
        purchaser = await cursor.fetchone()
    waifu_description = (
        "Hi! I am a waifu from {0}. You need {1} to buy me!"
        .format(resp[2], resp[database.Waifu.c.price]))
    embed = discord.Embed(
        title=resp[database.Waifu.c.name], description=waifu_description,
        type='rich', color=0x000000)
    if resp[4] is not None:
        embed.set_image(url=resp[database.Waifu.c.image_url])
    embed.add_field(name="From", value=resp[2])  # database.Waifu.c.from
    embed.add_field(name="Cost", value=resp[database.Waifu.c.price])
    embed.add_field(name="ID", value=resp[database.Waifu.c.id])
    if purchaser is not None:
        purchaser_user = message.guild.get_member(purchaser[database.PurchasedWaifu.c.member])
        purchased_for = purchaser[database.PurchasedWaifu.c.purchased_for]
        embed.set_footer(
            text="Purchased by {0} for {1} coins.".format(purchaser_user.name, purchased_for),
            icon_url=purchaser_user.avatar_url_as(size=128))
    await message.channel.send(embed=embed)


async def _buy(client, message, *args):
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
        query = database.PurchasedWaifu.select().where(
            database.PurchasedWaifu.c.waifu_id == resp[database.Waifu.c.id]
        ).where(
            database.PurchasedWaifu.c.guild == message.guild.id)
        cursor = await conn.execute(query)
        purchaser = await cursor.fetchone()
        if purchaser is not None:
            purchaser_user = message.guild.get_member(purchaser[database.PurchasedWaifu.c.member])
            if purchaser[database.PurchasedWaifu.c.member] == message.author.id:
                await message.channel.send(
                    "How many more times do you want to buy this waifu? :rolling_eyes:")
                return
            else:
                await message.channel.send("""
                Waifu is already purchased by {0}#{1}. Ask them to sell it or trade with you!
                """.format(purchaser_user.name, purchaser_user.discriminator))
                return
        cost = resp[database.Waifu.c.price]
        wallet = await _fetch_wallet(engine, message.author)
        if wallet - cost < 0:
            await message.channel.send("You do not have enough money :angry:")
            return
        await _remove_money(engine, message.author, cost)
        fetch_query = database.Member.select().where(
            database.Member.c.member == message.author.id
        ).where(
            database.Member.c.guild == message.guild.id
        )
        cursor = await conn.execute(fetch_query)
        buyer = await cursor.fetchone()
        create_query = database.PurchasedWaifu.insert().values([{
            'member_id': buyer[database.Member.c.id],
            'waifu_id': resp[database.Waifu.c.id],
            'guild': message.guild.id,
            'member': buyer[database.Member.c.member],
            'purchased_for': cost,
        }])
        await conn.execute(create_query)
        await message.channel.send("Successfully bought waifu :thumbsup:. Don't lewd them!")


async def waifu(client, message, *args):
    if len(args) > 1 and args[0] == 'search':
        return await _search(client, message, *args)
    elif len(args) > 1 and args[0] == 'details':
        return await _details(client, message, *args)
    elif len(args) > 1 and args[0] == 'buy':
        return await _buy(client, message, *args)
    else:
        await message.channel.send("""Usage:
!waifu search <name>
!waifu details <name/id>
!waifu buy <name/id>
!waifu sell <name/id> *not yet implemented
!waifu trade <user to trade with> <waifu name/id> <price> *not yet implemented
""")
        return


waifu_functions = {
    'waifu': (waifu, "For your loneliness.")
}
