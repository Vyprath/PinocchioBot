import database
import discord
import asyncio
from .currency import _fetch_wallet, _remove_money, _add_money
from variables import SELL_WAIFU_DEPRECIATION


async def _search(client, message, *args):
    search_string = '%' + ' '.join(args[1:]).lower().strip() + '%'
    if len(search_string) < 5:
        await message.channel.send("Please enter atleast 3 or more characters.")
        return
    engine = await database.prepare_engine()
    async with engine.acquire() as conn:
        query = database.Waifu.select().where(
            database.Waifu.c.name.ilike(search_string) |
            database.Waifu.c.from_anime.ilike(search_string))
        cursor = await conn.execute(query)
        resp = await cursor.fetchall()
        if resp is None or len(resp) == 0:
            await message.channel.send(
                "Waifu not found! Contact developer, he will add it.")
            return
        if len(resp) > 15:
            resp = resp[:15]
    resp_string = "{0} found in the dungeon:\n".format(len(resp))
    for row in resp:
        resp_string += (
            "**{0}**: ID is {1}, from *{2}*. Costs **{3}** coins.\n".
            format(row[database.Waifu.c.name], row[database.Waifu.c.id],
                   row[database.Waifu.c.from_anime], row[database.Waifu.c.price])
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
    gender = resp[database.Waifu.c.gender]
    if gender == "m":
        gender = "Husbando"
    elif gender == "f":
        gender = "Waifu"
    else:
        gender = "?????"
    waifu_description = (
        "Hi! I am a {2} from {0}. You need {1} to buy me!"
        .format(resp[database.Waifu.c.from_anime], resp[database.Waifu.c.price], gender.lower()))
    embed = discord.Embed(
        title=resp[database.Waifu.c.name], description=waifu_description,
        type='rich', color=0x4f00f2)
    if resp[4] is not None:
        embed.set_image(url=resp[database.Waifu.c.image_url])
    embed.add_field(name="From", value=resp[database.Waifu.c.from_anime])
    embed.add_field(name="Cost", value=resp[database.Waifu.c.price])
    embed.add_field(name="ID", value=resp[database.Waifu.c.id])
    embed.add_field(name="Gender", value=gender)
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
        await message.channel.send("Want to buy for sure? Reply with `confirm` in 60s or `exit`.")

        def check(m):
            return (m.author.id != client.user.id and
                    m.channel == message.channel and message.author.id == m.author.id)
        sure = False
        while not sure:
            try:
                msg = await client.wait_for('message', check=check, timeout=60)
                if msg.content == 'confirm':
                    sure = True
                elif msg.content == 'exit':
                    await message.channel.send("Okay, exiting...")
                    return
                else:
                    await message.channel.send("Respond properly. Write `exit` to exit.")
            except asyncio.TimeoutError:
                await message.channel.send('Error: Timeout.')
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


async def _sell(client, message, *args):
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
                "Waifu not found! Don't sell your imaginary waifus.")
            return
        query = database.PurchasedWaifu.select().where(
            database.PurchasedWaifu.c.waifu_id == resp[database.Waifu.c.id]
        ).where(
            database.PurchasedWaifu.c.guild == message.guild.id
        ).where(
            database.PurchasedWaifu.c.member == message.author.id)
        cursor = await conn.execute(query)
        purchased_waifu = await cursor.fetchone()
        if purchased_waifu is None:
            await message.channel.send(
                "By what logic are you trying to sell a waifu you don't own? :rolling_eyes:")
            return
        cost = purchased_waifu[database.PurchasedWaifu.c.purchased_for] * SELL_WAIFU_DEPRECIATION
        cost = int(cost)
        await message.channel.send(
            "Want to sell for sure? You will get back {0}% of the cost, {1} coins. Reply with `confirm` in 60s or `exit`.".format(  # noqa
                SELL_WAIFU_DEPRECIATION * 100, cost))

        def check(m):
            return (m.author.id != client.user.id and
                    m.channel == message.channel and message.author.id == m.author.id)
        sure = False
        while not sure:
            try:
                msg = await client.wait_for('message', check=check, timeout=60)
                if msg.content == 'confirm':
                    sure = True
                elif msg.content == 'exit':
                    await message.channel.send("Okay, exiting...")
                    return
                else:
                    await message.channel.send("Respond properly. Write `exit` to exit.")
            except asyncio.TimeoutError:
                await message.channel.send('Error: Timeout.')
                return
        delete_query = database.PurchasedWaifu.delete().where(
            database.PurchasedWaifu.c.waifu_id == purchased_waifu[database.PurchasedWaifu.c.waifu_id]  # noqa
        ).where(
            database.PurchasedWaifu.c.member_id == purchased_waifu[database.PurchasedWaifu.c.member_id]  # noqa
        )
        await conn.execute(delete_query)
        await _add_money(engine, message.author, cost)
        await message.channel.send("Successfully transferred waifu from your locker to the dungeon :thumbsup:.")  # noqa


