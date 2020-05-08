import database
import discord
import asyncio
import time
from datetime import datetime
from random import randint
from .currency import _fetch_wallet, _remove_money, _add_money
from .utils import paginate_embed
from variables import PREFIX
import variables


async def search(client, message, *args):
    if len(args) < 1:
        await message.channel.send(
            f"USAGE: `{PREFIX}search`: <waifu name or ID or anime name>"
        )
        return
    search_string = "%" + " ".join(args).lower().strip() + "%"
    if len(search_string) < 5:
        await message.channel.send("Please enter atleast 3 or more characters!")
        return
    engine = await database.prepare_engine()
    async with engine.acquire() as conn:
        query = database.Waifu.select().where(
            database.Waifu.c.name.ilike(search_string)
            | database.Waifu.c.from_anime.ilike(search_string)
        )
        cursor = await conn.execute(query)
        resp = await cursor.fetchall()
        if resp is None or len(resp) == 0:
            await message.channel.send(
                "Waifu not found! You can add the waifu yourself, please join the support server! (`=support`) <a:thanks:699004469610020964>"
            )
            return
        resp = resp[:30]
    pages = []
    resp_string = ""
    for row in resp:
        resp_string += "**{0}**: ID is {1}, from *{2}*. Costs **{3}** <:PIC:668725298388271105>\n".format(
            row[database.Waifu.c.name],
            row[database.Waifu.c.id],
            row[database.Waifu.c.from_anime],
            row[database.Waifu.c.price],
        )
        if len(resp_string) > 1900:
            pages.append(resp_string)
            resp_string = ""
    if resp_string != "":
        pages.append(resp_string)
    embed = discord.Embed(
        title=f"{len(resp)} Waifus Found in the Dungeon!\n",
        description=pages[0],
        color=message.author.colour,
    )
    if len(pages) > 1:
        embed.add_field(name="Page Number", value=f"1/{len(pages)}")
    embed.set_footer(text=f"To view details, do {PREFIX}details <name/id>")

    async def modifier_func(type, curr_page):
        embed.description = pages[curr_page]
        embed.set_field_at(
            index=0, name="Page Number", value=f"{curr_page+1}/{len(pages)}"
        )

    await paginate_embed(client, message.channel, embed, len(pages), modifier_func)


async def details(client, message, *args):
    if len(args) < 1:
        await message.channel.send(f"USAGE: `{PREFIX}details`: <waifu name or ID>")
        return
    engine = await database.prepare_engine()
    async with engine.acquire() as conn:
        if len(args) == 1 and args[0].isdigit():
            search_id = int(args[0])
            query = database.Waifu.select().where(database.Waifu.c.id == search_id)
        else:
            search_string = "%" + " ".join(args).lower().strip() + "%"
            query = database.Waifu.select().where(
                database.Waifu.c.name.ilike(search_string)
            )
        cursor = await conn.execute(query)
        resp = await cursor.fetchone()
        if resp is None:
            await message.channel.send(
                "Waifu not found! You can add the waifu yourself, please join the support server! (`=support`) <a:thanks:699004469610020964>"
            )
            return
        query = (
            database.PurchasedWaifu.select()
            .where(database.PurchasedWaifu.c.waifu_id == resp[database.Waifu.c.id])
            .where(database.PurchasedWaifu.c.guild == message.guild.id)
        )
        cursor = await conn.execute(query)
        purchaser = await cursor.fetchone()
    purchaseable = purchaser is None
    purchaser_user = None
    if not purchaseable:
        purchaser_user = message.guild.get_member(
            purchaser[database.PurchasedWaifu.c.member]
        )
        purchased_for = purchaser[database.PurchasedWaifu.c.purchased_for]
    gender = resp[database.Waifu.c.gender]
    if gender == "m":
        gender = "Husbando"
    elif gender == "f":
        gender = "Waifu"
    else:
        gender = "??Trap??"
    from_anime = resp[database.Waifu.c.from_anime]
    coins_req = resp[database.Waifu.c.price]
    gender = gender.lower()
    waifu_description = resp[database.Waifu.c.description]
    if waifu_description is None or waifu_description == "":
        waifu_description = f"Hi! I am a {gender} from {from_anime}."
    if len(waifu_description) > 1900:
        waifu_description = waifu_description[:1900] + "..."
    waifu_description = waifu_description.replace("\\n", "\n")
    if purchaseable:
        waifu_description += (
            f"\n\nYou need {coins_req} <:PIC:668725298388271105> to buy them."
        )
    else:
        if purchaser_user is not None:
            rstatus = (
                "deep" if purchaser[database.PurchasedWaifu.c.favorite] else "casual"
            )
            waifu_description += f"\n\nThey are already in a {rstatus} relationship with {str(purchaser_user)}."
        else:
            waifu_description += f"\n\nThey were purchased and abandoned by someone who left this server. Rescue them with `{PREFIX}rescuewaifus`!"
    embed = discord.Embed(
        title=resp[database.Waifu.c.name],
        description=waifu_description,
        color=message.author.colour,
    )
    images = []
    if resp[database.Waifu.c.image_url] is not None:
        images = resp[database.Waifu.c.image_url].split(",")
        embed.set_image(url=images[0])
    embed.add_field(name="From", value=resp[database.Waifu.c.from_anime])
    embed.add_field(
        name="Cost", value=f"{resp[database.Waifu.c.price]} <:PIC:668725298388271105>"
    )
    embed.add_field(name="ID", value=resp[database.Waifu.c.id])
    embed.add_field(name="Gender", value=gender)
    image_field_id = 4
    if purchaser_user and purchaser[database.PurchasedWaifu.c.favorite]:
        embed.add_field(name="Favorite", value="Purchaser's favorite waifu :heart:")
        image_field_id += 1
    if len(images) > 1:
        embed.add_field(
            name="Image", inline=False, value=f"**Showing: 1/{len(images)}**"
        )
    if purchaser is not None:
        if purchaser_user is not None:
            embed.set_footer(
                text=f"Purchased by {purchaser_user.name}#{purchaser_user.discriminator} for {purchased_for} PIC.",
                icon_url=purchaser_user.avatar_url_as(size=128),
            )
        else:
            embed.set_footer(
                text=f"Purchased by someone who left for {purchased_for} PIC."
            )

    async def modifier_func(type, curr_page):
        embed.set_image(url=images[curr_page])
        embed.set_field_at(
            index=image_field_id,
            name="Image",
            inline=False,
            value=f"**Showing: {curr_page+1}/{len(images)}**",
        )

    await paginate_embed(client, message.channel, embed, len(images), modifier_func)


