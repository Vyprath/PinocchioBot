from .currency import _remove_money, _fetch_wallet
import database
import discord
import asyncio
from variables import CUSTOM_ROLE_COST


async def buy_colored_role(client, message, *args):
    engine = await database.prepare_engine()
    await message.channel.send("Welcome to the custom colored role creator!")
    wallet = await _fetch_wallet(engine, message.author)
    if wallet - CUSTOM_ROLE_COST < 0:
        await message.channel.send(
            "Unfortunately you don't have enough money. Cost is {0} coins".format(CUSTOM_ROLE_COST))
        return
    await message.channel.send(
        "Enter the color (Either enter a hex code like `0x00ff00`, or enter an 8-bit RGB sequence like `0 255 0`):")  # noqa

    def check(m):
        return (m.author.id != client.user.id
                and m.channel == message.channel
                and m.author.id == message.author.id)

    try:
        msg = await client.wait_for('message', check=check, timeout=180)
        split = msg.content.split()
        if len(split) == 1 and msg.content.startswith("0x") and len(msg.content) == 8:
            color = discord.Color(int(msg.content[2:], 16))
        else:
            assert (len(split) == 3 and split[0].isdigit() and split[1].isdigit() and split[2].isdigit())  # noqa
            r, g, b = [int(x) for x in split]
            assert (0 <= r <= 255) and (0 <= g <= 255) and (0 <= b <= 255)
            color = discord.Color.from_rgb(*[int(x) for x in split])
        await message.channel.send("Good job, now enter a role name:")
        msg = await client.wait_for('message', check=check, timeout=180)
        role_name = msg.content
        await message.channel.send(
            "Creating '{0}' role with color {1}. You sure? Reply `yes`/`no`.".format(role_name, str(color)))  # noqa
        msg = await client.wait_for('message', check=check, timeout=180)
        if msg.content.lower().strip() == 'yes':
            pass
        elif msg.content.lower().strip() == 'no':
            await message.channel.send("Ok, exiting.")
            return
        else:
            raise AssertionError
    except asyncio.TimeoutError:
        await message.channel.send("Error: No response recieved. Timeout.")
        return
    except (AssertionError, ValueError):
        await message.channel.send("Invalid text entered. Exiting...")
        return
    await _remove_money(engine, message.author, CUSTOM_ROLE_COST)
    role = await message.guild.create_role(
        name=role_name, color=color, reason="Bought this custom role.")
    await message.author.add_roles(role, reason="Bought this custom role.")
    await message.channel.send("Successfully bought you the role! :thumbsup:")


async def paid_roles(client, message, *args):
    engine = await database.prepare_engine()
    async with engine.acquire() as conn:
        fetch_query = database.Guild.select().where(
            database.Guild.c.guild == message.guild.id
        )
        cursor = await conn.execute(fetch_query)
        resp = await cursor.fetchone()
        shop_roles = None
        if resp is not None:
            shop_roles = resp[database.Guild.c.shop_roles]
        if shop_roles is not None:
            shop_roles_named = {
                message.guild.get_role(int(k)).name: k for k in shop_roles.keys()
            }
        else:
            await message.channel.send("No paid roles set. Tell your admins to set some.")
            return
        shop_roles_string = "\n".join(
                ": ".join((
                    str(message.guild.get_role(int(k)).name),
                    str(v))) for k, v in shop_roles.items())
        await message.channel.send(
            """
Current paid roles are: ```{0}```\n
Reply with the role name. Ensure you have the money!
Exit this menu by writing `exit`.
            """
            .format(shop_roles_string)
        )

        def check(m):
            return (m.channel == message.channel and
                    m.author.id != client.user.id and
                    m.author.id == message.author.id)
        try:
            role_id = None
            while role_id is None:
                _msg = await client.wait_for('message', check=check, timeout=120)
                msg = _msg.content
                if msg in shop_roles_named.keys():
                    role_id = shop_roles_named[msg]
                elif msg == 'exit':
                    await message.channel.send("Exited paid roles.")
                    return
                else:
                    await message.channel.send(
                        "Invalid role entered.\n" +
                        "Exit this menu by writing `exit`.")
            wallet = await _fetch_wallet(engine, message.author)
            if wallet - shop_roles[role_id] < 0:
                await message.channel.send("You don't have the money! :angry:")
            else:
                await _remove_money(engine, message.author, shop_roles[role_id])
                await message.author.add_roles(
                    message.guild.get_role(int(role_id)),
                    reason='Bought role.')
                await message.channel.send("Got ya the role :thumbsup:")
        except asyncio.TimeoutError:
            await message.channel.send("Error: Timeout.")


shop_functions = {
    'paidroles': (paid_roles, 'Get a role with $$$.'),
    'customrole': (buy_colored_role, 'Get a custom colored role with $$$$$$.')
}
