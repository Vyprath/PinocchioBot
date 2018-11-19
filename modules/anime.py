from variables import PREFIX
from jikanpy import AioJikan
from jikanpy.exceptions import APIException
import asyncio
import discord
import datetime


jikan = AioJikan(loop=asyncio.get_event_loop())


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
    anime = await jikan.anime(search_result)
    embed = discord.Embed(title=anime['title'], url=anime['url'], color=message.author.colour)
    if 'image_url' in anime.keys() and anime['image_url']:
        embed.set_thumbnail(url=anime['image_url'])
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


def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i+n]


anime_functions = {
    'anime': (anime, "Get details for an anime."),
    'manga': (manga, "Get details for an manga."),
    'animelist': (animelist, "Get the MAL animelist for an user."),
    'mangalist': (mangalist, "Get the MAL mangalist for an user."),
    'profile': (profile, "Get profile for an user.")
}
