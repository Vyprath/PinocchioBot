import asyncio
import datetime
import json
from base64 import b64encode
from io import BytesIO

import aiohttp
import discord
from jikanpy import AioJikan
from jikanpy.exceptions import APIException
from NyaaPy import Nyaa
from PIL import Image

from variables import PREFIX, TRACE_MOE_TOKEN

from .utils import chunks


async def make_anime_embed(loop, mal_id, color=0x00000000, init_fields=[]):
    jikan = AioJikan()
    anime = await jikan.anime(mal_id)
    synopsis = anime["synopsis"]
    if len(synopsis) > 1500:
        synopsis = synopsis[:1500] + "..."
    embed = discord.Embed(
        title=anime["title"], description=synopsis, url=anime["url"], color=color
    )
    if "image_url" in anime.keys() and anime["image_url"]:
        embed.set_image(url=anime["image_url"])
    if len(init_fields) > 0:
        for field in init_fields:
            embed.add_field(name=field[0], value=field[1], inline=field[2])
    embed.add_field(name="Type", value=anime["type"])
    embed.add_field(name="Episodes", value=f"{anime['episodes']} ({anime['duration']})")
    embed.add_field(name="Status", value=anime["status"])
    embed.add_field(name="Aired", value=anime["aired"]["string"])
    embed.add_field(name="Rank", value=anime["rank"])
    if anime["broadcast"]:
        embed.add_field(name="Broadcast", value=anime["broadcast"])
    if anime["premiered"]:
        embed.add_field(name="Premiered", value=anime["premiered"])
    embed.add_field(
        name="Score", value=f"{anime['score']} by {anime['scored_by']} members"
    )
    embed.add_field(name="Rating", value=anime["rating"], inline=True)
    genres = ", ".join([g["name"] for g in anime["genres"]])
    embed.add_field(name="Genres", value=genres, inline=True)
    if "Adaptation" in anime["related"].keys():
        adaptations = ", ".join(
            [f"{i['name']} ({i['type']})" for i in anime["related"]["Adaptation"]]
        )
        embed.add_field(name="Adaptations", value=adaptations, inline=True)
    if "Prequel" in anime["related"].keys():
        prequels = ", ".join(
            [f"{i['name']} ({i['type']})" for i in anime["related"]["Prequel"]]
        )
        embed.add_field(name="Prequels", value=prequels, inline=True)
    if "Sequel" in anime["related"].keys():
        sequels = ", ".join(
            [f"{i['name']} ({i['type']})" for i in anime["related"]["Sequel"]]
        )
        embed.add_field(name="Sequels", value=sequels, inline=True)
    if len(anime["opening_themes"]) > 0:
        embed.add_field(
            name="Opening Theme Song",
            value="\n".join(
                [f"{i+1}. {j}" for i, j in enumerate(anime["opening_themes"])]
            ),
            inline=True,
        )
    if len(anime["ending_themes"]) > 0:
        embed.add_field(
            name="Ending Theme Song",
            value="\n".join(
                [f"{i+1}. {j}" for i, j in enumerate(anime["ending_themes"])]
            ),
            inline=True,
        )
    embed.set_footer(text="Taken from MyAnimeList.net")
    return embed


async def anime(client, message, *args):
    if len(args) == 0:
        await message.channel.send(f"Usage: {PREFIX}anime <anime name>")
        return
    search_str = " ".join(args)
    if len(search_str) < 3:
        await message.channel.send("Anime name must be atleast 3 letters.")
        return
    jikan = AioJikan()
    _search_result = await jikan.search(search_type="anime", query=search_str)
    search_result = _search_result["results"][0]["mal_id"]
    embed = await make_anime_embed(client.loop, search_result, message.author.color)
    await message.channel.send(embed=embed)