def favorite(unfavorite=False):
    async def _favorite(client, message, *args):
        if len(args) < 1:
            await message.channel.send(
                f"USAGE: `{PREFIX}favorite <name/id>/{PREFIX}unfavorite <name/id>`: Pick a waifu as your favorite!"
            )
        engine = await database.prepare_engine()
        async with engine.acquire() as conn:
            if len(args) == 1 and args[0].isdigit():
                search_id = int(args[0])
                query = database.Waifu.select().where(database.Waifu.c.id == search_id)
            else:
                search_string = "%" + " ".join(args).lower().strip() + "%"
                query = database.Waifu.select().where(
                    database.Waifu.c.name.ilike(search_string)
                )
            cursor = await conn.execute(query)
            waifu = await cursor.fetchone()
            if waifu is None:
                await message.channel.send(
                    "Waifu not found! Don't mark your imaginary waifus as favorite <:smug:575373306715439151>"
                )
                return
            query = (
                database.PurchasedWaifu.select()
                .where(database.PurchasedWaifu.c.waifu_id == waifu[database.Waifu.c.id])
                .where(database.PurchasedWaifu.c.guild == message.guild.id)
                .where(database.PurchasedWaifu.c.member == message.author.id)
            )
            cursor = await conn.execute(query)
            purchased_waifu = await cursor.fetchone()
            if purchased_waifu is None:
                await message.channel.send(
                    "You can't mark a waifu you don't own as a favorite <:smug:575373306715439151>"
                )
                return
            update_query = (
                database.PurchasedWaifu.update()
                .where(
                    database.PurchasedWaifu.c.id
                    == purchased_waifu[database.PurchasedWaifu.c.id]
                )
                .values(favorite=not unfavorite)
            )
            await conn.execute(update_query)
            if not unfavorite:
                gender = "him" if waifu[database.Waifu.c.gender] == "m" else "her"
                await message.channel.send(
                    f"{waifu[database.Waifu.c.name]} is delighted to hear you made {gender} your favorite! <:AilunaHug:575373643551473665>"
                )
            else:
                gender = "he" if waifu[database.Waifu.c.gender] == "m" else "she"
                await message.channel.send(
                    f"{waifu[database.Waifu.c.name]} is heartbroken but {gender} respects your decision! <:Eww:575373991640956938>"
                )

    return _favorite


buy_lock = {}
ug_lock = {}
sell_lock = {}


def handle_lock(uid, lock, type):
    last = lock.get(uid)
    if type == "ADD":
        if last and time.time() - last < 125:
            return False
        lock[uid] = time.time()
        return True
    elif type == "REMOVE":
        if not last:
            return False
        lock.pop(uid)
    elif type == "GET":
        if last and time.time() - last < 125:
            return True
        if last:
            lock.pop(uid)
        return False
    raise Exception(f"Unknown type for lock: {type}")


