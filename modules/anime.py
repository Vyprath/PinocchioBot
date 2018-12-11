from variables import PREFIX, TINYURL, TRACE_MOE_URL
from jikanpy import AioJikan
from jikanpy.exceptions import APIException
from NyaaPy import Nyaa
from io import BytesIO
from PIL import Image
from base64 import b64encode
import asyncio
import discord
import datetime
import aiohttp
import json

jikan = AioJikan(loop=asyncio.get_event_loop())


async def _anime_embed(mal_id, color=0x00000000, init_fields=[]):
    anime = await jikan.anime(mal_id)
    embed = discord.Embed(title=anime['title'], url=anime['url'], color=color)
    if 'image_url' in anime.keys() and anime['image_url']:
        embed.set_thumbnail(url=anime['image_url'])
    if len(init_fields) > 0:
        for field in init_fields:
            embed.add_field(name=field[0], value=field[1], inline=field[2])
    embed.add_field(name="Type", value=anime['type'])
    embed.add_field(name="Episodes", value="{0} ({1})".format(anime['episodes'], anime['duration']))
    embed.add_field(name="Status", value=anime['status'])
    embed.add_field(name="Aired", value=anime['aired']['string'])
    embed.add_field(name="Rank", value=anime['rank'])
    if anime['broadcast']:
        embed.add_field(name="Broadcast", value=anime['broadcast'])
    if anime['premiered']:
        embed.add_field(name="Premiered", value=anime['premiered'])
    embed.add_field(
        name="Score", value='{0} by {1} members'.format(anime['score'], anime['scored_by']))
    embed.add_field(name="Rating", value=anime['rating'], inline=False)
    genres = ", ".join([g['name'] for g in anime['genres']])
    embed.add_field(name="Genres", value=genres, inline=False)
    if 'Adaptation' in anime['related'].keys():
        adaptations = ", ".join(["{0} ({1})".format(
            i['name'], i['type']) for i in anime['related']['Adaptation']])
        embed.add_field(name="Adaptations", value=adaptations, inline=False)
    if 'Prequel' in anime['related'].keys():
        prequels = ", ".join(["{0} ({1})".format(
            i['name'], i['type']) for i in anime['related']['Prequel']])
        embed.add_field(name="Prequels", value=prequels, inline=False)
    if 'Sequel' in anime['related'].keys():
        sequels = ", ".join(["{0} ({1})".format(
            i['name'], i['type']) for i in anime['related']['Sequel']])
        embed.add_field(name="Sequels", value=sequels, inline=False)
    synopsis = anime['synopsis']
    if len(synopsis) > 840:
        synopsis = synopsis[:700] + "..."
    embed.add_field(name="Synopsis", value=synopsis, inline=False)
    if len(anime['opening_themes']) > 0:
        embed.add_field(
            name="Opening Theme Song", value=", ".join(anime['opening_themes']), inline=False)
    if len(anime['ending_themes']) > 0:
        embed.add_field(
            name="Ending Theme Song", value=", ".join(anime['ending_themes']), inline=False)
    embed.set_footer(text="Taken from MyAnimeList.net")
    return embed


async def anime(client, message, *args):
    if len(args) == 0:
        await message.channel.send("Usage: {0}anime <anime name>".format(PREFIX))
        return
    search_str = ' '.join(args)
    if len(search_str) < 3:
        await message.channel.send("Anime name must be atleast 3 letters.")
        return
    _search_result = await jikan.search(search_type='anime', query=search_str)
    search_result = _search_result['results'][0]['mal_id']
    embed = _anime_embed(search_result, message.author.color)
    await message.channel.send(embed=embed)


