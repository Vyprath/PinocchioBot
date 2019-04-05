import database
import asyncio
from variables import PREFIX


async def clean(client, message, *args):
    if not message.author.guild_permissions.administrator:
        await message.channel.send("This command is restricted, to be used only by admins.")
        return
    if len(args) != 1 or not args[0].isdigit() or not (1 <= int(args[0]) <= 100):
        await message.channel.send("Usage: {0}purge <limit between 1 to 100>".format(PREFIX))
        return
    limit = int(args[0])
    await message.channel.purge(limit=limit)
    msg = await message.channel.send("Successfully deleted {0} messages. :thumbsup:".format(limit))
    await asyncio.sleep(3)
    await msg.delete()


async def set_welcome_leave_channel(client, message, *args):
    if not message.author.guild_permissions.administrator:
        await message.channel.send("This command is restricted, to be used only by admins.")
        return
    engine = await database.prepare_engine()
    async with engine.acquire() as conn:
        fetch_query = database.Guild.select().where(
            database.Guild.c.guild == message.guild.id
        )
        cursor = await conn.execute(fetch_query)
        resp = await cursor.fetchone()
        channel = message.guild.get_channel(
            resp[database.Guild.c.join_leave_channel])
    if len(args) == 0:
        if channel:
            channel_string = channel.name
        else:
            channel_string = "None"
        await message.channel.send(
            """
Current welcome/leave message channel: {0}\n
To set, run `{1}setwlchannel set <channel id>`. To get channel ID, please Google.
To disable, run `{1}setwlchannel disable`.
            """
            .format(channel_string, PREFIX)
        )
    elif len(args) == 2 and args[0] == "set" and args[1].isdigit():
        new_channel = message.guild.get_channel(int(args[1]))
        if new_channel is None:
            await message.channel.send("Channel with this ID does not exist.")
        else:
            async with engine.acquire() as conn:
                update_query = database.Guild.update().where(
                    database.Guild.c.guild == message.guild.id
                ).values(join_leave_channel=new_channel.id)
            await conn.execute(update_query)
            await message.channel.send("Done.")
    elif len(args) == 1 and args[0] == "disable":
        async with engine.acquire() as conn:
            update_query = database.Guild.update().where(
                database.Guild.c.guild == message.guild.id
            ).values(join_leave_channel=None)
        await conn.execute(update_query)
        await message.channel.send("Done.")
    else:
        await message.channel.send("Invalid command.")


async def set_paid_roles(client, message, *args):
    if not message.author.guild_permissions.administrator:
        await message.channel.send("This command is restricted, to be used only by admins.")
        return
    available_role_names = {
        r.name.lower().strip(): r for r in message.guild.roles if not r.name == "@everyone"}
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
    if len(args) == 0:
        if shop_roles:
            shop_roles_string = "\n".join(
                ": ".join((
                    str(message.guild.get_role(int(k)).name),
                    str(v))) for k, v in shop_roles.items())
        else:
            shop_roles_string = "No paid roles set."
        await message.channel.send(
            """
Current paid roles are: ```{0}```\n
To set, run `{1}setpaidroles set <amount> "<role name>"`\n
To remove, run `{1}setpaidroles delete <role name>`
            """
            .format(shop_roles_string, PREFIX)
        )
    elif len(args) >= 3 and args[0] == "set" and args[1].isdigit():
        mentioned_role = " ".join(args[2:])
        if mentioned_role.lower().strip() in available_role_names.keys():
            mentioned_role = available_role_names[mentioned_role.lower().strip()]
        else:
            await message.channel.send("No role in server with that name.")
            return
        amount = int(args[1])
        if shop_roles:
            shop_roles.update({mentioned_role.id: amount})
        else:
            shop_roles = {mentioned_role.id: amount}
        async with engine.acquire() as conn:
            update_query = database.Guild.update().where(
                database.Guild.c.guild == message.guild.id
            ).values(shop_roles=shop_roles)
            await conn.execute(update_query)
            await message.channel.send("Done.")
    elif len(args) >= 2 and args[0] == "delete":
        mentioned_role = " ".join(args[1:])
        if mentioned_role.lower().strip() in available_role_names.keys():
            mentioned_role = available_role_names[mentioned_role.lower().strip()]
        else:
            await message.channel.send("No role in server with that name.")
            return
        if shop_roles and str(mentioned_role.id) in shop_roles.keys():
            shop_roles.pop(str(mentioned_role.id))
            async with engine.acquire() as conn:
                update_query = database.Guild.update().where(
                    database.Guild.c.guild == message.guild.id
                ).values(shop_roles=shop_roles)
                await conn.execute(update_query)
                await message.channel.send("Done.")
        else:
            await message.channel.send("Role not present.")
    else:
        await message.channel.send("Invalid command.")