async def buy(client, message, *args):
    if len(args) < 1:
        await message.channel.send(f"USAGE: `{PREFIX}buy <waifu name/ID>`")
        return

    engine = await database.prepare_engine()

    async with engine.acquire() as conn:
        if len(args) == 1 and args[0].isdigit():
            search_id = int(args[0])
            query = database.Waifu.select().where(database.Waifu.c.id == search_id)
        else:
            search_string = "%" + " ".join(args).lower().strip() + "%"
            query = database.Waifu.select().where(
                database.Waifu.c.name.ilike(search_string)
            )
        cursor = await conn.execute(query)
        resp = await cursor.fetchone()
        if resp is None:
            await message.channel.send(
                "Waifu not found! You can add the waifu yourself, please join the support server! (`=support`) <a:thanks:699004469610020964>"
            )
            return
        waifu_name = resp[database.Waifu.c.name]
        waifu_id = resp[database.Waifu.c.id]

        if handle_lock(f"{message.guild.id}:{message.author.id}", ug_lock, "GET"):
            await message.channel.send(
                "You are already trying to do something! You should do things one at a time <:KannaBlob:575373833763028993>"
            )
            return

        if handle_lock(f"{waifu_id}:{message.guild.id}", buy_lock, "GET"):
            await message.channel.send(
                "Someone is already trying to buy this waifu! You should do things one at a time <:KannaBlob:575373833763028993>"
            )
            return

        query = (
            database.PurchasedWaifu.select()
            .where(database.PurchasedWaifu.c.waifu_id == waifu_id)
            .where(database.PurchasedWaifu.c.guild == message.guild.id)
        )
        cursor = await conn.execute(query)
        purchaser = await cursor.fetchone()
        if purchaser is not None:
            purchaser_user = message.guild.get_member(
                purchaser[database.PurchasedWaifu.c.member]
            )
            if purchaser_user is None:
                await message.channel.send(
                    "This waifu was purchased by someone who has now left the server! Rescue them with `=rescuewaifus`."
                )
                return
            elif purchaser[database.PurchasedWaifu.c.member] == message.author.id:
                await message.channel.send(
                    "How many more times do you want to buy this waifu? <:smug:575373306715439151>"
                )
                return
            else:
                await message.channel.send(
                    f"""
                Waifu is already purchased by {purchaser_user.name}#{purchaser_user.discriminator}. Ask them to sell it or trade with you!
                """
                )
                return
        cost = resp[database.Waifu.c.price]
        wallet = await _fetch_wallet(engine, message.author)
        if wallet - cost < 0:
            await message.channel.send(
                f"You do not have enough money! <:Eww:575373991640956938>\nYou need {cost-wallet} <:PIC:668725298388271105> more."
            )
            return

        handle_lock(f"{message.guild.id}:{message.author.id}", ug_lock, "ADD")
        handle_lock(f"{waifu_id}:{message.guild.id}", buy_lock, "ADD")
        await message.channel.send(
            f"Want to buy {waifu_name} for sure? Reply with `confirm` in 60s or `exit`."
        )

        def check(m):
            return (
                m.author.id != client.user.id
                and m.channel == message.channel
                and message.author.id == m.author.id
            )

        sure = False
        while not sure:
            try:
                msg = await client.wait_for("message", check=check, timeout=60)
                if msg.content == "confirm":
                    sure = True
                elif msg.content == "exit":
                    await message.channel.send("Okay, exiting...")
                    handle_lock(
                        f"{message.guild.id}:{message.author.id}", ug_lock, "REMOVE"
                    )
                    handle_lock(f"{waifu_id}:{message.guild.id}", buy_lock, "REMOVE")
                    return
                else:
                    await message.channel.send(
                        "Respond properly. Write `exit` to exit."
                    )
            except asyncio.TimeoutError:
                await message.channel.send("Error: Timeout.")
                handle_lock(
                    f"{message.guild.id}:{message.author.id}", ug_lock, "REMOVE"
                )
                handle_lock(f"{waifu_id}:{message.guild.id}", buy_lock, "REMOVE")
                return
        await _remove_money(None, message.author, cost, conn)
        fetch_query = database.Member.select().where(
            database.Member.c.member == message.author.id
        )
        cursor = await conn.execute(fetch_query)
        buyer = await cursor.fetchone()
        create_query = database.PurchasedWaifu.insert().values(
            [
                {
                    "member_id": buyer[database.Member.c.id],
                    "waifu_id": resp[database.Waifu.c.id],
                    "guild": message.guild.id,
                    "member": buyer[database.Member.c.member],
                    "purchased_for": cost,
                }
            ]
        )
        await conn.execute(create_query)
        handle_lock(f"{message.guild.id}:{message.author.id}", ug_lock, "REMOVE")
        handle_lock(f"{waifu_id}:{message.guild.id}", buy_lock, "REMOVE")
        await message.channel.send(
            f"You're now in a relationship with {waifu_name} <:SataniaThumb:575384688714317824>\nDon't lewd them! <:uwu:575372762583924757>"
        )


async def sell(client, message, *args):
    if len(args) < 1:
        await message.channel.send(f"USAGE: `{PREFIX}sell <waifu name/ID>`")
        return

    engine = await database.prepare_engine()

    async with engine.acquire() as conn:
        if len(args) == 1 and args[0].isdigit():
            search_id = int(args[0])
            query = database.Waifu.select().where(database.Waifu.c.id == search_id)
        else:
            search_string = "%" + " ".join(args).lower().strip() + "%"
            query = database.Waifu.select().where(
                database.Waifu.c.name.ilike(search_string)
            )
        cursor = await conn.execute(query)
        resp = await cursor.fetchone()
        if resp is None:
            await message.channel.send(
                "Waifu not found! Don't sell your imaginary waifus <:smug:575373306715439151>"
            )
            return
        waifu_id = resp[database.Waifu.c.id]
        waifu_name = resp[database.Waifu.c.name]

        if handle_lock(f"{message.guild.id}:{message.author.id}", ug_lock, "GET"):
            await message.channel.send(
                "You are already trying to do something! You should do things one at a time <:KannaBlob:575373833763028993>"
            )
            return

        if handle_lock(f"{waifu_id}:{message.guild.id}", sell_lock, "GET"):
            await message.channel.send(
                "Someone is already trying to sell this waifu! You should do things one at a time <:KannaBlob:575373833763028993>"
            )
            return

        query = (
            database.PurchasedWaifu.select()
            .where(database.PurchasedWaifu.c.waifu_id == waifu_id)
            .where(database.PurchasedWaifu.c.guild == message.guild.id)
            .where(database.PurchasedWaifu.c.member == message.author.id)
        )
        cursor = await conn.execute(query)
        purchased_waifu = await cursor.fetchone()
        if purchased_waifu is None:
            await message.channel.send(
                "By what logic are you trying to sell a waifu you don't own? <:Eww:575373991640956938>"
            )
            return

        handle_lock(f"{message.guild.id}:{message.author.id}", ug_lock, "ADD")
        handle_lock(f"{waifu_id}:{message.guild.id}", sell_lock, "ADD")

        cost = (
            purchased_waifu[database.PurchasedWaifu.c.purchased_for]
            * variables.SELL_WAIFU_DEPRECIATION
        )
        cost = int(cost)
        await message.channel.send(
            f"Want to break up with {waifu_name} for sure? You will get back {variables.SELL_WAIFU_DEPRECIATION * 100}%% of the cost, {cost} <:PIC:668725298388271105>\nReply with `confirm` in 60s or `exit`."
        )

        def check(m):
            return (
                m.author.id != client.user.id
                and m.channel == message.channel
                and message.author.id == m.author.id
            )

        sure = False
        while not sure:
            try:
                msg = await client.wait_for("message", check=check, timeout=60)
                if msg.content == "confirm":
                    sure = True
                elif msg.content == "exit":
                    await message.channel.send("Okay, exiting...")
                    handle_lock(
                        f"{message.guild.id}:{message.author.id}", ug_lock, "REMOVE"
                    )
                    handle_lock(f"{waifu_id}:{message.guild.id}", sell_lock, "REMOVE")
                    return
                else:
                    await message.channel.send(
                        "Respond properly. Write `exit` to exit."
                    )
            except asyncio.TimeoutError:
                await message.channel.send("Error: Timeout.")
                handle_lock(
                    f"{message.guild.id}:{message.author.id}", ug_lock, "REMOVE"
                )
                handle_lock(f"{waifu_id}:{message.guild.id}", sell_lock, "REMOVE")
                return
        delete_query = (
            database.PurchasedWaifu.delete()
            .where(
                database.PurchasedWaifu.c.waifu_id
                == purchased_waifu[database.PurchasedWaifu.c.waifu_id]
            )
            .where(
                database.PurchasedWaifu.c.member_id
                == purchased_waifu[database.PurchasedWaifu.c.member_id]
            )
        )
        await conn.execute(delete_query)
        await _add_money(engine, message.author, cost)
        handle_lock(f"{message.guild.id}:{message.author.id}", ug_lock, "REMOVE")
        handle_lock(f"{waifu_id}:{message.guild.id}", sell_lock, "REMOVE")
        await message.channel.send(
            f"You successfully broke up with {waifu_name} and they are being sent back to the Dungeon! <:SataniaThumb:575384688714317824>"
        )