async def manga(client, message, *args):
    if len(args) == 0:
        await message.channel.send("Usage: {0}manga <manga name>".format(PREFIX))
        return
    search_str = ' '.join(args)
    if len(search_str) < 3:
        await message.channel.send("Manga name must be atleast 3 letters.")
        return
    _search_result = await jikan.search(search_type='manga', query=search_str)
    search_result = _search_result['results'][0]['mal_id']
    manga = await jikan.manga(search_result)
    embed = discord.Embed(title=manga['title'], url=manga['url'], color=message.author.colour)
    if 'image_url' in manga.keys() and manga['image_url']:
        embed.set_thumbnail(url=manga['image_url'])
    embed.add_field(name="Type", value=manga['type'])
    embed.add_field(
        name="Chapters", value="{0} ({1} volumes)".format(manga['chapters'], manga['volumes']))
    embed.add_field(name="Status", value=manga['status'])
    embed.add_field(name="Published", value=manga['published']['string'])
    embed.add_field(name="Rank", value=manga['rank'])
    embed.add_field(
        name="Score", value='{0} by {1} members'.format(manga['score'], manga['scored_by']))
    genres = ", ".join([g['name'] for g in manga['genres']])
    embed.add_field(name="Genres", value=genres, inline=False)
    if 'Adaptation' in manga['related'].keys():
        adaptations = ", ".join(["{0} ({1})".format(
            i['name'], i['type']) for i in manga['related']['Adaptation']])
        embed.add_field(name="Adaptations", value=adaptations, inline=False)
    synopsis = manga['synopsis']
    if len(synopsis) > 840:
        synopsis = synopsis[:840] + "..."
    embed.add_field(name="Synopsis", value=synopsis, inline=False)
    embed.set_footer(text="Taken from MyMangaList.net")
    await message.channel.send(embed=embed)


async def animelist(client, message, *args):
    if len(args) == 0:
        await message.channel.send("Usage: {0}animelist <MAL User>".format(PREFIX))
        return
    search_str = ' '.join(args)
    try:
        raw_animelist = await jikan.user(username=search_str, request='animelist')
    except APIException:
        await message.channel.send("Username not found on MAL, or account is private.")
        return
    animelist = raw_animelist['anime']
    sentences = []
    for i, anime in enumerate(animelist):
        watching_status = anime['watching_status']
        if watching_status == 1:
            status = 'Currently Watching ({0}/{1} eps)'.format(
                anime['watched_episodes'], anime['total_episodes'])
        elif watching_status == 2:
            status = 'Completed ({0}/{1} eps)'.format(
                anime['watched_episodes'], anime['total_episodes'])
        elif watching_status == 3:
            status = 'On Hold ({0}/{1} eps)'.format(
                anime['watched_episodes'], anime['total_episodes'])
        elif watching_status == 4:
            status = 'Dropped ({0}/{1} eps)'.format(
                anime['watched_episodes'], anime['total_episodes'])
        elif watching_status == 6:
            status = 'Plan To Watch'
        sentences.append(
            "{0}. **__[{1}]({2})__** ({3}). Status: **{4}**. Score: **{5}**.".format(
                i+1, anime['title'], anime['url'].replace("_", "\_"),
                anime['type'], status, anime['score']
            ))
    pages = list(chunks(sentences, 5))
    page_num = 1
    total_pages = len(pages)
    embed = discord.Embed(title="{0}'s AnimeList".format(search_str), color=message.author.colour)
    embed.add_field(name="Total Anime", value=len(animelist))
    embed.add_field(name="List", value='\n'.join(pages[page_num - 1]), inline=False)
    embed.set_footer(text="Page: {0}/{1}".format(page_num, total_pages))
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
            reaction, _ = await client.wait_for('reaction_add', timeout=300, check=check)
            emoji = str(reaction.emoji)
            if emoji == "⬅":
                if not page_num - 1 > 0:
                    continue
                page_num -= 1
                embed.set_field_at(
                    index=1, name="List",
                    value='\n'.join(pages[page_num - 1]), inline=False)
            elif emoji == "➡":
                if not page_num + 1 <= total_pages:
                    continue
                page_num += 1
                embed.set_field_at(
                    index=1, name="List",
                    value='\n'.join(pages[page_num - 1]), inline=False)
            else:
                continue
            embed.set_footer(text="Page: {0}/{1}".format(page_num, total_pages))
            await msg.edit(embed=embed)
    except asyncio.TimeoutError:
        pass  # Ignore.


