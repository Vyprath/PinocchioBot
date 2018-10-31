import database
# TODO: Handle in case profile not yet created.


async def fetch_wallet(engine, member):
    async with engine.acquire() as conn:
        fetch_query = database.Member.select().where(
            database.Member.c.guild == member.guild.id and
            database.Member.c.member == member.id
        )
        cursor = await conn.execute(fetch_query)
        resp = await cursor.fetchone()
        if resp is None:
            return None
        else:
            return resp[database.Member.c.wallet]


async def _get_money(engine, member, amount):
    current_balance = await fetch_wallet(engine, member)
    if current_balance is None:
        return None
    async with engine.acquire() as conn:
        update_query = database.Member.update().where(
            database.Member.c.guild == member.guild.id and
            database.Member.c.member == member.id
        ).values(wallet=current_balance + amount)
        await conn.execute(update_query)
    return current_balance + amount

async def check_wallet(client, message, *args):
    engine = await database.prepare_engine()
    if len(args) == 0:
        wallet = await fetch_wallet(engine, message.author)
        if wallet is None:
            await database.make_member_profile([message.author], client.user.id)
            wallet = await fetch_wallet(engine, message.author)
        await message.channel.send(
            "Heya, {0}. You have `{1}` coins in your wallet."
            .format(message.author.mention, wallet)
            )


async def get_money(client, message, *args):
    if not message.author.guild_permissions.administrator:
        await message.channel.send("This command is restricted, to be used only by gods.")
        return
    if len(args) == 0 or not args[0].isdigit():
        await message.channel.send("Correct command is: `wallet <amount>`")
    else:
        amount = int(args[0])
        engine = await database.prepare_engine()
        balance = await _get_money(engine, message.author, amount)
        await message.channel.send(
            "Gave `{0}` coins. You now have `{1}` coins in your wallet."
            .format(amount, balance)
            )


currency_functions = {
    'wallet': (check_wallet, 'Check your wallet.'),
    'get-money': (get_money, 'Get yourself some coins.')
}
currency_handlers = []
