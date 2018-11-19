from PIL import Image, ImageDraw, ImageFont
import aiohttp
import discord
import database
import io


async def make_join_leave_image(image_url, header, subtitle):
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as resp:
            image_bytes = await resp.read()
    profile_pic = Image.open(io.BytesIO(image_bytes), 'r')
    profile_pic = profile_pic.resize((160, 160), Image.ANTIALIAS)
    background = Image.open("assets/background_1.jpg", 'r')
    font_1 = ImageFont.truetype("assets/DiscordFont.otf", 28)
    font_2 = ImageFont.truetype("assets/DiscordFont.otf", 20)
    bigsize = (profile_pic.size[0] * 3, profile_pic.size[1] * 3)
    mask = Image.new('L', bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(profile_pic.size, Image.ANTIALIAS)
    profile_pic.putalpha(mask)
    background.paste(profile_pic, (240, 48), profile_pic)
    draw = ImageDraw.Draw(background)
    w, h = draw.textsize(header, font=font_1)
    draw.text(((640-w)/2, 240), header, font=font_1)
    w, h = draw.textsize(subtitle, font=font_2)
    draw.text(((640-w)/2, 290), subtitle, font=font_2)
    byte_io = io.BytesIO()
    background.save(byte_io, 'PNG')
    byte_io.flush()
    byte_io.seek(0)
    return discord.File(fp=byte_io, filename='discord.png')


async def send_on_member_join(member):
    engine = await database.prepare_engine()
    async with engine.acquire() as conn:
        fetch_query = database.Guild.select().where(
            database.Guild.c.guild == member.guild.id
            )
        cursor = await conn.execute(fetch_query)
        result = await cursor.fetchone()
        channel = member.guild.get_channel(result[database.Guild.c.join_leave_channel])
        welcome_str = result[database.Guild.c.welcome_str]
    if channel is None or welcome_str is None:
        return
    img = await make_join_leave_image(
        member.avatar_url,
        "{0}#{1} has joined".format(member.name, member.discriminator).capitalize(),
        welcome_str
        )
    await channel.send(file=img)


async def send_on_member_leave(member):
    engine = await database.prepare_engine()
    async with engine.acquire() as conn:
        fetch_query = database.Guild.select().where(
            database.Guild.c.guild == member.guild.id
            )
        cursor = await conn.execute(fetch_query)
        result = await cursor.fetchone()
        channel = member.guild.get_channel(result[database.Guild.c.join_leave_channel])
        leave_str = result[database.Guild.c.leave_str]
    if channel is None or leave_str is None:
        return
    img = await make_join_leave_image(
        member.avatar_url,
        "{0}#{1} has left".format(member.name, member.discriminator),
        leave_str
        )
    await channel.send(file=img)
