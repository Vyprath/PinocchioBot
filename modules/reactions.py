import aiohttp
import discord

import variables
from variables import PREFIX

tenor_anon_id = None


async def _get_gif_url(search_string):
    global tenor_anon_id
    async with aiohttp.ClientSession() as session:
        if tenor_anon_id is None:
            async with session.get(
                f"https://api.tenor.com/v1/anonid?key={variables.TENOR_API_TOKEN}"
            ) as resp:
                resp_json = await resp.json()
                tenor_anon_id = resp_json["anon_id"]

        search_url = f"https://api.tenor.com/v1/random?q={search_string}&key={variables.TENOR_API_TOKEN}&limit=1&anon_id={tenor_anon_id}&media_filter=minimal"  # noqa
        async with session.get(search_url) as resp:
            resp_json = await resp.json()
            url = resp_json["results"][0]["media"][0]["gif"]["url"]
            return url


def gif(gif_name=None, action="", requires_mention=False):
    async def _gif(client, message, *args):
        if gif_name is not None:
            try:
                mention = message.mentions[0]  # Check if mentions is @user
                mention_name = (
                    mention.name if mention.id != message.author.id else "themself ;-;"
                )
            except IndexError:
                mention_name = (
                    discord.utils.escape_mentions(
                        " ".join(args)
                    )  # or args[0] to show only mentions?
                    if args[0] in ["@​here", "@​everyone"]
                    else ""
                )
            if requires_mention and mention_name != "":
                await message.channel.send(
                    f"Usage: `{PREFIX}{gif_name} <@mention>`"  # No longer limited to user mentions yey
                )
                return
            search_str = "anime " + gif_name
        else:
            if len(args) == 0:
                await message.channel.send(f"Usage: `{PREFIX}gif <search string>`")
                return
            else:
                search_str = " ".join(args)
        if requires_mention:
            title = f"{message.author.name} {action} {mention_name}"
        else:
            title = action.capitalize()
        gif_url = await _get_gif_url(search_str)
        embed = discord.Embed(title=title, color=message.author.colour)
        embed.set_image(url=gif_url)
        await message.channel.send(embed=embed)

    return _gif


reactions_functions = {
    "facepalm": (gif("facepalm", "*Facepalms*"), None),
    "cry": (gif("cry", "*Cries*"), None),
    "laugh": (gif("laugh", "*Laughs*"), None),
    "confused": (gif("confused", "*Confused*"), None),
    "blush": (gif("blush", "*Blushes*"), None),
    "jojo": (gif("jojo", "*Jojo*"), None),
    "megumin": (gif("megumin", "*Explosion Loli*"), None),
    "satania": (gif("satania", "*Great Archdemon*"), None),
    "pout": (gif("pout", "*Pouts*"), None),
    "hug": (gif("hug", "hugs", True), None),
    "kiss": (gif("kiss", "kisses", True), None),
    "pat": (gif("pat", "pats", True), None),
    "dance": (gif("dance", "*Dances*"), None),
    "cudle": (gif("cudle", "*Cuddles*"), None),
    "tickle": (gif("tickle", "tickles", True), None),
    "bite": (gif("bite", "bites", True), None),
    "stab": (gif("stab", "stabs", True), None),
    "seduce": (gif("seduce", "seduces", True), None),
    "kick": (gif("kick", "kicks", True), None),
    "slap": (gif("slap", "slaps", True), None),
    "punch": (gif("punch", "punches", True), None),
    "nom": (gif("nom", "*Nom Nom*"), None),
    "lick": (gif("lick", "*Lick Lick*"), None),
    "think": (gif("think", "*Thinks*"), None),
    "shrug": (gif("shrug", "*Shrugs*"), None),
    "owo": (gif("owo", "**OwO**"), None),
    "eyeroll": (gif("eyeroll", "*Rolls eyes*"), None),
    "lewd": (gif("lewd", "**LEWD ALERT**"), None),
    "poke": (gif("poke", "pokes", True), None),
    "stare": (gif("stare", "*Stares*"), None),
    "triggered": (gif("triggered", "*Triggered*"), None),
    "gif": (gif(), "`{P}gif <search string>`: Search for a GIF."),
}