async def set_welcome_msg(client, message, *args):
    if not message.author.guild_permissions.administrator:
        await message.channel.send("This command is restricted, to be used only by admins.")
        return
    if len(args) == 0:
        await message.channel.send(
            "Usage: `{0}setwelcome` <welcome text, less than 61 chars. Write \"None\" for no welcome message>".format(PREFIX))  # noqa
        return
    welcome_str = " ".join(args)
    if len(welcome_str) > 60:
        await message.channel.send("Error: Text larger than 60 characters.")
        return
    if welcome_str == "None":
        welcome_str = None
    engine = await database.prepare_engine()
    async with engine.acquire() as conn:
        update_query = database.Guild.update().where(
            database.Guild.c.guild == message.guild.id
        ).values(welcome_str=welcome_str)
        await conn.execute(update_query)
    if welcome_str:
        await message.channel.send("Done.")
    else:
        await message.channel.send("Disabled welcome message.")


async def set_leave_msg(client, message, *args):
    if not message.author.guild_permissions.administrator:
        await message.channel.send("This command is restricted, to be used only by admins.")
        return
    if len(args) == 0:
        await message.channel.send(
            "Usage: `{0}setleave` <leave text, less than 61 chars. Write \"None\" for no leave message>".format(PREFIX))  # noqa
        return
    leave_str = " ".join(args)
    if len(leave_str) > 60:
        await message.channel.send("Error: Text larger than 60 characters.")
        return
    if leave_str == "None":
        leave_str = None
    engine = await database.prepare_engine()
    async with engine.acquire() as conn:
        update_query = database.Guild.update().where(
            database.Guild.c.guild == message.guild.id
        ).values(leave_str=leave_str)
        await conn.execute(update_query)
    if leave_str:
        await message.channel.send("Done.")
    else:
        await message.channel.send("Disabled leave message.")


async def set_coin_drops(client, message, *args):
    if not message.author.guild_permissions.administrator:
        await message.channel.send("This command is restricted, to be used only by admins.")
        return
    if len(args) == 0:
        await message.channel.send(
            "Usage: `{0}coindrops` <disable/enable>".format(PREFIX))  # noqa
        return
    input_str = " ".join(args).lower()
    if input_str == "enable":
        engine = await database.prepare_engine()
        async with engine.acquire() as conn:
            update_query = database.Guild.update().where(
                database.Guild.c.guild == message.guild.id
            ).values(coin_drops=True)
            await conn.execute(update_query)
            await message.channel.send("Enabled coin drops.")
    elif input_str == "disable":
        engine = await database.prepare_engine()
        async with engine.acquire() as conn:
            update_query = database.Guild.update().where(
                database.Guild.c.guild == message.guild.id
            ).values(coin_drops=False)
            await conn.execute(update_query)
            await message.channel.send("Disabled coin drops.")
    else:
        await message.channel.send("Invalid command.")


async def set_custom_roles(client, message, *args):
    if not message.author.guild_permissions.administrator:
        await message.channel.send("This command is restricted, to be used only by admins.")
        return
    if len(args) != 1 or not args[0].lstrip("-").isdigit():
        await message.channel.send(
            "Usage: {}setcustomroles <price (-1 for disabling)>".format(PREFIX))
        return
    price = int(args[0])
    engine = await database.prepare_engine()
    async with engine.acquire() as conn:
        update_query = database.Guild.update().where(
            database.Guild.c.guild == message.guild.id
        ).values(custom_role=price)
        await conn.execute(update_query)
    if price < 0:
        await message.channel.send("Successfully disabled custom roles.")
    else:
        await message.channel.send("Set custom roles price to {}.".format(price))


async def remove_abandoned_waifus(client, message, *args):
    if not message.author.guild_permissions.administrator:
        await message.channel.send("This command is restricted, to be used only by admins.")
        return
    await message.channel.send(":skull_crossbones: This command will remove all waifus from users who left the server. Do you want to proceed? Type `confirm` in 15s.")  # noqa

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
    engine = await database.prepare_engine()
    async with engine.acquire() as conn:
        delete_query = database.PurchasedWaifu.delete().where(
            database.PurchasedWaifu.c.guild == message.guild.id
        ).where(
            database.PurchasedWaifu.c.member.notin_()
        )
        await conn.execute(delete_query)
    await message.channel.send(":skull_crossbones: Removed waifus from people who left the server.")



admin_functions = {
    'setpaidroles': (set_paid_roles, "Set up paid roles."),
    'setwlchannel': (set_welcome_leave_channel, "Set welcome/leave message channel."),
    'setwelcome': (set_welcome_msg, "Set the text for the welcome message."),
    'setleave': (set_leave_msg, "Set the text for the leave message."),
    'setcustomroles': (set_custom_roles, "Change the settings for custom roles."),
    'purge': (clean, "Purge X messages from this channel."),
    'coindrops': (set_coin_drops, "Enable/Disable coin drops for a server. Default: disabled."),
}
