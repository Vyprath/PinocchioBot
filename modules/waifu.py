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
    purchaser_user = None
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
        if purchaser_user is not None:
            rstatus = 'deep' if purchaser[database.PurchasedWaifu.c.favorite] else 'casual'
            waifu_description = (
                "Hi! I am a {1} from {0}. I am already in a {4} relationship with {2}#{3}."  # noqa
                .format(resp[database.Waifu.c.from_anime], gender.lower(),
                        purchaser_user.name, purchaser_user.discriminator, rstatus))
        else:
            waifu_description = (
                "Hi! I am a {1} from {0}. I was purchased an abandoned by someone who left this server. Rescue me with `=rescuewaifus`."  # noqa
                .format(resp[database.Waifu.c.from_anime], gender.lower()))
    embed = discord.Embed(
        title=resp[database.Waifu.c.name], description=waifu_description,
        type='rich', color=message.author.colour)
    curr_img = -1
    images = []
    if resp[database.Waifu.c.image_url] is not None:
        images = resp[database.Waifu.c.image_url].split(",")
        embed.set_image(url=images[0])
        curr_img = 0
    embed.add_field(name="From", value=resp[database.Waifu.c.from_anime])
    embed.add_field(name="Cost", value=resp[database.Waifu.c.price])
    embed.add_field(name="ID", value=resp[database.Waifu.c.id])
    embed.add_field(name="Gender", value=gender)
    image_field_id = 4
    if purchaser_user and purchaser[database.PurchasedWaifu.c.favorite]:
        embed.add_field(name="Favorite", inline=False,
                        value="Purchaser's favorite waifu :heart:")
        image_field_id += 1
    if len(images) > 1:
        embed.add_field(
            name="Image", inline=False,
            value=f"**Showing: {curr_img+1}/{len(images)}**")
    if purchaser is not None:
        if purchaser_user is not None:
            embed.set_footer(
                text="Purchased by {0} for {1} coins.".format(purchaser_user.name, purchased_for),
                icon_url=purchaser_user.avatar_url_as(size=128))
        else:
            embed.set_footer(
                text="Purchased by someone who left for {0} coins.".format(purchased_for))
    detail_msg = await message.channel.send(embed=embed)
    if len(images) <= 1:
        return
    await detail_msg.add_reaction("⬅")
    await detail_msg.add_reaction("➡")

    def check(reaction, user):
        return (not user.bot
                and reaction.message.channel == message.channel
                and reaction.message.id == detail_msg.id)
    seen = False
    try:
        while not seen:
            reaction, purchaser = await client.wait_for(
                'reaction_add', timeout=120.0, check=check)
            if str(reaction.emoji) == '➡' and len(images) > 1:
                if curr_img < len(images) - 1:
                    curr_img += 1
                    embed.set_image(url=images[curr_img])
                    embed.set_field_at(
                        index=image_field_id, name="Image", inline=False,
                        value=f"**Showing: {curr_img+1}/{len(images)}**")
                    await detail_msg.edit(embed=embed)
                await detail_msg.remove_reaction('➡', purchaser)
            elif str(reaction.emoji) == '⬅' and len(images) > 1:
                if curr_img > 0:
                    curr_img -= 1
                    embed.set_image(url=images[curr_img])
                    embed.set_field_at(
                        index=image_field_id, name="Image", inline=False,
                        value=f"**Showing: {curr_img+1}/{len(images)}**")
                    await detail_msg.edit(embed=embed)
                await detail_msg.remove_reaction('⬅', purchaser)
            else:
                continue
    except asyncio.TimeoutError:
        await detail_msg.remove_reaction("⬅", client.user)
        await detail_msg.remove_reaction("➡", client.user)
        return



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


async def _favorite(client, message, *args, unfavorite=False):
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
                "Waifu not found! Don't mark your imaginary waifus as favorite.")
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
                "You can't mark an un-owned waifu as favorite!")
            return
        update_query = database.PurchasedWaifu.update().where(
            database.PurchasedWaifu.c.id == purchased_waifu[database.PurchasedWaifu.c.id]
        ).values(favorite=not unfavorite)
        await conn.execute(update_query)
        if not unfavorite:
            await message.channel.send("Successfully marked waifu as favorite! :heart:")  # noqa
        else:
            await message.channel.send("Successfully marked waifu as unfavorite! :broken_heart:")  # noqa