async def manga(client, message, *args):
    if len(args) == 0:
        await message.channel.send(f"Usage: {PREFIX}manga <manga name>")
        return
    search_str = " ".join(args)
    if len(search_str) < 3:
        await message.channel.send("Manga name must be atleast 3 letters.")
        return
    jikan = AioJikan()
    _search_result = await jikan.search(search_type="manga", query=search_str)
    search_result = _search_result["results"][0]["mal_id"]
    manga = await jikan.manga(search_result)
    synopsis = manga["synopsis"]
    if len(synopsis) > 1500:
        synopsis = synopsis[:1500] + "..."
    embed = discord.Embed(
        title=manga["title"],
        description=synopsis,
        url=manga["url"],
        color=message.author.colour,
    )
    if "image_url" in manga.keys() and manga["image_url"]:
        embed.set_image(url=manga["image_url"])
    embed.add_field(name="Type", value=manga["type"])
    embed.add_field(
        name="Chapters", value=f"{manga['chapters']} ({manga['volumes']} volumes)"
    )
    embed.add_field(name="Status", value=manga["status"])
    embed.add_field(name="Published", value=manga["published"]["string"])
    embed.add_field(name="Rank", value=manga["rank"])
    embed.add_field(
        name="Score", value=f"{manga['score']} by {manga['scored_by']} members"
    )
    genres = ", ".join([g["name"] for g in manga["genres"]])
    embed.add_field(name="Genres", value=genres, inline=True)
    if "Adaptation" in manga["related"].keys():
        adaptations = ", ".join(
            [f"{i['name']} ({i['type']})" for i in manga["related"]["Adaptation"]]
        )
        embed.add_field(name="Adaptations", value=adaptations, inline=True)
    embed.set_footer(text="Taken from MyMangaList.net")
    await message.channel.send(embed=embed)


async def animelist(client, message, *args):
    if len(args) == 0:
        await message.channel.send(f"Usage: {PREFIX}animelist <MAL User>")
        return
    search_str = " ".join(args)
    try:
        jikan = AioJikan()
        raw_animelist = await jikan.user(username=search_str, request="animelist")
    except APIException:
        await message.channel.send("Username not found on MAL, or account is private.")
        return
    animelist = raw_animelist["anime"]
    sentences = []
    for i, anime in enumerate(animelist):
        watching_status = anime["watching_status"]
        if watching_status == 1:
            status = f"Currently Watching ({anime['watched_episodes']}/{anime['total_episodes']} eps)"
        elif watching_status == 2:
            status = (
                f"Completed ({anime['watched_episodes']}/{anime['total_episodes']} eps)"
            )
        elif watching_status == 3:
            status = (
                f"On Hold ({anime['watched_episodes']}/{anime['total_episodes']} eps)"
            )
        elif watching_status == 4:
            status = (
                f"Dropped ({anime['watched_episodes']}/{anime['total_episodes']} eps)"
            )
        elif watching_status == 6:
            status = "Plan To Watch"
        sentences.append(
            "{0}. **__[{1}]({2})__** ({3}). Status: **{4}**. Score: **{5}**.".format(
                i + 1,
                anime["title"],
                anime["url"].replace("_", r"\_"),
                anime["type"],
                status,
                anime["score"],
            )
        )
    pages = list(chunks(sentences, 15))
    page_num = 1
    total_pages = len(pages)
    embed = discord.Embed(
        title=f"{search_str}'s AnimeList",
        color=message.author.colour,
        description="\n".join(pages[page_num - 1]),
    )
    embed.add_field(name="Total Anime", value=len(animelist))
    embed.set_footer(text=f"Page: {page_num}/{total_pages}")
    msg = await message.channel.send(embed=embed)
    if total_pages == 1:
        return
    await msg.add_reaction("⬅")
    await msg.add_reaction("➡")
    try:
        while True:

            def check(reaction, user):
                emoji = str(reaction.emoji)
                return not user.bot and (emoji == "⬅" or emoji == "➡")

            reaction, _ = await client.wait_for(
                "reaction_add", timeout=300, check=check
            )
            emoji = str(reaction.emoji)
            if emoji == "⬅":
                if not page_num - 1 > 0:
                    continue
                page_num -= 1
                embed.description = "\n".join(pages[page_num - 1])
            elif emoji == "➡":
                if not page_num + 1 <= total_pages:
                    continue
                page_num += 1
                embed.description = "\n".join(pages[page_num - 1])
            else:
                continue
            embed.set_footer(text=f"Page: {page_num}/{total_pages}")
            await msg.edit(embed=embed)
    except asyncio.TimeoutError:
        pass  # Ignore.


