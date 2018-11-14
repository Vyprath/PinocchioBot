import database
import discord
import asyncio
from variables import PREFIX


async def _get_characters(member_id, guild_id):
    engine = await database.prepare_engine()
    async with engine.acquire() as conn:
        fetch_query = database.RPGCharacter.select().where(
            database.RPGCharacter.c.member == member_id).where(
                database.RPGCharacter.c.guild == guild_id
            )
        cursor = await conn.execute(fetch_query)
        resp = await cursor.fetchall()
    return resp


async def _get_single_character(guild_id, char_id=None, char_name=None):
    if char_id is not None:
        fetch_query = database.RPGCharacter.select().where(
            database.RPGCharacter.c.guild == guild_id).where(
                database.RPGCharacter.c.id == char_id
            )
    elif char_name is not None:
        fetch_query = database.RPGCharacter.select().where(
            database.RPGCharacter.c.guild == guild_id).where(
            database.RPGCharacter.c.name.ilike('%' + char_name + '%'))
    else:
        return None
    engine = await database.prepare_engine()
    async with engine.acquire() as conn:
        cursor = await conn.execute(fetch_query)
        resp = await cursor.fetchall()
    if len(resp) == 0:
        return None
    return resp[0]


async def view_characters(client, message, *args):
    if len(message.mentions) == 0:
        member = message.author
    else:
        member = message.mentions[0]
    chars = await _get_characters(member.id, message.guild.id)
    msg = "Characters belonging to {0}:\n".format(member.name)
    if len(chars) == 0:
        msg += "User has no characters in this server.\n"
    else:
        for i, c in enumerate(chars):
            msg += "{0}. **{1}** Wallet: {2}, Level: {3}\n".format(
                i + 1, c[database.RPGCharacter.c.name],
                c[database.RPGCharacter.c.game_wallet],
                c[database.RPGCharacter.c.level])
            if len(msg) > 1800:
                await message.channel.send(msg)
                msg = ""
    msg += "To view details, do `{0}character <name/id>`".format(PREFIX)
    await message.channel.send(msg)


async def character(client, message, *args):
    if len(args) == 0:
        await message.channel.send("Usage: `{0}character <name/id>`".format(PREFIX))
        return
    elif len(args) == 1 and args[0].isdigit():
        char = await _get_single_character(guild_id=message.guild.id, char_id=int(args[0]))
    else:
        char = await _get_single_character(guild_id=message.guild.id, char_name=(" ".join(args)))
    if char is None:
        await message.channel.send("Character not found!")
    else:
        embed = discord.Embed(title=char[database.RPGCharacter.c.name], color=0x3e26f1)
        owner = message.guild.get_member(char[database.RPGCharacter.c.member])
        embed.set_footer(
            text="Owned by: {0}#{1}".format(owner.name, owner.discriminator),
            icon_url=owner.avatar_url)
        embed.add_field(
            name="Wallet", inline=False,
            value=char[database.RPGCharacter.c.game_wallet])
        embed.add_field(
            name="Level", inline=False,
            value=char[database.RPGCharacter.c.level])
        _weapon = char[database.RPGCharacter.c.weapon_id]
        if _weapon is None:
            weapon = "No weapon."
        else:
            engine = await database.prepare_engine()
            async with engine.acquire() as conn:
                fetch_query = database.RPGWeapon.select().where(
                    database.RPGWeapon.c.id == _weapon
                )
                cursor = await conn.execute(fetch_query)
                resp = await cursor.fetchone()
            weapon = resp[database.RPGWeapon.c.name]
        embed.add_field(name="Weapon", value=weapon, inline=False)
        await message.channel.send(embed=embed)


async def create_character(client, message, *args):
    name = ""
    confirmed = False

    def check(m):
        return (m.author.id != client.user.id and
                m.channel == message.channel and message.author.id == m.author.id)

    await message.channel.send("Welcome to character creation. Please enter character name:")
    while not confirmed:
        try:
            msg = await client.wait_for('message', check=check, timeout=120)
            name = msg.content
            if len(name) > 40:
                await message.channel.send("Please keep name under 40 characters.")
                continue
            if name == 'exit':
                await message.channel.send("Okay, exiting...")
                return
            await message.channel.send(
                "Name is \"{0}\", sure? Reply with `confirm`.".format(name))
            msg = await client.wait_for('message', check=check, timeout=60)
            if msg.content == 'confirm':
                confirmed = True
            else:
                await message.channel.send("Not confirmed, exiting...")
                return
        except asyncio.TimeoutError:
            await message.channel.send('Error: Timeout.')
            return
    engine = await database.prepare_engine()
    async with engine.acquire() as conn:
        insert_query = database.RPGCharacter.insert().values([{
            'member': message.author.id,
            'guild': message.guild.id,
            'name': name,
            'level': 1,
            'game_wallet': 0,
        }]).returning(database.RPGCharacter.c.id)
        cursor = await conn.execute(insert_query)
        id = await cursor.fetchone()
    await message.channel.send("Character successfully created with ID {0}".format(id[0]))


rpg_functions = {
    'viewcharacters': (view_characters, "View some user's characters"),
    'character': (character, "Get detailed info about a character"),
    'char': (character, "Get detailed info about a character"),
    'createcharacter': (create_character, "Create a RPG character"),
}
