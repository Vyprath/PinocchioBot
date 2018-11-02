from .currency import _remove_money, _fetch_wallet
import database
import asyncio


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
Exit this menu by writing `exit-paid-roles`.
            """
            .format(shop_roles_string)
        )

        def check(m):
            return m.channel == message.channel and m.author.id != client.user.id
        try:
            role_id = None
            while role_id is None:
                _msg = await client.wait_for('message', check=check, timeout=120)
                msg = _msg.content
                if msg in shop_roles_named.keys():
                    role_id = shop_roles_named[msg]
                elif msg == 'exit-paid-roles':
                    await message.channel.send("Exited paid roles.")
                    return
                else:
                    await message.channel.send(
                        "Invalid role entered.\n" +
                        "Exit this menu by writing `exit-paid-roles`.")
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
    'paidroles': (paid_roles, 'Get a role with $$$.')
}