def trade(using_money=False):
    async def _trade(client, message, *args):
        if len(message.mentions) != 1:
            await message.channel.send(
                f"Usage: {PREFIX}{'moneytrade' if using_money else 'trade'} <@user mention>"
            )
            return
        receiver = message.mentions[0]
        sender = message.author

        if handle_lock(
            f"{message.guild.id}:{receiver.id}", ug_lock, "GET"
        ) or handle_lock(f"{message.guild.id}:{sender.id}", ug_lock, "GET"):
            await message.channel.send(
                "You are already trying to do something! You should do things one at a time <:KannaBlob:575373833763028993>"
            )
            return

        handle_lock(f"{message.guild.id}:{receiver.id}", ug_lock, "ADD")
        handle_lock(f"{message.guild.id}:{sender.id}", ug_lock, "ADD")

        engine = await database.prepare_engine()
        async with engine.acquire() as conn:

            def check_user(user):
                def _check(m):
                    return (
                        m.author.id != client.user.id
                        and m.channel == message.channel
                        and user.id == m.author.id
                    )

                return _check

            try:
                await message.channel.send(
                    f"{sender.mention}, enter the name or ID of the waifu you want to trade:"
                )
                msg = await client.wait_for(
                    "message", check=check_user(sender), timeout=120
                )
                if msg.content.isdigit():
                    search_id = int(msg.content)
                    query = database.Waifu.select().where(
                        database.Waifu.c.id == search_id
                    )
                else:
                    search_string = "%" + msg.content.lower().strip() + "%"
                    query = database.Waifu.select().where(
                        database.Waifu.c.name.ilike(search_string)
                    )
                cursor = await conn.execute(query)
                sender_waifu = await cursor.fetchone()
                if sender_waifu is None:
                    await message.channel.send(
                        "Waifu not found! Don't trade your imaginary waifus <:smug:575373306715439151>"
                    )
                    
                    handle_lock(f"{message.guild.id}:{receiver.id}", ug_lock, "REMOVE")
                    handle_lock(f"{message.guild.id}:{sender.id}", ug_lock, "REMOVE")
                    return
                query = (
                    database.PurchasedWaifu.select()
                    .where(
                        database.PurchasedWaifu.c.waifu_id
                        == sender_waifu[database.Waifu.c.id]
                    )
                    .where(database.PurchasedWaifu.c.guild == message.guild.id)
                    .where(database.PurchasedWaifu.c.member == sender.id)
                )
                cursor = await conn.execute(query)
                sender_pwaifu = await cursor.fetchone()
                if sender_pwaifu is None:
                    await message.channel.send(
                        "By what logic are you trying to trade a waifu you don't own? <:smug:575373306715439151>"
                    )
                    handle_lock(f"{message.guild.id}:{receiver.id}", ug_lock, "REMOVE")
                    handle_lock(f"{message.guild.id}:{sender.id}", ug_lock, "REMOVE")
                    return

                if using_money:
                    await message.channel.send(
                        f"{receiver.mention}, enter the price you want to trade {sender_waifu[database.Waifu.c.name]} for:"
                    )
                else:
                    await message.channel.send(
                        f"{receiver.mention}, enter the name or ID of the waifu you want to trade with {sender_waifu[database.Waifu.c.name]}:"
                    )
                msg = await client.wait_for(
                    "message", check=check_user(receiver), timeout=120
                )
                if using_money:
                    if msg.content.isdigit():
                        receiver_money = int(msg.content)
                        receiver_wallet = await _fetch_wallet(engine, receiver)
                        if receiver_wallet - receiver_money < 0:
                            await message.channel.send(
                                f"You do not have enough money! <:Eww:575373991640956938>\nYou need {receiver_money-receiver_wallet} <:PIC:668725298388271105> more."
                            )
                            handle_lock(f"{message.guild.id}:{receiver.id}", ug_lock, "REMOVE")
                            handle_lock(f"{message.guild.id}:{sender.id}", ug_lock, "REMOVE")
                            return
                        await _remove_money(None, receiver, receiver_money, conn)
                    else:
                        await message.channel.send("Invalid amount entered! Exiting...")
                        handle_lock(f"{message.guild.id}:{receiver.id}", ug_lock, "REMOVE")
                        handle_lock(f"{message.guild.id}:{sender.id}", ug_lock, "REMOVE")
                        return
                else:
                    if msg.content.isdigit():
                        search_id = int(msg.content)
                        query = database.Waifu.select().where(
                            database.Waifu.c.id == search_id
                        )
                    else:
                        search_string = "%" + msg.content.lower().strip() + "%"
                        query = database.Waifu.select().where(
                            database.Waifu.c.name.ilike(search_string)
                        )
                    cursor = await conn.execute(query)
                    receiver_waifu = await cursor.fetchone()
                    if receiver_waifu is None:
                        await message.channel.send(
                            "Waifu not found! Don't trade your imaginary waifus <:smug:575373306715439151>"
                        )
                        handle_lock(f"{message.guild.id}:{receiver.id}", ug_lock, "REMOVE")
                        handle_lock(f"{message.guild.id}:{sender.id}", ug_lock, "REMOVE")
                        return
                    query = (
                        database.PurchasedWaifu.select()
                        .where(
                            database.PurchasedWaifu.c.waifu_id
                            == receiver_waifu[database.Waifu.c.id]
                        )
                        .where(database.PurchasedWaifu.c.guild == message.guild.id)
                        .where(database.PurchasedWaifu.c.member == receiver.id)
                    )
                    cursor = await conn.execute(query)
                    receiver_pwaifu = await cursor.fetchone()
                    if receiver_pwaifu is None:
                        await message.channel.send(
                            "By what logic are you trying to trade a waifu you don't own? <:smug:575373306715439151>"
                        )
                        handle_lock(f"{message.guild.id}:{receiver.id}", ug_lock, "REMOVE")
                        handle_lock(f"{message.guild.id}:{sender.id}", ug_lock, "REMOVE")
                        return

                if using_money:
                    await message.channel.send(
                        f"""
{sender.mention}, do you confirm the trade of your {sender_waifu[database.Waifu.c.name]} in exchange for {receiver_money} <:PIC:668725298388271105> from {receiver.mention}?
Enter Yes/No:
    """
                    )
                else:
                    await message.channel.send(
                        f"""
{sender.mention}, do you confirm the trade of your {sender_waifu[database.Waifu.c.name]} in exchange for {receiver.mention}'s {receiver_waifu[database.Waifu.c.name]}?
Enter Yes/No:
    """
                    )

                msg = await client.wait_for(
                    "message", check=check_user(sender), timeout=120
                )
                if msg.content.lower() in ["yes", "y", "ye", "yeah", "yea", "yep"]:
                    pass
                elif msg.content.lower() in ["no", "n", "nah", "nein", "nope"]:
                    await message.channel.send("Okay, cancelling trade...")
                    if using_money:
                        await _add_money(engine, receiver, receiver_money)
                    handle_lock(f"{message.guild.id}:{receiver.id}", ug_lock, "REMOVE")
                    handle_lock(f"{message.guild.id}:{sender.id}", ug_lock, "REMOVE")
                    return
                else:
                    await message.channel.send("Invalid option. Exiting...")
                    if using_money:
                        await _add_money(engine, receiver, receiver_money)
                    handle_lock(f"{message.guild.id}:{receiver.id}", ug_lock, "REMOVE")
                    handle_lock(f"{message.guild.id}:{sender.id}", ug_lock, "REMOVE")
                    return

            except asyncio.TimeoutError:
                await message.channel.send("Error: Timeout.")
                if using_money:
                    await _add_money(engine, receiver, receiver_money)
                handle_lock(f"{message.guild.id}:{receiver.id}", ug_lock, "REMOVE")
                handle_lock(f"{message.guild.id}:{sender.id}", ug_lock, "REMOVE")
                return

            fetch_query = database.Member.select().where(
                database.Member.c.member == receiver.id
            )
            cursor = await conn.execute(fetch_query)
            receiver_db = await cursor.fetchone()
            delete_query = (
                database.PurchasedWaifu.delete()
                .where(
                    database.PurchasedWaifu.c.waifu_id
                    == sender_pwaifu[database.PurchasedWaifu.c.waifu_id]
                )
                .where(
                    database.PurchasedWaifu.c.member_id
                    == sender_pwaifu[database.PurchasedWaifu.c.member_id]
                )
            )
            create_query = database.PurchasedWaifu.insert().values(
                [
                    {
                        "member_id": receiver_db[database.Member.c.id],
                        "waifu_id": sender_waifu[database.Waifu.c.id],
                        "guild": message.guild.id,
                        "member": receiver_db[database.Member.c.member],
                        "purchased_for": 0,
                    }
                ]
            )
            await conn.execute(delete_query)
            await conn.execute(create_query)
            if using_money:
                await _add_money(engine, sender, receiver_money)
            else:
                delete_query = (
                    database.PurchasedWaifu.delete()
                    .where(
                        database.PurchasedWaifu.c.waifu_id
                        == receiver_pwaifu[database.PurchasedWaifu.c.waifu_id]
                    )
                    .where(
                        database.PurchasedWaifu.c.member_id
                        == receiver_pwaifu[database.PurchasedWaifu.c.member_id]
                    )
                )
                create_query = database.PurchasedWaifu.insert().values(
                    [
                        {
                            "member_id": sender_pwaifu[
                                database.PurchasedWaifu.c.member_id
                            ],
                            "waifu_id": receiver_waifu[database.Waifu.c.id],
                            "guild": message.guild.id,
                            "member": sender_pwaifu[database.PurchasedWaifu.c.member],
                            "purchased_for": 0,
                        }
                    ]
                )
                await conn.execute(delete_query)
                await conn.execute(create_query)

                handle_lock(f"{message.guild.id}:{receiver.id}", ug_lock, "REMOVE")
                handle_lock(f"{message.guild.id}:{sender.id}", ug_lock, "REMOVE")
            await message.channel.send(
                "Trade successful! <:SataniaThumb:575384688714317824>"
            )

    return _trade


