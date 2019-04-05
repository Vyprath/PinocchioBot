import database
import discord
import asyncio
from datetime import datetime
from random import randint
from .currency import _fetch_wallet, _remove_money, _add_money
from variables import PREFIX
import variables


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
    resp_string += "\nTo view details, do `{0}waifu details <name/id>`".format(PREFIX)
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
    purchaseable = purchaser is None
    if not purchaseable:
        purchaser_user = message.guild.get_member(purchaser[database.PurchasedWaifu.c.member])
        purchased_for = purchaser[database.PurchasedWaifu.c.purchased_for]
    gender = resp[database.Waifu.c.gender]
    if gender == "m":
        gender = "Husbando"
    elif gender == "f":
        gender = "Waifu"
    else:
        gender = "?????"
    if purchaseable:
        waifu_description = (
            "Hi! I am a {2} from {0}. You need {1} coins to buy me!"
            .format(resp[database.Waifu.c.from_anime], resp[database.Waifu.c.price], gender.lower()))
    else:
        waifu_description = (
        "Hi! I am a {1} from {0}. I am already in a relationship with {2}#{3}."  # noqa
            .format(resp[database.Waifu.c.from_anime], gender.lower(),
                    purchaser_user.name, purchaser_user.discriminator))
    embed = discord.Embed(
        title=resp[database.Waifu.c.name], description=waifu_description,
        type='rich', color=message.author.colour)
    if resp[database.Waifu.c.image_url] is not None:
        embed.set_image(url=resp[database.Waifu.c.image_url])
    embed.add_field(name="From", value=resp[database.Waifu.c.from_anime])
    embed.add_field(name="Cost", value=resp[database.Waifu.c.price])
    embed.add_field(name="ID", value=resp[database.Waifu.c.id])
    embed.add_field(name="Gender", value=gender)
    if purchaser is not None:
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
        cost = purchased_waifu[database.PurchasedWaifu.c.purchased_for] * variables.SELL_WAIFU_DEPRECIATION
        cost = int(cost)
        await message.channel.send(
            "Want to sell for sure? You will get back {0}% of the cost, {1} coins. Reply with `confirm` in 60s or `exit`.".format(  # noqa
                variables.SELL_WAIFU_DEPRECIATION * 100, cost))

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


async def _trade(client, message, *args):
    engine = await database.prepare_engine()
    if len(message.mentions) == 0:
        await message.channel.send("Usage: {0}waifu trade <@user mention>".format(PREFIX))
        return
    recipient = message.mentions[0]
    giver = message.author
    async with engine.acquire() as conn:
        def check_recpt(m):
            return (m.author.id != client.user.id and
                    m.channel == message.channel and recipient.id == m.author.id)

        def check_giver(m):
            return (m.author.id != client.user.id and
                    m.channel == message.channel and giver.id == m.author.id)

        try:
            await message.channel.send("Enter the name or ID of the waifu you want to trade:")
            msg = await client.wait_for('message', check=check_giver, timeout=120)
            waifu_name = msg.content
            if waifu_name.isdigit():
                search_id = int(waifu_name)
                query = database.Waifu.select().where(
                    database.Waifu.c.id == search_id)
            else:
                search_string = '%' + waifu_name.lower().strip() + '%'
                query = database.Waifu.select().where(
                    database.Waifu.c.name.ilike(search_string))
            cursor = await conn.execute(query)
            resp = await cursor.fetchone()
            if resp is None:
                await message.channel.send(
                    "Waifu not found! Don't trade your imaginary waifus.")
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
                    "By what logic are you trying to trade a waifu you don't own? :rolling_eyes:")
                return
            await message.channel.send("Enter the price you wish to trade this waifu for:")
            msg = await client.wait_for('message', check=check_giver, timeout=120)
            if not msg.content.isdigit():
                await message.channel.send("Not a valid price.")
                return
            price = int(msg.content)
            wallet = await _fetch_wallet(engine, recipient)
            if wallet - price < 0:
                await message.channel.send(
                    "The recipient does not have enough money to finish this trade.")
                return
            await message.channel.send(
                "{0}, do you wish to get {1} from {2} for {3} coins? Type `confirm` or `exit`."
                .format(recipient.mention, resp[database.Waifu.c.name],
                        giver.mention, price))
            msg = await client.wait_for('message', check=check_recpt, timeout=120)
            if msg.content == 'confirm':
                pass
            elif msg.content == 'exit':
                await message.channel.send("Okay, exiting...")
                return
            else:
                await message.channel.send("Invalid response. Exiting...")
                return
        except asyncio.TimeoutError:
            await message.channel.send('Error: Timeout.')
            return
        delete_query = database.PurchasedWaifu.delete().where(
            database.PurchasedWaifu.c.waifu_id == purchased_waifu[database.PurchasedWaifu.c.waifu_id]  # noqa
        ).where(
            database.PurchasedWaifu.c.member_id == purchased_waifu[database.PurchasedWaifu.c.member_id]  # noqa
        )
        await conn.execute(delete_query)
        await _add_money(engine, giver, price)
        await _remove_money(engine, recipient, price)
        fetch_query = database.Member.select().where(
            database.Member.c.member == recipient.id
        )
        cursor = await conn.execute(fetch_query)
        buyer = await cursor.fetchone()
        create_query = database.PurchasedWaifu.insert().values([{
            'member_id': buyer[database.Member.c.id],
            'waifu_id': resp[database.Waifu.c.id],
            'guild': message.guild.id,
            'member': buyer[database.Member.c.member],
            'purchased_for': price,
        }])
        await conn.execute(create_query)
        await message.channel.send("Trade successful :thumbsup:.")


