import database
import discord
import asyncio
from .currency import _fetch_wallet, _remove_money, _add_money
from variables import PREFIX


async def weapon_shop(client, message, *args):
    if len(args) == 0 or args[0] not in ['sell', 'buy', 'list']:
        await message.channel.send(f"""
Welcome to the weapons shop!\n
To buy, `{PREFIX}wshop buy <ID>`.
To sell, `{PREFIX}wshop sell <ID>`.
To view details, `{PREFIX}wshop details <ID>`.
To view the available weapons, `{PREFIX}wshop list`.
        """)
    elif args[0] == 'buy':
        pass
    elif args[0] == 'sell':
        pass
    elif args[0] == 'list':
        await _list(client, message, args[1:])


async def _list(client, message, *args):
    member = message.author
    engine = await database.prepare_engine()
    async with engine.acquire() as conn:
        query = database.RPGWeapon.select().where(
            database.RPGWeapon.c.req_level >= 0  # TODO TODO
        )
        cursor = await conn.execute(query)
        weapons = await cursor.fetchall()
    pages = []
    n = 0
    for i in range(0, len(weapons), 10):
        pages.append(
            [(n+nn+1, j) for nn, j in enumerate(weapons[i:i+10])]
        )
        n += 10
    curr_page = 0

    def _prepare_page(curr_page):
        page = pages[curr_page]
        txt = []
        for n, data in page:
            txt.append(
                "{0}: **__{1}__**\n**Cost:** {2}. **Required Level:** {3}.\n\n".
                format(n, data[database.RPGWeapon.c.name],
                       data[database.RPGWeapon.c.price],
                       data[database.RPGWeapon.c.req_level]))
        return "\n".join(txt)

    embed = discord.Embed(
        title=f"Weapons Arsenal", color=member.color,
        description=_prepare_page(curr_page))
    embed.add_field(
        name="\u200b", inline=False,
        value=f"To view details, do `{PREFIX}wshop details <name/id>`")
    embed.set_footer(
        text=f"{member.name}#{member.discriminator} • Page {curr_page+1}/{len(pages)}",
        icon_url=member.avatar_url_as(size=128))
    inventory_msg = await message.channel.send(embed=embed)
    if len(pages) == 1:
        return
    await inventory_msg.add_reaction("⬅")
    await inventory_msg.add_reaction("➡")

    def check(reaction, user):
        return (not user.bot
                and reaction.message.channel == message.channel
                and reaction.message.id == inventory_msg.id)
    seen = False
    try:
        while not seen:
            reaction, user = await client.wait_for(
                'reaction_add', timeout=120.0, check=check)
            if str(reaction.emoji) == '➡' and len(pages) > 1:
                if curr_page < len(pages) - 1:
                    curr_page += 1
                    embed.description = _prepare_page(curr_page)
                    embed.set_footer(
                        text=f"{member.name}#{member.discriminator} • Page {curr_page+1}/{len(pages)}",  # noqa
                        icon_url=member.avatar_url_as(size=128))
                    await inventory_msg.edit(embed=embed)
                await inventory_msg.remove_reaction('➡', user)
            elif str(reaction.emoji) == '⬅' and len(pages) > 1:
                if curr_page > 0:
                    curr_page -= 1
                    embed.description = _prepare_page(curr_page)
                    embed.set_footer(
                        text=f"{member.name}#{member.discriminator} • Page {curr_page+1}/{len(pages)}",  # noqa
                        icon_url=member.avatar_url_as(size=128))
                    await inventory_msg.edit(embed=embed)
                await inventory_msg.remove_reaction('⬅', user)
            else:
                continue
    except asyncio.TimeoutError:
        await inventory_msg.remove_reaction("⬅", client.user)
        await inventory_msg.remove_reaction("➡", client.user)
    return


