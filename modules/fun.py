import datetime
import html
import io
import json
import textwrap
from random import randint
from urllib.parse import quote

import aiohttp
import discord
from PIL import Image, ImageDraw

import variables
from variables import PREFIX


async def avatar_url(client, message, *args):
    if len(message.mentions) == 0:
        member = message.author
    else:
        member = message.mentions[0]
    url = str(member.avatar_url)
    embed = discord.Embed(
        title=f"{member.name}#{member.discriminator}'s Avatar",
        url=url,
        colour=member.colour,
    )
    embed.set_image(url=avatar_url)
    await message.channel.send(embed=embed)


async def _fetch_text(url, headers={}, json=False):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if json:
                return await resp.json()
            return await resp.text()


async def chuck_norris(client, message, *args):
    resp_txt = await _fetch_text("http://api.icndb.com/jokes/random", json=True)
    joke = resp_txt["value"]["joke"]
    joke = html.unescape(joke)
    await message.channel.send(joke)


async def dad_joke(client, message, *args):
    headers = {"Accept": "application/json"}
    resp_txt = await _fetch_text("https://icanhazdadjoke.com", headers, json=True)
    joke = resp_txt["joke"]
    await message.channel.send(joke)


async def cat_fact(client, message, *args):
    resp_txt = await _fetch_text("https://catfact.ninja/fact", json=True)
    fact = resp_txt["fact"]
    await message.channel.send(fact)


LATEST_XKCD_ID = -1
LAST_XKCD_LATEST_STORE = None


async def xkcd(client, message, *args):
    global LATEST_XKCD_ID
    global LAST_XKCD_LATEST_STORE
    now = datetime.datetime.now()
    if LATEST_XKCD_ID == -1 or (now - LAST_XKCD_LATEST_STORE).days > 1:
        latest = await _fetch_text("https://xkcd.com/info.0.json")
        last = json.loads(latest)["num"]
        latest_xkcd_id = last
    rand_id = randint(1, latest_xkcd_id)
    random = await _fetch_text(f"https://xkcd.com/{rand_id}/info.0.json")
    img_url = json.loads(random)["img"]
    embed = discord.Embed(
        title=f"XKCD #{rand_id}",
        url=f"https://xkcd.com/{rand_id}",
        colour=message.author.colour,
    )
    embed.set_image(url=img_url)
    await message.channel.send(embed=embed)


async def lmgtfy(client, message, *args):
    if len(args) == 0:
        await message.channel.send(f"{PREFIX}lmgtfy <search string>")
        return
    query = " ".join(args)
    url = f"https://lmgtfy.com/?q={quote(query)}"
    embed = discord.Embed(
        title="LMGTFY",
        colour=message.author.colour,
        url=url,
        description="[{0}]({1})".format(query, url.replace("_", r"\_")),
    )
    await message.channel.send(embed=embed)


async def urban_dictionary(client, message, *args):
    if len(args) == 0:
        await message.channel.send(
            f"{PREFIX}urbandictionary <search string>".format(variables.PREFIX)
        )
        return
    query = " ".join(args)
    resp_txt = await _fetch_text(
        f"https://api.urbandictionary.com/v0/define?term={quote(query)}"
    )
    ud_reply = json.loads(resp_txt)["list"]
    if len(ud_reply) == 0:
        await message.channel.send("No results found for this search string.")
        return
    exact_ud_reply = [i for i in ud_reply if i["word"].lower() == query.lower()]
    if len(exact_ud_reply) > 0:
        ud_reply = exact_ud_reply
    rand_id = randint(0, len(ud_reply) - 1)
    ud_def = ud_reply[rand_id]
    embed = discord.Embed(
        title=f"Urban Dictionary: {ud_def['word']}",
        url=ud_def["permalink"],
        colour=message.author.colour,
    )
    definition = ud_def["definition"].replace("[", "").replace("]", "")
    if len(definition) > 1000:
        definition = definition[:1000] + "..."
    embed.add_field(name="Definition", inline=False, value=definition)
    example = ud_def["example"].replace("[", "").replace("]", "")
    if len(example) > 1000:
        example = example[:1000] + "..."
    embed.add_field(name="Example", inline=False, value=example)
    embed.add_field(name="Author", value=ud_def["author"])
    embed.add_field(
        name="Votes",
        value=f"{ud_def['thumbs_up']} :thumbsup: {ud_def['thumbs_down']} :thumbsdown:",
    )
    await message.channel.send(embed=embed)


async def eight_ball(client, message, *args):
    choices = [
        "Not so sure",
        "42",
        "Most likely",
        "Absolutely not",
        "Outlook is good",
        "I see good things happening",
        "Never",
        "Negative",
        "Could be",
        "Unclear, ask again",
        "Yes",
        "No",
        "Possible, but not probable",
    ]
    rand_id = randint(0, len(choices) - 1)
    await message.channel.send(f"The 8-ball reads: {choices[rand_id]}")