async def mangalist(client, message, *args):
    if len(args) == 0:
        await message.channel.send(f"Usage: {PREFIX}mangalist <MAL User>")
        return
    search_str = " ".join(args)
    try:
        jikan = AioJikan()
        raw_mangalist = await jikan.user(username=search_str, request="mangalist")
    except APIException:
        await message.channel.send("Username not found on MAL, or account is private.")
        return
    mangalist = raw_mangalist["manga"]
    sentences = []
    for i, manga in enumerate(mangalist):
        reading_status = manga["reading_status"]
        if reading_status == 1:
            status = f"Currently Reading ({manga['read_chapters']}/{manga['total_chapters']} chaps)"
        elif reading_status == 2:
            status = (
                f"Completed ({manga['read_chapters']}/{manga['total_chapters']} chaps)"
            )
        elif reading_status == 3:
            status = (
                f"On Hold ({manga['read_chapters']}/{manga['total_chapters']} chaps)"
            )
        elif reading_status == 4:
            status = (
                f"Dropped ({manga['read_chapters']}/{manga['total_chapters']} chaps)"
            )
        elif reading_status == 6:
            status = "Plan To Read"
        sentences.append(
            "{0}. **__[{1}]({2})__**. Status: **{3}**. Score: **{4}**.".format(
                i + 1,
                manga["title"],
                manga["url"].replace("_", r"\_"),
                status,
                manga["score"],
            )
        )
    pages = list(chunks(sentences, 15))
    page_num = 1
    total_pages = len(pages)
    embed = discord.Embed(
        title=f"{search_str}'s MangaList",
        color=message.author.colour,
        description="\n".join(pages[page_num - 1]),
    )
    embed.add_field(name="Total Manga", value=len(mangalist))
    embed.set_footer(text=f"Page: {page_num}/{total_pages}")
    msg = await message.channel.send(embed=embed)
    if total_pages == 1:
        return
    await msg.add_reaction("⬅")
    await msg.add_reaction("➡")
    try:
        while True:

            def check(reaction, user):
                emoji = str(reaction.emoji)
                return not user.bot and (emoji == "⬅" or emoji == "➡")

            reaction, _ = await client.wait_for(
                "reaction_add", timeout=300, check=check
            )
            emoji = str(reaction.emoji)
            if emoji == "⬅":
                if not page_num - 1 > 0:
                    continue
                page_num -= 1
                embed.description = "\n".join(pages[page_num - 1])
            elif emoji == "➡":
                if not page_num + 1 <= total_pages:
                    continue
                page_num += 1
                embed.description = "\n".join(pages[page_num - 1])
            else:
                continue
            embed.set_footer(text=f"Page: {page_num}/{total_pages}")
            await msg.edit(embed=embed)
    except asyncio.TimeoutError:
        pass  # Ignore.