def _prepare_harem_page(waifus, waifu_data):
    txt = ""
    for n, row in waifus:
        data = waifu_data[row[database.PurchasedWaifu.c.waifu_id]]
        if not row[database.PurchasedWaifu.c.favorite]:
            txt += "{0}: **__{1}__**\n**ID:** {2}. **Bought For:** {4} <:PIC:668725298388271105> **From:** {3}\n".format(
                n,
                data[database.Waifu.c.name],
                data[database.Waifu.c.id],
                data[database.Waifu.c.from_anime],
                row[database.PurchasedWaifu.c.purchased_for],
            )
        else:
            txt += "{0}: **__{1}__** :heart:\n**ID:** {2}. **Bought For:** {4} <:PIC:668725298388271105> **From:** {3}\n".format(
                n,
                data[database.Waifu.c.name],
                data[database.Waifu.c.id],
                data[database.Waifu.c.from_anime],
                row[database.PurchasedWaifu.c.purchased_for],
            )
    return txt


def compare_strings(a, b):
    a = "".join(e for e in a.lower().strip() if e.isalnum())
    b = "".join(e for e in b.lower().strip() if e.isalnum())
    return a in b


async def _harem(
    client, message, member, sort_opt=None, sort_gender=None, series_name=None
):
    engine = await database.prepare_engine()
    async with engine.acquire() as conn:
        query = (
            database.PurchasedWaifu.select()
            .where(database.PurchasedWaifu.c.member == member.id)
            .where(database.PurchasedWaifu.c.guild == message.guild.id)
        )
        cursor = await conn.execute(query)
        resp = await cursor.fetchall()
        if resp is None or len(resp) == 0:
            await message.channel.send(
                "{0}#{1} does not have a harem. Lonely life :(".format(
                    member.name, member.discriminator
                )
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
            x
            for x in purchased_waifus
            if compare_strings(
                series_name,
                waifu_data[x[database.PurchasedWaifu.c.waifu_id]][
                    database.Waifu.c.from_anime
                ],
            )
        ]
    if sort_opt:
        reverse = False
        if "desc" in sort_opt:
            reverse = True
        if sort_opt.startswith("id"):
            purchased_waifus.sort(
                key=lambda x: x[database.PurchasedWaifu.c.waifu_id], reverse=reverse
            )
        elif sort_opt.startswith("price"):
            purchased_waifus.sort(
                key=lambda x: x[database.PurchasedWaifu.c.purchased_for],
                reverse=reverse,
            )
        elif sort_opt.startswith("name"):
            tpw = [
                (
                    waifu_data[x[database.PurchasedWaifu.c.waifu_id]][
                        database.Waifu.c.name
                    ],
                    x,
                )
                for x in purchased_waifus
            ]
            tpw.sort(reverse=reverse)
            purchased_waifus = [x[1] for x in tpw]
        elif sort_opt.startswith("series"):
            tpw = [
                (
                    waifu_data[x[database.PurchasedWaifu.c.waifu_id]][
                        database.Waifu.c.from_anime
                    ],
                    x,
                )
                for x in purchased_waifus
            ]
            tpw.sort(reverse=reverse)
            purchased_waifus = [x[1] for x in tpw]
    if sort_gender:
        if sort_gender == "waifu":
            purchased_waifus = [
                x
                for x in purchased_waifus
                if waifu_data[x[database.PurchasedWaifu.c.waifu_id]][
                    database.Waifu.c.gender
                ]
                == "f"
            ]
        elif sort_gender == "husbando":
            purchased_waifus = [
                x
                for x in purchased_waifus
                if waifu_data[x[database.PurchasedWaifu.c.waifu_id]][
                    database.Waifu.c.gender
                ]
                == "m"
            ]
    tpw = [(x[database.PurchasedWaifu.c.favorite], x) for x in purchased_waifus]
    tpw.sort(reverse=True, key=lambda i: i[0])
    purchased_waifus = [x[1] for x in tpw]
    if len(purchased_waifus) == 0:
        await message.channel.send("No harem found for specified queries.")
        return
    pages = []
    n = 0
    for i in range(0, len(purchased_waifus), 10):
        pages.append(
            [(n + nn + 1, j) for nn, j in enumerate(purchased_waifus[i : i + 10])]
        )
        n += 10
    curr_page = 0
    embed = discord.Embed(
        title=f"{member.name}'s Harem",
        color=member.color,
        description=_prepare_harem_page(pages[curr_page], waifu_data),
    )
    embed.add_field(name="Waifus Inside Locker", value=len(purchased_waifus))
    embed.add_field(
        name="Net Harem Value",
        value=str(
            sum([i[database.PurchasedWaifu.c.purchased_for] for i in purchased_waifus])
        )
        + " <:PIC:668725298388271105>",
    )
    embed.add_field(
        name="\u200b",
        inline=False,
        value=f"To view details, do `{PREFIX}waifu details <name/id>`",
    )
    embed.set_footer(
        text=f"{member.name}#{member.discriminator} • Page {curr_page+1}/{len(pages)}",
        icon_url=member.avatar_url_as(size=128),
    )
    harem_msg = await message.channel.send(embed=embed)
    if len(pages) == 1:
        return
    await harem_msg.add_reaction("⬅")
    await harem_msg.add_reaction("➡")

    def check(reaction, user):
        return (
            not user.bot
            and reaction.message.channel == message.channel
            and reaction.message.id == harem_msg.id
        )

    seen = False
    try:
        while not seen:
            reaction, user = await client.wait_for(
                "reaction_add", timeout=120.0, check=check
            )
            if str(reaction.emoji) == "➡" and len(pages) > 1:
                if curr_page < len(pages) - 1:
                    curr_page += 1
                    embed.description = _prepare_harem_page(
                        pages[curr_page], waifu_data
                    )
                    embed.set_footer(
                        text=f"{member.name}#{member.discriminator} • Page {curr_page+1}/{len(pages)}",  # noqa
                        icon_url=member.avatar_url_as(size=128),
                    )
                    await harem_msg.edit(embed=embed)
                await harem_msg.remove_reaction("➡", user)
            elif str(reaction.emoji) == "⬅" and len(pages) > 1:
                if curr_page > 0:
                    curr_page -= 1
                    embed.description = _prepare_harem_page(
                        pages[curr_page], waifu_data
                    )
                    embed.set_footer(
                        text=f"{member.name}#{member.discriminator} • Page {curr_page+1}/{len(pages)}",  # noqa
                        icon_url=member.avatar_url_as(size=128),
                    )
                    await harem_msg.edit(embed=embed)
                await harem_msg.remove_reaction("⬅", user)
            else:
                continue
    except asyncio.TimeoutError:
        await harem_msg.remove_reaction("⬅", client.user)
        await harem_msg.remove_reaction("➡", client.user)
    return