async def waifu(client, message, *args):
    if len(args) > 1 and args[0] == 'search':
        return await _search(client, message, *args)
    elif len(args) > 1 and args[0] == 'details':
        return await _details(client, message, *args)
    elif len(args) > 1 and args[0] == 'buy':
        return await _buy(client, message, *args)
    elif len(args) > 1 and args[0] == 'sell':
        return await _sell(client, message, *args)
    elif len(args) > 1 and args[0] == 'trade':
        return await _trade(client, message, *args)
    else:
        await message.channel.send("""Usage:
`{0}waifu search <name>`: Search for a waifu
`{0}waifu details <name/id>`: Get the details for a waifu
`{0}waifu buy <name/id>`: Buy a waifu
`{0}waifu sell <name/id>`: Sell your waifu
`{0}waifu trade <@user mention>`: Trade your waifu with others for money.
`{0}harem`: Get your harem, aka your bought waifus.
        """.format(PREFIX))
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
    resp_string += "\nTo view details, do `{0}waifu details <name/id>`".format(PREFIX)
    await message.channel.send(resp_string)


async def harem(client, message, *args):
    if len(args) == 0:
        await _harem(client, message, message.author)
    elif len(args) == 1 and len(message.mentions) == 1:
        await _harem(client, message, message.mentions[0])
    else:
        await message.channel.send(
            "View your or others' harem list with `{0}harem [user mention]`.".format(PREFIX))


random_waifu_counter = {}


async def random_waifu(client, message, *args):
    engine = await database.prepare_engine()
    member = message.author
    async with engine.acquire() as conn:
        fetch_query = database.Member.select().where(
            database.Member.c.member == member.id
        )
        cursor = await conn.execute(fetch_query)
        resp = await cursor.fetchone()
    member_tier = resp[database.Member.c.tier]
    if member_tier >= variables.DEV_TIER:
        total_rolls = 3*3600  # Virtually unlimited for devs, lol.
    elif member_tier >= variables.DONATOR_TIER_2:
        total_rolls = 90
    elif member_tier >= variables.DONATOR_TIER_1:
        total_rolls = 30
    else:
        total_rolls = 10
    rolls_left = total_rolls
    last_roll = None
    if member.id in random_waifu_counter.keys():
        last_roll = random_waifu_counter[member.id][1]
        last_roll_interval = datetime.now() - last_roll
        if last_roll_interval.seconds + last_roll_interval.days*24*3600 < variables.ROLL_INTERVAL:
            rolls_left = total_rolls - random_waifu_counter[member.id][0]
    else:
        random_waifu_counter.update({member.id: (0, datetime.now())})
    if rolls_left < 1:
        s = variables.ROLL_INTERVAL - (datetime.now() - last_roll).seconds
        h = s // 3600
        m = s // 60 - h*60
        await message.channel.send(
            """
You have no rolls left! Rolls reset in {0:02d} hours {1:02d} minutes. You can donate to me and get more rolls!
""".format(h, m))
        return
    random_waifu_counter.update({member.id: (total_rolls - rolls_left + 1, datetime.now())})
    async with engine.acquire() as conn:
        count_query = database.Waifu.count()
        cur = await conn.execute(count_query)
        resp = await cur.fetchone()
        wid = randint(1, resp[0])
        query = database.Waifu.select().where(
            database.Waifu.c.id == wid)
        cursor = await conn.execute(query)
        resp = await cursor.fetchone()
        query = database.PurchasedWaifu.select().where(
            database.PurchasedWaifu.c.waifu_id == resp[database.Waifu.c.id]
        ).where(
            database.PurchasedWaifu.c.guild == message.guild.id)
        cursor = await conn.execute(query)
        purchaser = await cursor.fetchone()
        if purchaser is not None:
            purchaser_user = message.guild.get_member(purchaser[database.PurchasedWaifu.c.member])
            purchased_for = purchaser[database.PurchasedWaifu.c.purchased_for]
        purchaseable = purchaser is None
        gender = resp[database.Waifu.c.gender]
        if gender == "m":
            gender = "Husbando"
        elif gender == "f":
            gender = "Waifu"
        else:
            gender = "?????"
        price = int(resp[database.Waifu.c.price] * variables.PRICE_CUT)
        if purchaseable:
            waifu_description = (
                "Hi! I am a {2} from {0}. You need {1} coins to buy me! React with the :heart: below to buy me! Hurry up, 10 seconds left."  # noqa
                .format(resp[database.Waifu.c.from_anime], price, gender.lower()))
        else:
            waifu_description = (
                "Hi! I am a {1} from {0}. I am already in a relationship with {2}#{3}."  # noqa
                .format(resp[database.Waifu.c.from_anime], gender.lower(),
                        purchaser_user.name, purchaser_user.discriminator))
        embed = discord.Embed(
            title=resp[database.Waifu.c.name], description=waifu_description,
            type='rich', color=message.author.colour)
        if resp[database.Waifu.c.image_url] is not None:
            embed.set_image(url=resp[database.Waifu.c.image_url])
        embed.add_field(name="From", value=resp[database.Waifu.c.from_anime])
        embed.add_field(name="Cost", value=price)
        embed.add_field(name="ID", value=resp[database.Waifu.c.id])
        embed.add_field(name="Gender", value=gender)
        if not purchaseable:
            embed.set_footer(
                text="Purchased by {0} for {1} coins.".format(purchaser_user.name, purchased_for),
                icon_url=purchaser_user.avatar_url_as(size=128))
        roll_msg = await message.channel.send(embed=embed)
        if not purchaseable:
            return
        await roll_msg.add_reaction("❤")

        def check(reaction, user):
            return (not user.bot
                    and reaction.message.channel == message.channel
                    and reaction.message.id == roll_msg.id)

        try:
            reaction, purchaser = await client.wait_for('reaction_add', timeout=10.0, check=check)
            if not (str(reaction.emoji) == '❤'):
                embed.description = "Oh no! You were too late to buy me. Bye bye."
                await roll_msg.remove_reaction("❤", client.user)
                await roll_msg.edit(embed=embed)
                return
        except asyncio.TimeoutError:
            embed.description = "Oh no! You were too late to buy me. Bye bye."
            await roll_msg.remove_reaction("❤", client.user)
            await roll_msg.edit(embed=embed)
            return
        wallet = await _fetch_wallet(engine, purchaser)
        if wallet - price < 0:
            embed.description = "Don't buy me if you don't have the money :angry:, bye."
            await roll_msg.edit(embed=embed)
            await message.channel.send("You do not have enough money :angry:")
            return
        await _remove_money(engine, purchaser, price)
        fetch_query = database.Member.select().where(
            database.Member.c.member == purchaser.id
        )
        cursor = await conn.execute(fetch_query)
        buyer = await cursor.fetchone()
        create_query = database.PurchasedWaifu.insert().values([{
            'member_id': buyer[database.Member.c.id],
            'waifu_id': resp[database.Waifu.c.id],
            'guild': message.guild.id,
            'member': buyer[database.Member.c.member],
            'purchased_for': price,
        }])
        await conn.execute(create_query)
        embed.description = "I am now in a relationship with {}!".format(purchaser.name)
        await roll_msg.edit(embed=embed)
        await message.channel.send(
            "Successfully bought waifu at an unbelievable price :thumbsup:. Don't lewd them!")


