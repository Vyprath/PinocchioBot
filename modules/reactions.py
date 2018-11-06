import variables
import aiohttp
import json
import discord


async def _get_gif(search_string):
    async with aiohttp.ClientSession() as session:
        async with session.get(variables.GIF_SEARCH_URL(search_string)) as resp:
            gifs = await resp.text()
            url = json.loads(gifs)['results'][0]['media'][0]['gif']['url']
        async with session.get(url) as resp:
            gif = await resp.read()
        return gif


def gif(gif_name=None):
    async def _gif(client, message, *args):
        if gif_name is not None:
            search_str = "anime " + gif_name
        else:
            if len(args) == 0:
                await message.channel.send("Usage: `!gif <search string>`")
                return
            else:
                search_str = ' '.join(*args)
        gif = await _get_gif(search_str)
        await message.channel.send(file=discord.File(gif, filename=(search_str + ".gif")))
    return _gif


reactions_functions = {
    'cry': (gif('cry'), None),
    'laugh': (gif('laugh'), None),
    'confused': (gif('confused'), None),
    'blush': (gif('blush'), None),
    'jojo': (gif('jojo'), None),
    'megumin': (gif('megumin'), None),
    'satania': (gif('satania'), None),
    'pout': (gif('pout'), None),
    'hug': (gif('hug'), None),
    'kiss': (gif('kiss'), None),
    'pat': (gif('pat'), None),
    'dance': (gif('dance'), None),
    'cudle': (gif('cudle'), None),
    'tickle': (gif('tickle'), None),
    'bite': (gif('bite'), None),
    'kick': (gif('kick'), None),
    'slap': (gif('slap'), None),
    'punch': (gif('punch'), None),
    'nom': (gif('nom'), None),
    'lick': (gif('lick'), None),
    'think': (gif('think'), None),
    'owo': (gif('owo'), None),
    'eyeroll': (gif('eyeroll'), None),
    'lewd': (gif('lewd'), None),
    'poke': (gif('poke'), None),
    'stare': (gif('stare'), None),
    'triggered': (gif('triggered'), None),
    'gif': (gif(), None)
}