async def profile(client, message, *args):
    if len(args) == 0:
        await message.channel.send(f"Usage: {PREFIX}profile <MAL User>")
        return
    search_str = " ".join(args)
    try:
        jikan = AioJikan()
        profile = await jikan.user(username=search_str, request="profile")
    except APIException:
        await message.channel.send("Username not found on MAL, or account is private.")
        return
    embed = discord.Embed(
        title="{0}'s MAL Profile".format(search_str),
        url=profile["url"],
        color=message.author.colour,
    )
    if profile["image_url"]:
        embed.set_thumbnail(url=profile["image_url"])
    if profile["gender"]:
        embed.add_field(name="Gender", value=profile["gender"])
    if profile["birthday"]:
        birthday = datetime.datetime.fromisoformat(profile["birthday"]).strftime(
            "%A, %d %B, %Y"
        )
        embed.add_field(name="Birthday", value=birthday)
    if profile["location"]:
        embed.add_field(name="Location", value=profile["location"])
    if profile["joined"]:
        joined = datetime.datetime.fromisoformat(profile["joined"]).strftime(
            "%A, %d %B, %Y"
        )
        embed.add_field(name="Joined MAL", value=joined)
    astats = profile["anime_stats"]
    anime_stats = f"""
Days of anime watched: {astats['days_watched']}
Mean score: {astats['mean_score']}
Watching: {astats['watching']}
Completed: {astats['completed']}
On Hold: {astats['on_hold']}
Dropped: {astats['dropped']}
Plan to Watch: {astats['plan_to_watch']}
Rewatched: {astats['rewatched']}
Episodes Watched: {astats['episodes_watched']}
Total: {astats['total_entries']}
    """
    mstats = profile["manga_stats"]
    manga_stats = f"""
Days of manga read: {mstats['days_read']}
Mean score: {mstats['mean_score']}
Reading: {mstats['reading']}
Completed: {mstats['completed']}
On Hold: {mstats['on_hold']}
Dropped: {mstats['dropped']}
Plan to Read: {mstats['plan_to_read']}
Reread: {mstats['reread']}
Chapters Read: {mstats['chapters_read']}
Volumes Read: {mstats['volumes_read']}
Total: {mstats['total_entries']}
    """
    embed.add_field(name="Anime Stats", value=anime_stats, inline=False)
    embed.add_field(name="Manga Stats", value=manga_stats, inline=False)
    if profile["favorites"]["anime"]:
        afavs = profile["favorites"]["anime"]
        anime_favorites = ", ".join(
            [
                "[{0}]({1})".format(
                    i["name"].replace(",", ""), i["url"].replace("_", r"\_")
                )
                for i in afavs
            ]
        )
    else:
        anime_favorites = "No anime favorites set."
    if profile["favorites"]["manga"]:
        mfavs = profile["favorites"]["manga"]
        manga_favorites = ", ".join(
            [
                "[{0}]({1})".format(
                    i["name"].replace(",", ""), i["url"].replace("_", r"\_")
                )
                for i in mfavs
            ]
        )
    else:
        manga_favorites = "No manga favorites set."
    if profile["favorites"]["characters"]:
        cfavs = profile["favorites"]["characters"]
        favorite_chars = ", ".join(
            [
                "[{0}]({1})".format(
                    i["name"].replace(",", ""), i["url"].replace("_", r"\_")
                )
                for i in cfavs
            ]
        )
    else:
        favorite_chars = "No favorite characters set."
    embed.add_field(name="Anime Favorites", value=anime_favorites, inline=False)
    embed.add_field(name="Manga Favorites", value=manga_favorites, inline=False)
    embed.add_field(name="Favorite Characters", value=favorite_chars, inline=False)
    about = profile["about"]
    if about:
        if len(about) > 500:
            about = about[:500] + "..."
        embed.add_field(name="About Them", value=about)
    await message.channel.send(embed=embed)


async def nyaa_search(client, message, *args):
    if len(args) == 0:
        await message.channel.send("Usage: {}nyaa <search term>".format(PREFIX))
        return
    search_term = " ".join(args)
    wait_msg = await message.channel.send("Fetching data, please wait...")
    search_results = Nyaa.search(keyword=search_term)
    if len(search_results) == 0:
        await message.channel.send("Nothing found.")
        await wait_msg.delete()
        return
    embed = discord.Embed(title="Nyaa.Si Results", colour=message.author.colour)
    fields = 1
    for result in search_results:
        if fields > 10:
            break
        short_url = await short(result["url"])
        download_url = await short(result["download_url"])
        field_txt = "{0}\n**Size:** {1} **Date:** {2}\n{3} :arrow_up: {4} :arrow_down:\n[Link]({5}) [Torrent File]({6})\n".format(  # noqa
            result["category"],
            result["size"],
            result["date"],
            result["seeders"],
            result["leechers"],
            short_url,
            download_url,
        )
        embed.add_field(name=result["name"], value=field_txt, inline=False)
        fields += 1
    await message.channel.send(embed=embed)
    await wait_msg.delete()