async def rolls_left(client, message, *args):
    engine = await database.prepare_engine()
    member = message.author
    async with engine.acquire() as conn:
        fetch_query = database.Member.select().where(
            database.Member.c.member == member.id
        )
        cursor = await conn.execute(fetch_query)
        resp = await cursor.fetchone()
    member_tier = resp[database.Member.c.tier]
    if member_tier >= variables.DEV_TIER:
        total_rolls = 3*3600  # Virtually unlimited for devs, lol.
    elif member_tier >= variables.DONATOR_TIER_2:
        total_rolls = 45
    elif member_tier >= variables.DONATOR_TIER_1:
        total_rolls = 20
    else:
        total_rolls = 10
    rolls_left = total_rolls
    last_roll = None
    if member.id in random_waifu_counter.keys():
        last_roll = random_waifu_counter[member.id][1]
        last_roll_interval = datetime.now() - last_roll
        if last_roll_interval.seconds + last_roll_interval.days*24*3600 < variables.ROLL_INTERVAL:
            rolls_left = total_rolls - random_waifu_counter[member.id][0]
    else:
        random_waifu_counter.update({member.id: (0, datetime.now())})
    s = variables.ROLL_INTERVAL - (datetime.now() - last_roll).seconds
    h = s // 3600
    m = s // 60 - h*60
    rolls_left_txt = "no" if rolls_left < 1 else rolls_left
    await message.channel.send("""
You have {2} rolls left! Please try again in {0:02d} hours {1:02d} minutes. You can donate to me and get more rolls!
    """.format(h, m, rolls_left_txt))


waifu_functions = {
    'waifu': (waifu, "For your loneliness."),
    'harem': (harem, "Your waifu list. Now go, show off."),
    'randomwaifu': (random_waifu, "Get a random waifu/husbando for cheap."),
    'rw': (random_waifu, "Get a random waifu/husbando for cheap."),
    'randomroll': (random_waifu, "Get a random waifu/husbando for cheap."),
    'rr': (random_waifu, "Get a random waifu/husbando for cheap."),
    'rolls': (rolls_left, "Rolls left for random waifus.")
}