async def harem(client, message, *args):
    args = list(args)
    VALID_SORT_OPTS = [
        "name-desc",
        "series-desc",
        "name-asc",
        "series-asc",
        "id-asc",
        "id-desc",
        "price-asc",
        "price-desc",
    ]
    VALID_GENDER_OPTS = ["waifu", "husbando"]
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
    if len(message.mentions) == 0 and len(args) > 0:
        series_name = " ".join(args)
    if len(message.mentions) == 1 and len(args) > 1:
        series_name = " ".join(args[1:])
    if len(message.mentions) == 0:
        await _harem(
            client, message, message.author, matching_sort, matching_gender, series_name
        )
    if len(message.mentions) == 1:
        await _harem(
            client,
            message,
            message.mentions[0],
            matching_sort,
            matching_gender,
            series_name,
        )


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
        total_rolls = 3 * 3600  # Virtually unlimited for devs, lol.
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
        if (
            last_roll_interval.seconds + last_roll_interval.days * 24 * 3600
            < variables.ROLL_INTERVAL
        ):
            rolls_left = total_rolls - random_waifu_counter[member.id][0]
    else:
        random_waifu_counter.update({member.id: (0, datetime.now())})
    if rolls_left < 1:
        s = variables.ROLL_INTERVAL - (datetime.now() - last_roll).seconds
        h = s // 3600
        m = s // 60 - h * 60
        await message.channel.send(
            f"""
You have no rolls left! Rolls reset in {h:02d} hours {m:02d} minutes. You can donate to me and get more rolls!
            """
        )
        return
    random_waifu_counter.update(
        {member.id: (total_rolls - rolls_left + 1, datetime.now())}
    )
    async with engine.acquire() as conn:
        count_query = database.Waifu.count()
        cur = await conn.execute(count_query)
        resp = await cur.fetchone()
        wid = randint(1, resp[0])
        query = database.Waifu.select().where(database.Waifu.c.id == wid)
        cursor = await conn.execute(query)
        resp = await cursor.fetchone()
        query = (
            database.PurchasedWaifu.select()
            .where(database.PurchasedWaifu.c.waifu_id == resp[database.Waifu.c.id])
            .where(database.PurchasedWaifu.c.guild == message.guild.id)
        )
        cursor = await conn.execute(query)
        purchaser = await cursor.fetchone()
        if purchaser is not None:
            purchaser_user = message.guild.get_member(
                purchaser[database.PurchasedWaifu.c.member]
            )
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
            waifu_description = "Hi! I am a {2} from {0}. You need {1} <:PIC:668725298388271105> to buy me! React with the :heart: below to buy me! Hurry up, 10 seconds left.".format(  # noqa
                resp[database.Waifu.c.from_anime], price, gender.lower()
            )
        else:
            waifu_description = "Hi! I am a {1} from {0}. I am already in a relationship with {2}#{3}.".format(  # noqa
                resp[database.Waifu.c.from_anime],
                gender.lower(),
                purchaser_user.name,
                purchaser_user.discriminator,
            )
        embed = discord.Embed(
            title=resp[database.Waifu.c.name],
            description=waifu_description,
            type="rich",
            color=message.author.colour,
        )
        curr_img = -1
        images = []
        if resp[database.Waifu.c.image_url] is not None:
            images = resp[database.Waifu.c.image_url].split(",")
            embed.set_image(url=images[0])
            curr_img = 0
        embed.add_field(name="From", value=resp[database.Waifu.c.from_anime])
        embed.add_field(name="Cost", value=f"{price} <:PIC:668725298388271105>")
        embed.add_field(name="ID", value=resp[database.Waifu.c.id])
        embed.add_field(name="Gender", value=gender)
        if len(images) > 1:
            embed.add_field(
                name="Image",
                inline=False,
                value=f"**Showing: {curr_img+1}/{len(images)}**",
            )
        if not purchaseable:
            embed.set_footer(
                text="Purchased by {0} for {1} PIC.".format(
                    purchaser_user.name, purchased_for
                ),
                icon_url=purchaser_user.avatar_url_as(size=128),
            )
        roll_msg = await message.channel.send(embed=embed)
        if purchaseable:
            await roll_msg.add_reaction("❤")
        if len(images) > 1:
            await roll_msg.add_reaction("⬅")
            await roll_msg.add_reaction("➡")

        def check(reaction, user):
            return (
                not user.bot
                and reaction.message.channel == message.channel
                and reaction.message.id == roll_msg.id
            )

        purchased = False
        try:
            while not purchased:
                reaction, purchaser = await client.wait_for(
                    "reaction_add", timeout=10.0, check=check
                )
                if str(reaction.emoji) == "❤":
                    purchased = True
                elif str(reaction.emoji) == "➡" and len(images) > 1:
                    if curr_img < len(images) - 1:
                        curr_img += 1
                        embed.set_image(url=images[curr_img])
                        embed.set_field_at(
                            index=4,
                            name="Image",
                            inline=False,
                            value=f"**Showing: {curr_img+1}/{len(images)}**",
                        )
                        await roll_msg.edit(embed=embed)
                    await roll_msg.remove_reaction("➡", purchaser)
                elif str(reaction.emoji) == "⬅" and len(images) > 1:
                    if curr_img > 0:
                        curr_img -= 1
                        embed.set_image(url=images[curr_img])
                        embed.set_field_at(
                            index=4,
                            name="Image",
                            inline=False,
                            value=f"**Showing: {curr_img+1}/{len(images)}**",
                        )
                        await roll_msg.edit(embed=embed)
                    await roll_msg.remove_reaction("⬅", purchaser)
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
        await _remove_money(None, purchaser, price, conn)
        fetch_query = database.Member.select().where(
            database.Member.c.member == purchaser.id
        )
        cursor = await conn.execute(fetch_query)
        buyer = await cursor.fetchone()
        create_query = database.PurchasedWaifu.insert().values(
            [
                {
                    "member_id": buyer[database.Member.c.id],
                    "waifu_id": resp[database.Waifu.c.id],
                    "guild": message.guild.id,
                    "member": buyer[database.Member.c.member],
                    "purchased_for": price,
                }
            ]
        )
        await conn.execute(create_query)
        embed.description = "I am now in a relationship with {}!".format(purchaser.name)
        await roll_msg.edit(embed=embed)
        await roll_msg.remove_reaction("⬅", client.user)
        await roll_msg.remove_reaction("➡", client.user)
        await message.channel.send(
            "Successfully bought waifu at an unbelievable price :thumbsup:. Don't lewd them!"
        )


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
        total_rolls = 3 * 3600  # Virtually unlimited for devs, lol.
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
        if (
            last_roll_interval.seconds + last_roll_interval.days * 24 * 3600
            < variables.ROLL_INTERVAL
        ):
            rolls_left = total_rolls - random_waifu_counter[member.id][0]
    else:
        random_waifu_counter.update({member.id: (0, datetime.now())})
    s = variables.ROLL_INTERVAL - (datetime.now() - last_roll).seconds
    h = s // 3600
    m = s // 60 - h * 60
    rolls_left_txt = "no" if rolls_left < 1 else rolls_left
    await message.channel.send(
        f"""
You have {rolls_left_txt} rolls left! Please try again in {h:02d} hours {m:02d} minutes. You can donate to me and get more rolls!
    """
    )