async def cowsay(client, message, *args):
    if len(args) == 0:
        await message.channel.send(f"USAGE: {PREFIX}cowsay <text>")
        return
    text = discord.utils.escape_mentions(" ".join(args)).replace("`", "\u200b`")
    await message.channel.send("```css\n" + _cowsay(text) + "```")


async def cook_user(client, message, *args):
    if len(message.mentions) == 0:
        await message.channel.send(f"USAGE: {PREFIX}cook <@user mention>")
        return
    cooked_user = message.mentions[0]
    profile_pic = Image.open(
        io.BytesIO(await _get_img_bytes_from_url(str(cooked_user.avatar_url))), "r"
    )
    profile_pic = profile_pic.resize((294, 294), Image.ANTIALIAS)
    background = Image.open("assets/plate.jpg", "r")
    bigsize = (profile_pic.size[0] * 3, profile_pic.size[1] * 3)
    mask = Image.new("L", bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(profile_pic.size, Image.ANTIALIAS)
    profile_pic.putalpha(mask)
    w, h = profile_pic.size
    pts = (348 - w // 2, 231 - h // 2)
    background.paste(profile_pic, pts, profile_pic)
    byte_io = io.BytesIO()
    background.save(byte_io, "PNG")
    byte_io.flush()
    byte_io.seek(0)
    await message.channel.send(
        file=discord.File(
            fp=byte_io, filename=f'cooked_{cooked_user.name.replace(" ", "_")}.png'
        )
    )


async def hjail(client, message, *args):
    if len(message.mentions) == 0:
        await message.channel.send(f"USAGE: {PREFIX}hjail <@user mention>")
        return
    cooked_user = message.mentions[0]
    profile_pic = Image.open(
        io.BytesIO(await _get_img_bytes_from_url(str(cooked_user.avatar_url))), "r"
    )
    profile_pic = profile_pic.resize((294, 294), Image.ANTIALIAS)
    background = Image.open("assets/hjail.png", "r")
    bigsize = (profile_pic.size[0] * 3, profile_pic.size[1] * 3)
    mask = Image.new("L", bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(profile_pic.size, Image.ANTIALIAS)
    profile_pic.putalpha(mask)
    w, h = profile_pic.size
    pts = (1074 - w // 2, 582 - h // 2)
    background.paste(profile_pic, pts, profile_pic)
    byte_io = io.BytesIO()
    background.save(byte_io, "PNG")
    byte_io.flush()
    byte_io.seek(0)
    await message.channel.send(
        file=discord.File(
            fp=byte_io, filename=f'jailed_{cooked_user.name.replace(" ", "_")}.png'
        )
    )


async def _get_img_bytes_from_url(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            image_bytes = await resp.read()
            return image_bytes


def _cowsay(string, length=40):
    return build_bubble(string, length) + build_cow()


def build_cow():
    return r"""
         \   ^__^
          \  (oo)\_______
             (__)\       )\/\\
                 ||----w |
                 ||     ||
    """


def build_bubble(string, length=40):
    bubble = []
    lines = normalize_text(string, length)
    bordersize = len(lines[0])
    bubble.append("  " + "-" * bordersize)
    for index, line in enumerate(lines):
        border = get_border(lines, index)
        bubble.append("%s %s %s" % (border[0], line, border[1]))
        bubble.append("  " + "-" * bordersize)
    return "\n".join(bubble)


def normalize_text(string, length):
    lines = textwrap.wrap(string, length)
    maxlen = len(max(lines, key=len))
    return [line.ljust(maxlen) for line in lines]


def get_border(lines, index):
    if len(lines) < 2:
        return ["<", ">"]
    elif index == 0:
        return ["/", "\\"]
    elif index == len(lines) - 1:
        return ["\\", "/"]
    return ["|", "|"]


fun_functions = {  # Kek, this feels like I am stuttering to say functions.
    "avatar": (
        avatar_url,
        "`{P}avatar [optional: @user mention]`: View yours or someone's avatar.",
    ),
    "chucknorris": (chuck_norris, "`{P}chucknorris`: A Chuck Norris about joke."),
    "dadjoke": (dad_joke, "`{P}dadjoke`: A (bad)dad joke."),
    "catfact": (cat_fact, "`{P}catfact`: Cat facts."),
    "xkcd": (xkcd, "`{P}xkcd`: Random xkcd comic strip."),
    "lmgtfy": (lmgtfy, "`{P}lmgtfy`: Let me google that for you."),
    "urbandictionary": (
        urban_dictionary,
        "`{P}urbandictionary`: Search urban dictionary.",
    ),
    "udict": (urban_dictionary, "`{P}urbandict`: Search urban dictionary."),
    "urbandict": (urban_dictionary, "`{P}urbandict`: Search urban dictionary."),
    "8ball": (eight_ball, "`{P}8ball`: Get life advice."),
    "cowsay": (
        cowsay,
        "`{P}cowsay`: Cow says moo. And you can order the cow to speak for you.",
    ),
    "cook": (cook_user, "`{P}cook`: Cook someone tastily."),
    "hjail": (hjail, "`{P}cook`: Send someone to the horny jail."),
}