async def mangalist(client, message, *args):
    if len(args) == 0:
        await message.channel.send("Usage: {0}mangalist <MAL User>".format(PREFIX))
        return
    search_str = ' '.join(args)
    try:
        raw_mangalist = await jikan.user(username=search_str, request='mangalist')
    except APIException:
        await message.channel.send("Username not found on MAL, or account is private.")
        return
    mangalist = raw_mangalist['manga']
    sentences = []
    for i, manga in enumerate(mangalist):
        reading_status = manga['reading_status']
        if reading_status == 1:
            status = 'Currently Reading ({0}/{1} chaps)'.format(
                manga['read_chapters'], manga['total_chapters'])
        elif reading_status == 2:
            status = 'Completed ({0}/{1} chaps)'.format(
                manga['read_chapters'], manga['total_chapters'])
        elif reading_status == 3:
            status = 'On Hold ({0}/{1} chaps)'.format(
                manga['read_chapters'], manga['total_chapters'])
        elif reading_status == 4:
            status = 'Dropped ({0}/{1} chaps)'.format(
                manga['read_chapters'], manga['total_chapters'])
        elif reading_status == 6:
            status = 'Plan To Read'
        sentences.append(
            "{0}. **__[{1}]({2})__**. Status: **{3}**. Score: **{4}**.".format(
                i+1, manga['title'], manga['url'].replace("_", "\_"), status, manga['score']
            ))
    pages = list(chunks(sentences, 5))
    page_num = 1
    total_pages = len(pages)
    embed = discord.Embed(title="{0}'s MangaList".format(search_str), color=message.author.colour)
    embed.add_field(name="Total Manga", value=len(mangalist))
    embed.add_field(name="List", value='\n'.join(pages[page_num - 1]), inline=False)
    embed.set_footer(text="Page: {0}/{1}".format(page_num, total_pages))
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
            reaction, _ = await client.wait_for('reaction_add', timeout=300, check=check)
            emoji = str(reaction.emoji)
            if emoji == "⬅":
                if not page_num - 1 > 0:
                    continue
                page_num -= 1
                embed.set_field_at(
                    index=1, name="List",
                    value='\n'.join(pages[page_num - 1]), inline=False)
            elif emoji == "➡":
                if not page_num + 1 <= total_pages:
                    continue
                page_num += 1
                embed.set_field_at(
                    index=1, name="List",
                    value='\n'.join(pages[page_num - 1]), inline=False)
            else:
                continue
            embed.set_footer(text="Page: {0}/{1}".format(page_num, total_pages))
            await msg.edit(embed=embed)
    except asyncio.TimeoutError:
        pass  # Ignore.


