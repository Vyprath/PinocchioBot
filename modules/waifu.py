import database


async def _search(client, message, *args):
    engine = await database.prepare_engine()
    async with engine.acquire() as conn:
        pass


async def waifu(client, message, *args):
    if len(args) == 1 and args[1] == 'search':
        return _search
    else:
        await message.channel.send("""Usage:
!waifu search <name>
!waifu details <name/id>
!waifu buy <name/id>
!waifu sell <name/id>
!waifu trade <user to trade with> <waifu name/id> <price>
""")
        return


waifu_functions = {
    'waifu': (waifu, "For your loneliness.")
}
