import aiohttp
import variables
import discord
import json
from random import randint
import datetime
from urllib.parse import quote


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


async def lmgtfy(client, message, *args):
    if len(args) == 0:
        await message.channel.send("{}lmgtfy <search string>".format(variables.PREFIX))
        return
    query = " ".join(args)
    url = variables.LMGTFY_URL + quote(query)
    print(url)
    embed = discord.Embed(
        title="LMGTFY", colour=message.author.colour, url=url,
        description="[{0}]({1})".format(query, url.replace("_", "\_")))
    await message.channel.send(embed=embed)


async def urban_dictionary(client, message, *args):
    if len(args) == 0:
        await message.channel.send("{}urbandictionary <search string>".format(variables.PREFIX))
        return
    query = " ".join(args)
    resp_txt = await _fetch_text(variables.UD_URL + quote(query))
    ud_reply = json.loads(resp_txt)['list']
    if len(ud_reply) == 0:
        await message.channel.send("No results found for this search string.")
        return
    rand_id = randint(0, len(ud_reply) - 1)
    ud_def = ud_reply[rand_id]
    embed = discord.Embed(
        title="Urban Dictionary: {0}".format(ud_def['word']),
        url=ud_def['permalink'], colour=message.author.colour
    )
    embed.add_field(
        name="Definition", inline=False,
        value=ud_def['definition'].replace("[", "").replace("]", ""))
    embed.add_field(
        name="Example", inline=False,
        value=ud_def['example'].replace("[", "").replace("]", ""))
    embed.add_field(name="Author", value=ud_def['author'])
    embed.add_field(
        name="Votes",
        value="{0} :thumbsup: {1} :thumbsdown:".format(
            ud_def['thumbs_up'], ud_def['thumbs_down']
        ))
    await message.channel.send(embed=embed)


async def eight_ball(client, message, *args):
    choices = [
        "Not so sure", "42", "Most likely", "Absolutely not", "Outlook is good",
        "I see good things happening", "Never", "Negative", "Could be",
        "Unclear, ask again", "Yes", "No", "Possible, but not probable"]
    rand_id = randint(0, len(choices) - 1)
    await message.channel.send("The 8-ball reads: {}".format(choices[rand_id]))


fun_functions = {  # Kek, this feels like I am stuttering to say functions.
    'avatar': (avatar_url, "View yours or someone's avatar."),
    'chucknorris': (chuck_norris, "A Chuck Norris joke."),
    'dadjoke': (dad_joke, "A (bad)dad joke."),
    'catfact': (cat_fact, "Cat facts."),
    'xkcd': (xkcd, 'xkcd.com'),
    'lmgtfy': (lmgtfy, "Let me google that for you."),
    'urbandictionary': (urban_dictionary, "Search urban dictionary."),
    '8ball': (eight_ball, "Get life advice.")
}