async def waifu(client, message, *args):
    if len(args) > 1 and args[0] == 'search':
        return await _search(client, message, *args)
    elif len(args) > 1 and args[0] == 'details':
        return await _details(client, message, *args)
    elif len(args) > 1 and args[0] == 'buy':
        return await _buy(client, message, *args)
    elif len(args) > 1 and args[0] == 'sell':
        return await _sell(client, message, *args)
    else:
        await message.channel.send("""Usage:
`!waifu search <name>`: Search for a waifu
`!waifu details <name/id>`: Get the details for a waifu
`!waifu buy <name/id>`: Buy a waifu
`!waifu sell <name/id>`: Sell your waifu
`!waifu trade <user to trade with> <waifu name/id> <price>`: Trade your waifus with someone **not yet implemented**
`!harem`: Get your harem, aka your bought waifus.
""")
        return


async def _harem(client, message, member):
    engine = await database.prepare_engine()
    async with engine.acquire() as conn:
        query = database.PurchasedWaifu.select().where(
            database.PurchasedWaifu.c.member == member.id
        ).where(
            database.PurchasedWaifu.c.guild == message.guild.id)
        cursor = await conn.execute(query)
        resp = await cursor.fetchall()
        if resp is None or len(resp) == 0:
            await message.channel.send(
                "{0}#{1} does not have a harem. Lonely life :(".format(
                    member.name, member.discriminator)
            )
            return
        purchased_waifus = resp
        waifu_ids = [x[database.PurchasedWaifu.c.waifu_id] for x in purchased_waifus]
        query = database.Waifu.select().where(database.Waifu.c.id.in_(waifu_ids))
        cursor = await conn.execute(query)
        resp = await cursor.fetchall()
        waifus = {x[database.Waifu.c.id]: x for x in resp}
    resp_string = "{0} found in {1}'s locker:\n".format(len(purchased_waifus), member.name)
    for row in purchased_waifus:
        data = waifus[row[database.PurchasedWaifu.c.waifu_id]]
        resp_string += (
            "**{0}**: ID is {1}, from *{2}*. Bought for **{3}** coins.\n".
            format(data[database.Waifu.c.name], data[database.Waifu.c.id],
                   data[database.Waifu.c.from_anime], row[database.PurchasedWaifu.c.purchased_for])
        )
        if len(resp_string) > 1600:
            await message.channel.send(resp_string)
            resp_string = ""
    resp_string += "\nTo view details, do `!waifu details <name/id>`"
    await message.channel.send(resp_string)


async def harem(client, message, *args):
    if len(args) == 0:
        await _harem(client, message, message.author)
    elif len(args) == 1 and len(message.mentions) == 1:
        await _harem(client, message, message.mentions[0])
    else:
        await message.channel.send("View your or others' harem list with `!harem [user mention]`.")


waifu_functions = {
    'waifu': (waifu, "For your loneliness."),
    'harem': (harem, "Your waifu list. Now go, show off."),
}
