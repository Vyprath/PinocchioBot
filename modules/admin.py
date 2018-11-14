import database
import asyncio
from variables import PREFIX


async def clean(client, message, *args):
    if not message.author.guild_permissions.administrator:
        await message.channel.send("This command is restricted, to be used only by gods.")
        return
    if len(args) != 1 or not args[0].isdigit() or not (1 <= int(args[0]) <= 100):
        await message.channel.send("Usage: {0}purge <limit between 1 to 100>".format(PREFIX))
        return
    limit = int(args[0])
    await message.channel.purge(limit=limit)
    msg = await message.channel.send("Successfully deleted {0} messages. :thumbsup:".format(limit))
    await asyncio.sleep(3)
    await msg.delete()


async def set_paid_roles(client, message, *args):
    if not message.author.guild_permissions.administrator:
        await message.channel.send("This command is restricted, to be used only by gods.")
        return
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
To set, run `{1}setpaidroles set <role mention> <amount>`\n
To remove, run `{1}setpaidroles delete <role mention>`
            """
            .format(shop_roles_string, PREFIX)
        )
    elif len(args) == 3 and args[0] == "set" and args[2].isdigit():
        if len(message.role_mentions) == 0:
            await message.channel.send("Please mention proper role.")
        else:
            role = message.role_mentions[0]
            amount = int(args[2])
            if shop_roles:
                shop_roles.update({role.id: amount})
            else:
                shop_roles = {role.id: amount}
            async with engine.acquire() as conn:
                update_query = database.Guild.update().where(
                    database.Guild.c.guild == message.guild.id
                ).values(shop_roles=shop_roles)
            await conn.execute(update_query)
            await message.channel.send("Done.")
    elif len(args) == 2 and args[0] == "delete":
        if len(message.role_mentions) == 0:
            await message.channel.send("Please mention proper role.")
        else:
            role = message.role_mentions[0]
            if shop_roles and str(role.id) in shop_roles.keys():
                shop_roles.pop(str(role.id))
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


admin_functions = {
    'setpaidroles': (set_paid_roles, None),
    'purge': (clean, "Purge X messages from this channel.")
}