async def _direct_trade(client, message, *args):
    engine = await database.prepare_engine()
    if len(message.mentions) == 0:
        await message.channel.send("Usage: {0}waifu trade <@user mention>".format(PREFIX))
        return
    recipient = message.mentions[0]
    giver = message.author
    async with engine.acquire() as conn:
        def check_user(user):
            def _check(m):
                return (m.author.id != client.user.id and
                        m.channel == message.channel and user.id == m.author.id)
            return _check

        try:
            await message.channel.send(
                f"{giver.mention}, enter the name or ID of the waifu you want to trade:")
            msg = await client.wait_for('message', check=check_user(giver), timeout=120)
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
            giver_waifu = await cursor.fetchone()
            if giver_waifu is None:
                await message.channel.send(
                    "Waifu not found! Don't trade your imaginary waifus.")
                return
            query = database.PurchasedWaifu.select().where(
                database.PurchasedWaifu.c.waifu_id == giver_waifu[database.Waifu.c.id]
            ).where(
                database.PurchasedWaifu.c.guild == message.guild.id
            ).where(
                database.PurchasedWaifu.c.member == giver.id)
            cursor = await conn.execute(query)
            giver_pwaifu = await cursor.fetchone()
            if giver_pwaifu is None:
                await message.channel.send(
                    "By what logic are you trying to trade a waifu you don't own? :rolling_eyes:")
                return
            await message.channel.send(
                f"{recipient.mention}, enter the name or ID of the waifu you want to trade:")
            msg = await client.wait_for('message', check=check_user(recipient), timeout=120)
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
            recipient_waifu = await cursor.fetchone()
            if recipient_waifu is None:
                await message.channel.send(
                    "Waifu not found! Don't trade your imaginary waifus.")
                return
            query = database.PurchasedWaifu.select().where(
                database.PurchasedWaifu.c.waifu_id == recipient_waifu[database.Waifu.c.id]
            ).where(
                database.PurchasedWaifu.c.guild == message.guild.id
            ).where(
                database.PurchasedWaifu.c.member == recipient.id)
            cursor = await conn.execute(query)
            recipient_pwaifu = await cursor.fetchone()
            if recipient_pwaifu is None:
                await message.channel.send(
                    "By what logic are you trying to trade a waifu you don't own? :rolling_eyes:")
                return
            await message.channel.send(f"""
{giver.mention} Do you confirm the trade of your {giver_waifu[database.Waifu.c.name]} in exchange for {recipient.mention}'s {recipient_waifu[database.Waifu.c.name]}?
Enter Y/N:
""")
            msg = await client.wait_for('message', check=check_user(giver), timeout=120)
            if msg.content.lower() in ['yes', 'y']:
                pass
            elif msg.content.lower() in ['no', 'n']:
                await message.channel.send("Okay, cancelling trade...")
                return
            else:
                await message.channel.send("Invalid option. Exiting...")
                return
        except asyncio.TimeoutError:
            await message.channel.send('Error: Timeout.')
            return
        delete_query = database.PurchasedWaifu.delete().where(
            database.PurchasedWaifu.c.waifu_id == giver_pwaifu[database.PurchasedWaifu.c.waifu_id]  # noqa
        ).where(
            database.PurchasedWaifu.c.member_id == giver_pwaifu[database.PurchasedWaifu.c.member_id]  # noqa
        )
        await conn.execute(delete_query)
        delete_query = database.PurchasedWaifu.delete().where(
            database.PurchasedWaifu.c.waifu_id == recipient_pwaifu[database.PurchasedWaifu.c.waifu_id]  # noqa
        ).where(
            database.PurchasedWaifu.c.member_id == recipient_pwaifu[database.PurchasedWaifu.c.member_id]  # noqa
        )
        await conn.execute(delete_query)
        create_query = database.PurchasedWaifu.insert().values([{
            'member_id': giver_pwaifu[database.PurchasedWaifu.c.member_id],
            'waifu_id': recipient_waifu[database.Waifu.c.id],
            'guild': message.guild.id,
            'member': giver_pwaifu[database.PurchasedWaifu.c.member],
            'purchased_for': 0,
        }])
        await conn.execute(create_query)
        create_query = database.PurchasedWaifu.insert().values([{
            'member_id': recipient_pwaifu[database.PurchasedWaifu.c.member_id],
            'waifu_id': giver_waifu[database.Waifu.c.id],
            'guild': message.guild.id,
            'member': recipient_pwaifu[database.PurchasedWaifu.c.member],
            'purchased_for': 0,
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
        return await _direct_trade(client, message, *args)
    elif len(args) > 1 and args[0] == 'favorite':
        return await _favorite(client, message, *args, unfavorite=False)
    elif len(args) > 1 and args[0] == 'unfavorite':
        return await _favorite(client, message, *args, unfavorite=True)
    else:
        await message.channel.send("""Usage:
`{0}waifu search <name>`: Search for a waifu.
`{0}waifu details <name/id>`: Get the details for a waifu.
`{0}waifu buy <name/id>`: Buy a waifu.
`{0}waifu sell <name/id>`: Sell your waifu.
`{0}waifu trade <@user mention>`: Trade your waifu for others' waifu.
`{0}waifu favorite <waifu name/id>`: Mark a waifu as a favorite.
`{0}waifu unfavorite <waifu name/id>`: Unmark a waifu as a favorite.
`{0}harem [@user mention] [sort option] [gender option] [series name]`: Get your harem, aka your bought waifus. Valid sort options: `name-desc`, `series-desc`, `name-asc`, `series-asc`, `id-asc`, `id-desc`, `price-asc`, `price-desc`. Valid gender options: `waifu`, `husbando`.
        """.format(PREFIX))
        return


def _prepare_harem_page(waifus, waifu_data):
    txt = ""
    for n, row in waifus:
        data = waifu_data[row[database.PurchasedWaifu.c.waifu_id]]
        if not row[database.PurchasedWaifu.c.favorite]:
            txt += (
                "{0}: **__{1}__**\n**ID:** {2}. **Bought For:** {4} coins. **From:** {3}.\n".
                format(n, data[database.Waifu.c.name], data[database.Waifu.c.id],
                       data[database.Waifu.c.from_anime],
                       row[database.PurchasedWaifu.c.purchased_for])
            )
        else:
            txt += (
                "{0}: **__{1}__** :heart:\n**ID:** {2}. **Bought For:** {4} coins. **From:** {3}.\n".
                format(n, data[database.Waifu.c.name], data[database.Waifu.c.id],
                       data[database.Waifu.c.from_anime],
                       row[database.PurchasedWaifu.c.purchased_for])
            )
    return txt


def compare_strings(a, b):
    a = ''.join(e for e in a.lower().strip() if e.isalnum())
    b = ''.join(e for e in b.lower().strip() if e.isalnum())
    return a in b


async def _harem(client, message, member, sort_opt=None, sort_gender=None, series_name=None):
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
        waifu_data = {x[database.Waifu.c.id]: x for x in resp}
    if series_name:
        purchased_waifus = [
            x for x in purchased_waifus
            if compare_strings(
                    series_name,
                    waifu_data[x[database.PurchasedWaifu.c.waifu_id]][database.Waifu.c.from_anime]
            )
        ]
    if sort_opt:
        reverse = False
        if 'desc' in sort_opt:
            reverse = True
        if sort_opt.startswith('id'):
            purchased_waifus.sort(
                key=lambda x: x[database.PurchasedWaifu.c.waifu_id],
                reverse=reverse)
        elif sort_opt.startswith('price'):
            purchased_waifus.sort(
                key=lambda x: x[database.PurchasedWaifu.c.purchased_for],
                reverse=reverse)
        elif sort_opt.startswith('name'):
            tpw = [
                (waifu_data[x[database.PurchasedWaifu.c.waifu_id]][database.Waifu.c.name], x)
                for x in purchased_waifus]
            tpw.sort(reverse=reverse)
            purchased_waifus = [x[1] for x in tpw]
        elif sort_opt.startswith('series'):
            tpw = [
                (waifu_data[x[database.PurchasedWaifu.c.waifu_id]][database.Waifu.c.from_anime], x)
                for x in purchased_waifus]
            tpw.sort(reverse=reverse)
            purchased_waifus = [x[1] for x in tpw]
    if sort_gender:
        if sort_gender == 'waifu':
            purchased_waifus = [
                x for x in purchased_waifus
                if waifu_data[x[database.PurchasedWaifu.c.waifu_id]][database.Waifu.c.gender] == 'f'
            ]
        elif sort_gender == 'husbando':
            purchased_waifus = [
                x for x in purchased_waifus
                if waifu_data[x[database.PurchasedWaifu.c.waifu_id]][database.Waifu.c.gender] == 'm'
            ]
    tpw = [
        (x[database.PurchasedWaifu.c.favorite], x)
        for x in purchased_waifus]
    tpw.sort(reverse=True, key=lambda i: i[0])
    purchased_waifus = [x[1] for x in tpw]
    if len(purchased_waifus) == 0:
        await message.channel.send("No harem found for specified queries.")
        return
    pages = []
    n = 0
    for i in range(0, len(purchased_waifus), 10):
        pages.append(
            [(n+nn+1, j) for nn, j in enumerate(purchased_waifus[i:i+10])]
        )
        n += 10
    curr_page = 0
    embed = discord.Embed(
        title=f"{member.name}'s Harem", color=member.color,
        description=_prepare_harem_page(pages[curr_page], waifu_data))
    embed.add_field(name="Waifus Inside Locker", value=len(purchased_waifus))
    embed.add_field(
        name="Net Harem Value",
        value=str(sum(
            [i[database.PurchasedWaifu.c.purchased_for] for i in purchased_waifus])) + " coins")
    embed.add_field(
        name="\u200b", inline=False,
        value=f"To view details, do `{PREFIX}waifu details <name/id>`")
    embed.set_footer(
        text=f"{member.name}#{member.discriminator} • Page {curr_page+1}/{len(pages)}",
        icon_url=member.avatar_url_as(size=128))
    harem_msg = await message.channel.send(embed=embed)
    if len(pages) == 1:
        return
    await harem_msg.add_reaction("⬅")
    await harem_msg.add_reaction("➡")

    def check(reaction, user):
        return (not user.bot
                and reaction.message.channel == message.channel
                and reaction.message.id == harem_msg.id)
    seen = False
    try:
        while not seen:
            reaction, user = await client.wait_for(
                'reaction_add', timeout=120.0, check=check)
            if str(reaction.emoji) == '➡' and len(pages) > 1:
                if curr_page < len(pages) - 1:
                    curr_page += 1
                    embed.description = _prepare_harem_page(pages[curr_page], waifu_data)
                    embed.set_footer(
                        text=f"{member.name}#{member.discriminator} • Page {curr_page+1}/{len(pages)}",  # noqa
                        icon_url=member.avatar_url_as(size=128))
                    await harem_msg.edit(embed=embed)
                await harem_msg.remove_reaction('➡', user)
            elif str(reaction.emoji) == '⬅' and len(pages) > 1:
                if curr_page > 0:
                    curr_page -= 1
                    embed.description = _prepare_harem_page(pages[curr_page], waifu_data)
                    embed.set_footer(
                        text=f"{member.name}#{member.discriminator} • Page {curr_page+1}/{len(pages)}",  # noqa
                        icon_url=member.avatar_url_as(size=128))
                    await harem_msg.edit(embed=embed)
                await harem_msg.remove_reaction('⬅', user)
            else:
                continue
    except asyncio.TimeoutError:
        await harem_msg.remove_reaction("⬅", client.user)
        await harem_msg.remove_reaction("➡", client.user)
    return


async def harem(client, message, *args):
    args = list(args)
    VALID_SORT_OPTS = [
        'name-desc', 'series-desc', 'name-asc',
        'series-asc', 'id-asc', 'id-desc',
        'price-asc', 'price-desc']
    VALID_GENDER_OPTS = ['waifu', 'husbando']
    matching_sort = None
    matching_gender = None
    x = [i in args for i in VALID_SORT_OPTS]
    if len(x) > 0 and max(x):
        matching_sort = VALID_SORT_OPTS[x.index(True)]
        args.remove(matching_sort)
    x = [i in args for i in VALID_GENDER_OPTS]
    if len(x) > 0 and max(x):
        matching_gender = VALID_GENDER_OPTS[x.index(True)]
        args.remove(matching_gender)
    series_name = None
    if (len(message.mentions) == 0 and len(args) > 0):
        series_name = " ".join(args)
    if (len(message.mentions) == 1 and len(args) > 1):
        series_name = " ".join(args[1:])
    if len(message.mentions) == 0:
        await _harem(
            client, message, message.author,
            matching_sort, matching_gender, series_name)
    if len(message.mentions) == 1:
        await _harem(
            client, message, message.mentions[0],
            matching_sort, matching_gender, series_name)


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
        curr_img = -1
        images = []
        if resp[database.Waifu.c.image_url] is not None:
            images = resp[database.Waifu.c.image_url].split(",")
            embed.set_image(url=images[0])
            curr_img = 0
        embed.add_field(name="From", value=resp[database.Waifu.c.from_anime])
        embed.add_field(name="Cost", value=price)
        embed.add_field(name="ID", value=resp[database.Waifu.c.id])
        embed.add_field(name="Gender", value=gender)
        if len(images) > 1:
            embed.add_field(
                name="Image", inline=False,
                value=f"**Showing: {curr_img+1}/{len(images)}**")
        if not purchaseable:
            embed.set_footer(
                text="Purchased by {0} for {1} coins.".format(purchaser_user.name, purchased_for),
                icon_url=purchaser_user.avatar_url_as(size=128))
        roll_msg = await message.channel.send(embed=embed)
        if purchaseable:
            await roll_msg.add_reaction("❤")
        if len(images) > 1:
            await roll_msg.add_reaction("⬅")
            await roll_msg.add_reaction("➡")

        def check(reaction, user):
            return (not user.bot
                    and reaction.message.channel == message.channel
                    and reaction.message.id == roll_msg.id)
        purchased = False
        try:
            while not purchased:
                reaction, purchaser = await client.wait_for(
                    'reaction_add', timeout=10.0, check=check)
                if str(reaction.emoji) == '❤':
                    purchased = True
                elif str(reaction.emoji) == '➡' and len(images) > 1:
                    if curr_img < len(images) - 1:
                        curr_img += 1
                        embed.set_image(url=images[curr_img])
                        embed.set_field_at(
                            index=4, name="Image", inline=False,
                            value=f"**Showing: {curr_img+1}/{len(images)}**")
                        await roll_msg.edit(embed=embed)
                    await roll_msg.remove_reaction('➡', purchaser)
                elif str(reaction.emoji) == '⬅' and len(images) > 1:
                    if curr_img > 0:
                        curr_img -= 1
                        embed.set_image(url=images[curr_img])
                        embed.set_field_at(
                            index=4, name="Image", inline=False,
                            value=f"**Showing: {curr_img+1}/{len(images)}**")
                        await roll_msg.edit(embed=embed)
                    await roll_msg.remove_reaction('⬅', purchaser)
                else:
                    embed.description = "Oh no! You were too late to buy me. Bye bye."
                    await roll_msg.remove_reaction("❤", client.user)
                    await roll_msg.edit(embed=embed)
                    return
        except asyncio.TimeoutError:
            if not purchaseable:
                await roll_msg.remove_reaction("⬅", client.user)
                await roll_msg.remove_reaction("➡", client.user)
                return
            embed.description = "Oh no! You were too late to buy me. Bye bye."
            await roll_msg.remove_reaction("❤", client.user)
            await roll_msg.remove_reaction("⬅", client.user)
            await roll_msg.remove_reaction("➡", client.user)
            await roll_msg.edit(embed=embed)
            return
        if not purchaseable:
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
        await roll_msg.remove_reaction("⬅", client.user)
        await roll_msg.remove_reaction("➡", client.user)
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
    s = variables.ROLL_INTERVAL - (datetime.now() - last_roll).seconds
    h = s // 3600
    m = s // 60 - h*60
    rolls_left_txt = "no" if rolls_left < 1 else rolls_left
    await message.channel.send("""
You have {2} rolls left! Please try again in {0:02d} hours {1:02d} minutes. You can donate to me and get more rolls!
    """.format(h, m, rolls_left_txt))


waifu_functions = {
    'waifu': (waifu, "`{P}waifu`: Buy/Sell/View/Search/Trade/Favorite/Unfavorite Waifus. Will make your loneliness disappear."),
    'harem': (harem, "`{P}harem [@user mention] [sort option] [gender option] [series name]`: Get the list of your bought waifus. Valid sort options: `name-desc`, `series-desc`, `name-asc`, `series-asc`, `id-asc`, `id-desc`, `price-asc`, `price-desc`. Valid gender options: `waifu`, `husbando`."),
    'randomroll': (random_waifu, "`{P}randomroll`: Get a random waifu/husbando for a very cheap price. Normal users can do it 10 times per 3 hours, tier 1 donators 30 times, and tier 2 donators 90 times."),
    'rr': (random_waifu, "`{P}rr`: Get a random waifu/husbando for a very cheap price. Normal users can do it 10 times per 3 hours, tier 1 donators 30 times, and tier 2 donators 90 times."),
    'rolls': (rolls_left, "`{P}rolls`: Check how many rolls you have left for getting a random waifu. Resets every 3 hours.")
}