async def profile(client, message, *args):
    if len(args) == 0:
        await message.channel.send("Usage: {0}profile <MAL User>".format(PREFIX))
        return
    search_str = ' '.join(args)
    try:
        profile = await jikan.user(username=search_str, request='profile')
    except APIException:
        await message.channel.send("Username not found on MAL, or account is private.")
        return
    embed = discord.Embed(
        title="{0}'s MAL Profile".format(search_str),
        url=profile['url'],
        color=message.author.colour)
    if profile['image_url']:
        embed.set_thumbnail(url=profile['image_url'])
    if profile['gender']:
        embed.add_field(name="Gender", value=profile['gender'])
    if profile['birthday']:
        birthday = datetime.datetime.fromisoformat(
            profile['birthday']).strftime("%A, %d %B, %Y")
        embed.add_field(name="Birthday", value=birthday)
    if profile['location']:
        embed.add_field(name="Location", value=profile['location'])
    if profile['joined']:
        joined = datetime.datetime.fromisoformat(
            profile['joined']).strftime("%A, %d %B, %Y")
        embed.add_field(name="Joined MAL", value=joined)
    astats = profile['anime_stats']
    anime_stats = """
Days of anime watched: {0}
Mean score: {1}
Watching: {2}
Completed: {3}
On Hold: {4}
Dropped: {5}
Plan to Watch: {6}
Rewatched: {7}
Episodes Watched: {8}
Total: {9}
    """.format(
        astats['days_watched'], astats['mean_score'], astats['watching'],
        astats['completed'], astats['on_hold'], astats['dropped'], astats['plan_to_watch'],
        astats['rewatched'], astats['episodes_watched'], astats['total_entries'],
    )
    mstats = profile['manga_stats']
    manga_stats = """
Days of manga read: {0}
Mean score: {1}
Reading: {2}
Completed: {3}
On Hold: {4}
Dropped: {5}
Plan to Read: {6}
Reread: {7}
Chapters Read: {8}
Volumes Read: {9}
Total: {10}
    """.format(
        mstats['days_read'], mstats['mean_score'], mstats['reading'],
        mstats['completed'], mstats['on_hold'], mstats['dropped'], mstats['plan_to_read'],
        mstats['reread'], mstats['chapters_read'], mstats['volumes_read'], mstats['total_entries'],
    )
    embed.add_field(name="Anime Stats", value=anime_stats, inline=False)
    embed.add_field(name="Manga Stats", value=manga_stats, inline=False)
    if profile['favorites']['anime']:
        afavs = profile['favorites']['anime']
        anime_favorites = ", ".join([
            "[{0}]({1})".format(
                i['name'].replace(",", ""), i['url'].replace("_", "\_"))
            for i in afavs])
    else:
        anime_favorites = "No anime favorites set."
    if profile['favorites']['manga']:
        mfavs = profile['favorites']['manga']
        manga_favorites = ", ".join([
            "[{0}]({1})".format(
                i['name'].replace(",", ""), i['url'].replace("_", "\_"))
            for i in mfavs])
    else:
        manga_favorites = "No manga favorites set."
    if profile['favorites']['characters']:
        cfavs = profile['favorites']['characters']
        favorite_chars = ", ".join([
            "[{0}]({1})".format(
                i['name'].replace(",", ""), i['url'].replace("_", "\_"))
            for i in cfavs])
    else:
        favorite_chars = "No favorite characters set."
    embed.add_field(name="Anime Favorites", value=anime_favorites, inline=False)
    embed.add_field(name="Manga Favorites", value=manga_favorites, inline=False)
    embed.add_field(name="Favorite Characters", value=favorite_chars, inline=False)
    about = profile['about']
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
    for i, result in enumerate(search_results):
        if fields > 10:
            break
        short_url = await short(result['url'])
        download_url = await short(result['download_url'])
        field_txt = "{0}\n**Size:** {1} **Date:** {2}\n{3} :arrow_up: {4} :arrow_down:\n[Link]({5}) [Torrent File]({6})\n".format(  # noqa
            result['category'], result['size'], result['date'],
            result['seeders'], result['leechers'], short_url, download_url
        )
        embed.add_field(name=result['name'], value=field_txt, inline=False)
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
        """)
    try:
        def check(m):
            return len(m.attachments) != 0 or m.content == 'exit'
        msg = await client.wait_for('message', check=check, timeout=60)
        if msg.content == 'exit':
            await message.channel.send("Okay, exiting...")
            return
        img_attachment = msg.attachments[0]
        img_bio = BytesIO()
        await img_attachment.save(img_bio)
    except asyncio.TimeoutError:
        await message.channel.send('Error: Timeout.')
        return
    img = Image.open(img_bio, 'r')
    img.thumbnail((320, 240), Image.ANTIALIAS)
    img = img.convert('RGB')
    out_io = BytesIO()
    img.save(out_io, 'JPEG')
    out_io.seek(0)
    b64_data = b64encode(out_io.getvalue()).decode()
    data = "data:image/jpeg;base64,{}".format(b64_data)
    async with aiohttp.ClientSession() as sess:
        async with sess.post(TRACE_MOE_URL, json={'image': data}) as resp:
            if resp.status == 429:
                await message.channel.send("Too many people using this command >.< Please wait till quota is cleared.")  # noqa
                return
            assert resp.status == 200
            txt = await resp.text()
            try:
                result = json.loads(txt)['docs']
            except (json.decoder.JSONDecodeError, KeyError, AssertionError):
                await message.channel.send("Something is wrong >.< . Contact developer.")
                return
    if len(result) == 0:
        await message.channel.send("No results found. Gommenasai.")
        return
    result = result[0]
    _st = int(result['from'])
    st_min = _st//60
    st_sec = int(_st-st_min*60)
    _et = int(result['to'])
    et_min = _et//60
    et_sec = int(_et-et_min*60)
    fields = [
        ("Match Similarity", "{0:.2f}%".format(float(result['similarity'])*100), True),
        ("Episode", result['episode'], True),
        ("Scene Appears Between",
         "{0:>02d}:{1:>02d} to {2:>02d}:{3:>02d}".format(st_min, st_sec, et_min, et_sec),
         True),
        ("Is Hentai", str(result['is_adult']).capitalize(), True)
    ]
    if result['mal_id']:
        embed = await _anime_embed(result['mal_id'], color=message.author.color, init_fields=fields)
    else:
        embed = discord.Embed(title=result['title_romaji'], color=message.author.color)
        for field in fields:
            embed.add_field(name=field[0], value=field[1], inline=field[2])
    await message.channel.send(embed=embed)


def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i+n]


async def short(url):
    async with aiohttp.ClientSession() as sess:
        async with sess.get(TINYURL + url) as resp:
            txt = await resp.text()
            return txt


anime_functions = {
    'anime': (anime, "Get details for an anime."),
    'manga': (manga, "Get details for an manga."),
    'animelist': (animelist, "Get the MAL animelist for an user."),
    'mangalist': (mangalist, "Get the MAL mangalist for an user."),
    'profile': (profile, "Get profile for an user."),
    'nyaa': (nyaa_search, "Get anime torrents from nyaa.si"),
    'whichanime': (which_anime, "Which Anime Is This? Get information about an anime scene. (trace.moe)")  # noqa
}