async def waifu(client, message, *args):
    await message.channel.send(
        """
Hey! Sorry for the inconvenience but `{0}waifu` has been deprecated.
In future, this command will be deleted or replaced with a help message.
The new commands are:

`{0}quiz`: Time to battle with your friends or yourself and test your anime knowledge! **NEW/WIP**
`{0}search <name>`: Search for a waifu in the Dungeon of Waifus. Don't get lost!
`{0}details <name/id>`: Get details (and pictures) for a waifu! (But don't lewd them <:uwu:575372762583924757>)
`{0}buy <name/id>`: Buy your own waifu and prove you love her! (PS: The waifus have consented. No trafficked waifus, promise!)
`{0}sell <name/id>`: Sell your waifus because you stopped loving them <:Eww:575373991640956938>
`{0}trade <@user mention>`: Organic:tm: Waifu-for-Waifu Trades! Go trade now with your friends* (*assuming you have friends)
`{0}moneytrade <@user mention>`: Inorganic:tm: Waifu-for-Money Trades! Your friend wants your waifu but you don't want a waifu from them? No issues, trade with money!
`{0}favorite <waifu name/id>`: Mark your waifu as a favorite to show your eternal love for them <a:thanks:699004469610020964>
`{0}unfavorite <waifu name/id>`: Unmark your waifu as a favorite cause all waifus are equal and deserve equal love!
`{0}harem [@user mention] [sort option] [gender option] [series name]`: Get your harem, aka your bought waifus. Valid sort options: `name-desc`, `series-desc`, `name-asc`, `series-asc`, `id-asc`, `id-desc`, `price-asc`, `price-desc`. Valid gender options: `waifu`, `husbando`.
        """.format(
            PREFIX
        )
    )