def _prepare_inventory_page(weapons, waifu_data):
    txt = ""
    for n, row in weapons:
        data = waifu_data[row[database.PurchasedWeapon.c.weapon_id]]
        weapon_stats = ", ".join(
            (f"{i.title().replace('_', ' ')}: {j}"
             for i, j in data[database.RPGWeapon.c.effects].items()))
        txt += (
            "{0}: **__{1}__**\n**ID:** {2}. **Level:** {3}. **Times Used:** {4}. **Stats:** {5}.\n\n".  # noqa
            format(n, data[database.RPGWeapon.c.name], data[database.RPGWeapon.c.id],
                   row[database.PurchasedWeapon.c.level],
                   row[database.PurchasedWeapon.c.used], weapon_stats)
        )
    return txt


async def inventory(client, message, *args):
    engine = await database.prepare_engine()
    member = message.author  # TODO: In future, others?
    async with engine.acquire() as conn:
        query = database.PurchasedWeapon.select().where(
            database.PurchasedWaifu.c.member == member.id)
        cursor = await conn.execute(query)
        resp = await cursor.fetchall()
        if resp is None or len(resp) == 0:
            await message.channel.send(
                f"Your inventory is empty. Buy some weapons with `{PREFIX}shop`!"
            )
            return
        purchased_weapons = resp
        weapon_ids = [x[database.PurchasedWeapon.c.weapon_id] for x in purchased_weapons]
        query = database.RPGWeapon.select().where(database.Weapon.c.id.in_(weapon_ids))
        cursor = await conn.execute(query)
        resp = await cursor.fetchall()
        weapon_data = {x[database.Weapon.c.id]: x for x in resp}
    pages = []
    n = 0
    for i in range(0, len(purchased_weapons), 10):
        pages.append(
            [(n+nn+1, j) for nn, j in enumerate(purchased_weapons[i:i+10])]
        )
        n += 10
    curr_page = 0
    embed = discord.Embed(
        title=f"{member.name}'s Inventory", color=member.color,
        description=_prepare_inventory_page(pages[curr_page], weapon_data))
    embed.add_field(name="Weapons Inside Locker", value=len(purchased_weapons))
    embed.add_field(
        name="\u200b", inline=False,
        value=f"To view details, do `{PREFIX}waifu details <name/id>`")
    embed.set_footer(
        text=f"{member.name}#{member.discriminator} • Page {curr_page+1}/{len(pages)}",
        icon_url=member.avatar_url_as(size=128))
    inventory_msg = await message.channel.send(embed=embed)
    if len(pages) == 1:
        return
    await inventory_msg.add_reaction("⬅")
    await inventory_msg.add_reaction("➡")

    def check(reaction, user):
        return (not user.bot
                and reaction.message.channel == message.channel
                and reaction.message.id == inventory_msg.id)
    seen = False
    try:
        while not seen:
            reaction, user = await client.wait_for(
                'reaction_add', timeout=120.0, check=check)
            if str(reaction.emoji) == '➡' and len(pages) > 1:
                if curr_page < len(pages) - 1:
                    curr_page += 1
                    embed.description = _prepare_inventory_page(pages[curr_page], weapon_data)
                    embed.set_footer(
                        text=f"{member.name}#{member.discriminator} • Page {curr_page+1}/{len(pages)}",  # noqa
                        icon_url=member.avatar_url_as(size=128))
                    await inventory_msg.edit(embed=embed)
                await inventory_msg.remove_reaction('➡', user)
            elif str(reaction.emoji) == '⬅' and len(pages) > 1:
                if curr_page > 0:
                    curr_page -= 1
                    embed.description = _prepare_inventory_page(pages[curr_page], waifu_data)
                    embed.set_footer(
                        text=f"{member.name}#{member.discriminator} • Page {curr_page+1}/{len(pages)}",  # noqa
                        icon_url=member.avatar_url_as(size=128))
                    await inventory_msg.edit(embed=embed)
                await inventory_msg.remove_reaction('⬅', user)
            else:
                continue
    except asyncio.TimeoutError:
        await inventory_msg.remove_reaction("⬅", client.user)
        await inventory_msg.remove_reaction("➡", client.user)
    return


async def duel(client, message, *args):
    pass


rpg_functions = {
    'weaponshop': (weapon_shop, "Buy weapons!"),
    'wshop': (weapon_shop, "Buy weapons!"),
    'inventory': (inventory, "See your weapons"),
    'duel': (duel, "Duel against another player"),
}