async def which_anime(client, message, *args):
    await message.channel.send(
        """
Let's find out which anime that scene is from!
This is using https://trace.moe, kudos to the creator.
**Please follow this: https://trace.moe/faq. You will get to know what kind of images to send.**
Send a picture (PNG/JPG/GIF only):
        """
    )
    try:

        def check(m):
            return (
                m.channel == message.channel
                and m.author == message.author
                and (len(m.attachments) != 0 or m.content == "exit")
            )

        msg = await client.wait_for("message", check=check, timeout=60)
        if msg.content == "exit":
            await message.channel.send("Okay, exiting...")
            return
        img_attachment = msg.attachments[0]
        img_bio = BytesIO()
        await img_attachment.save(img_bio)
    except asyncio.TimeoutError:
        await message.channel.send("Error: Timeout.")
        return
    img = Image.open(img_bio, "r")
    img.thumbnail((320, 240), Image.ANTIALIAS)
    img = img.convert("RGB")
    out_io = BytesIO()
    img.save(out_io, "JPEG")
    out_io.seek(0)
    b64_data = b64encode(out_io.getvalue()).decode()
    data = "data:image/jpeg;base64,{}".format(b64_data)
    async with aiohttp.ClientSession() as sess:
        async with sess.post(
            f"https://trace.moe/api/search?token={TRACE_MOE_TOKEN}",
            json={"image": data},
        ) as resp:
            if resp.status == 429:
                await message.channel.send(
                    "Too many people using this command <:Eww:575373991640956938> Please wait till quota is cleared."
                )  # noqa
                return
            assert resp.status == 200
            txt = await resp.text()
            try:
                result = json.loads(txt)["docs"]
            except (json.decoder.JSONDecodeError, KeyError, AssertionError):
                await message.channel.send(
                    "Something is wrong <:Eww:575373991640956938> . Contact developer."
                )
                return
    if len(result) == 0:
        await message.channel.send("No results found. Gommenasai.")
        return
    result = result[0]
    _st = int(result["from"])
    st_min = _st // 60
    st_sec = int(_st - st_min * 60)
    _et = int(result["to"])
    et_min = _et // 60
    et_sec = int(_et - et_min * 60)
    fields = [
        ("Match Similarity", f"{float(result['similarity'])*100:.2f}%", True),
        ("Episode", result["episode"], True),
        (
            "Scene Appears Between",
            f"{st_min:>02d}:{st_sec:>02d} to {et_min:>02d}:{et_sec:>02d}",
            True,
        ),
        ("Is Hentai", str(result["is_adult"]).capitalize(), True),
    ]
    if result["mal_id"]:
        embed = await make_anime_embed(
            client.loop,
            result["mal_id"],
            color=message.author.color,
            init_fields=fields,
        )
    else:
        embed = discord.Embed(title=result["title_romaji"], color=message.author.color)
        for field in fields:
            embed.add_field(name=field[0], value=field[1], inline=field[2])
    await message.channel.send(embed=embed)


async def short(url):
    async with aiohttp.ClientSession() as sess:
        async with sess.get("https://tinyurl.com/api-create.php?url=" + url) as resp:
            txt = await resp.text()
            return txt


anime_functions = {
    "anime": (anime, "`{P}anime <anime name>`: Get details about an anime."),
    "manga": (manga, "`{P}manga <manga name>`: Get details about a manga."),
    "animelist": (
        animelist,
        "`{P}animelist <MAL Username>`: Get someone's MAL animelist.",
    ),
    "mangalist": (
        mangalist,
        "`{P}mangalist <MAL Username>`: Get someone's MAL mangalist.",
    ),
    "profile": (profile, "`{P}profile <MAL Username>`: Get someone's MAL profile."),
    "nyaa": (
        nyaa_search,
        "`{P}nyaa <search string>`: Get anime torrents from nyaa.si.",
    ),
    "whichanime": (
        which_anime,
        "`{P}whichanime`: Get an anime from a scene picture. Using trace.moe.",
    ),  # noqa
}