waifu_functions = {
    "waifu": (waifu, "`{P}waifu`: Old interface to using the waifu system!"),
    "details": (
        details,
        "`{P}details`: Get details (and pictures) for a waifu! (But don't lewd them <:uwu:575372762583924757>)",
    ),
    "search": (
        search,
        "`{P}search`: Search for a waifu in the Dungeon of Waifus. Don't get lost!",
    ),
    "buy": (
        buy,
        "`{P}buy`: Buy your own waifu and prove you love her! (PS: The waifus have consented. No trafficked waifus, promise!)",
    ),
    "sell": (
        sell,
        "`{P}sell`: Sell your waifus because you stopped loving them <:Eww:575373991640956938>",
    ),
    "trade": (
        trade(using_money=False),
        "`{P}trade`: Organic:tm: Waifu-for-Waifu Trades! Go trade now with your friends* (*assuming you have friends)",
    ),
    "moneytrade": (
        trade(using_money=True),
        "`{P}moneytrade`: Inorganic:tm: Waifu-for-Money Trades! Your friend wants your waifu but you don't want a waifu from them? No issues, trade with money!",
    ),
    "favorite": (
        favorite(unfavorite=False),
        "`{P}favorite`: Mark your waifu as a favorite to show your eternal love for them <a:thanks:699004469610020964>",
    ),
    "unfavorite": (
        favorite(unfavorite=True),
        "`{P}unfavorite`: Unmark your waifu as a favorite cause all waifus are equal and deserve equal love!",
    ),
    "harem": (
        harem,
        "`{P}harem [@user mention] [sort option] [gender option] [series name]`: Flex your harem, or get jealous of others' harem! Valid sort options: `name-desc`, `series-desc`, `name-asc`, `series-asc`, `id-asc`, `id-desc`, `price-asc`, `price-desc`. Valid gender options: `waifu`, `husbando`.",
    ),
    "randomroll": (
        random_waifu,
        "`{P}randomroll`: Get a random waifu/husbando for a very cheap price. Normal users can do it 10 times per 3 hours, tier 1 donators 30 times, and tier 2 donators 90 times.",
    ),
    "rr": (
        random_waifu,
        "`{P}rr`: Get a random waifu/husbando for a very cheap price. Normal users can do it 10 times per 3 hours, tier 1 donators 30 times, and tier 2 donators 90 times.",
    ),
    "rolls": (
        rolls_left,
        "`{P}rolls`: Check how many rolls you have left for getting a random waifu. Resets every 3 hours.",
    ),
}
