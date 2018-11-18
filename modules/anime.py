from variables import PREFIX
from jikanpy import AioJikan
import asyncio
import discord


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
    embed = discord.Embed(title=anime['title'], url=anime['url'], color=0x2da8b6)
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
    embed = discord.Embed(title=manga['title'], url=manga['url'], color=0x2da8b6)
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


anime_functions = {
    'anime': (anime, "Get details for an anime"),
    'manga': (manga, "Get details for an manga"),
}
