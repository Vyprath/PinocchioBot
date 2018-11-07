import variables
import aiohttp
import json
import discord


async def _get_gif_url(search_string):
    async with aiohttp.ClientSession() as session:
        async with session.get(variables.GIF_SEARCH_URL(search_string)) as resp:
            gifs = await resp.text()
            url = json.loads(gifs)['results'][0]['media'][0]['gif']['url']
            return url


def gif(gif_name=None, action="",  requires_mention=False):
    async def _gif(client, message, *args):
        if gif_name is not None:
            if requires_mention and len(message.mentions) == 0:
                await message.channel.send("Usage: `!{0} <@user mention>`".format(gif_name))
                return
            search_str = "anime " + gif_name
        else:
            if len(args) == 0:
                await message.channel.send("Usage: `!gif <search string>`")
                return
            else:
                search_str = ' '.join(args)
        if requires_mention:
            mention = message.mentions[0]
            mention_name = mention.name if mention.id != message.author.id else "themself ;-;"
            title = "{0} {1} {2}".format(message.author.name, action, mention_name)
        else:
            title = action.capitalize()
        gif_url = await _get_gif_url(search_str)
        embed = discord.Embed(title=title, color=0x4f00f2)
        embed.set_image(url=gif_url)
        await message.channel.send(embed=embed)
    return _gif


reactions_functions = {
    'facepalm': (gif('facepalm', "*Facepalms*"), None),
    'cry': (gif('cry', "*Cries*"), None),
    'laugh': (gif('laugh', "*Laughs*"), None),
    'confused': (gif('confused', "*Confused*"), None),
    'blush': (gif('blush', "*Blushes*"), None),
    'jojo': (gif('jojo', "*Jojo*"), None),
    'megumin': (gif('megumin', "*Explosion Loli*"), None),
    'satania': (gif('satania', "*Great Archdemon*"), None),
    'pout': (gif('pout', "*Pouts*"), None),
    'hug': (gif('hug', "hugs", True), None),
    'kiss': (gif('kiss', "kisses", True), None),
    'pat': (gif('pat', "pats", True), None),
    'dance': (gif('dance', "*Dances*"), None),
    'cudle': (gif('cudle', "*Cuddles*"), None),
    'tickle': (gif('tickle', "tickles", True), None),
    'bite': (gif('bite', "bites", True), None),
    'kick': (gif('kick', "kicks", True), None),
    'slap': (gif('slap', "slaps", True), None),
    'punch': (gif('punch', "punches", True), None),
    'nom': (gif('nom', "*Nom Nom*"), None),
    'lick': (gif('lick', "*Lick Lick*"), None),
    'think': (gif('think', "*Thinks*"), None),
    'shrug': (gif('shrug', "*Shrugs*"), None),
    'owo': (gif('owo', "**OwO**"), None),
    'eyeroll': (gif('eyeroll', "*Rolls eyes*"), None),
    'lewd': (gif('lewd', "**LEWD ALERT**"), None),
    'poke': (gif('poke', "pokes", True), None),
    'stare': (gif('stare', "*Stares*"), None),
    'triggered': (gif('triggered', "*Triggered*"), None),
    'gif': (gif(), None)
}
