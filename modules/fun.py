import aiohttp
import variables
import discord
import json
from random import randint
import datetime


async def avatar_url(client, message, *args):
    if len(message.mentions) == 0:
        member = message.author
    else:
        member = message.mentions[0]
    embed = discord.Embed(
        title="{0}#{1}'s Avatar".format(member.name, member.discriminator),
        url=member.avatar_url, colour=member.colour
    )
    embed.set_image(url=member.avatar_url)
    await message.channel.send(embed=embed)


async def _fetch_text(url, headers={}):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            txt = await resp.text()
            return txt


async def chuck_norris(client, message, *args):
    resp_txt = await _fetch_text(variables.ICNDB_RANDOM_JOKE_URL)
    joke = json.loads(resp_txt)['value']['joke']
    await message.channel.send(joke)


async def dad_joke(client, message, *args):
    headers = {'Accept': 'application/json'}
    resp_txt = await _fetch_text(variables.DADJOKE_URL, headers)
    joke = json.loads(resp_txt)['joke']
    await message.channel.send(joke)


async def cat_fact(client, message, *args):
    resp_txt = await _fetch_text(variables.CATFACT_URL)
    fact = json.loads(resp_txt)['fact']
    await message.channel.send(fact)


latest_xkcd_id = -1
last_xkcd_latest_store = None


async def xkcd(client, message, *args):
    global latest_xkcd_id
    global last_xkcd_latest_store
    now = datetime.datetime.now()
    if latest_xkcd_id == -1 or (now - last_xkcd_latest_store).days > 1:
        latest = await _fetch_text("https://xkcd.com/info.0.json")
        last = json.loads(latest)['num']
        latest_xkcd_id = last
        last_xkcd_latest_store = now
    rand_id = randint(1, latest_xkcd_id)
    random = await _fetch_text("https://xkcd.com/{}/info.0.json".format(rand_id))
    img_url = json.loads(random)['img']
    embed = discord.Embed(
        title="XKCD #{0}".format(rand_id),
        url="https://xkcd.com/{}".format(rand_id),
        colour=message.author.colour
    )
    embed.set_image(url=img_url)
    await message.channel.send(embed=embed)


fun_functions = {  # Kek, this feels like I am stuttering to say functions.
    'avatar': (avatar_url, "View yours or someone's avatar."),
    'chucknorris': (chuck_norris, "A Chuck Norris joke."),
    'dadjoke': (dad_joke, "A (bad)dad joke."),
    'catfact': (cat_fact, "Cat facts."),
    'xkcd': (xkcd, 'xkcd.com'),
}
