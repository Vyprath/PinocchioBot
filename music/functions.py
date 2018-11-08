from .utils import MusicInfo, GuildState
import discord
import asyncio


summoners = {}
guild_states = {}


def get_guild_state(guild):
    if guild.id in guild_states:
        return guild_states[guild.id]
    else:
        guild_state = GuildState()
        guild_states.update({guild.id: guild_state})
        return guild_state


async def ensure_in_voice_channel(message):
    voice_state = message.author.voice
    voice_client = message.guild.voice_client
    if voice_state is None or voice_state.channel is None:
        await message.channel.send("Please join a voice channel first.")
        return None
    if voice_client is None:
        voice_client = await voice_state.channel.connect()
        summoners.update({hash(voice_client): message.author})
        return voice_client
    elif voice_client.channel == voice_state.channel:
        return voice_client
    else:
        await message.channel.send("""
Bot is already connected to a voice channel.
Make the bot leave previous voice channel with `!leave`. Requires **administrator** permission.
Or ask {} to leave the previous voice channel.
""".format(summoners[hash(voice_client)].name))
        return None


async def _play_music(message, voice_client, guild_state):
    if len(guild_state.playlist) == 0:
        await voice_client.disconnect()
    music = guild_state.playlist.pop(0)
    guild_state.now_playing = music
    source = discord.PCMVolumeTransformer(
        discord.FFmpegPCMAudio(music.stream_url), volume=guild_state.volume)

    def after_finished(err):
        asyncio.run_coroutine_threadsafe(
            _play_music(message, voice_client, guild_state),
            voice_client.loop)

    voice_client.play(source, after=after_finished)
    embed = music.get_embed()
    embed.remove_field(1)
    await message.channel.send("Now Playing", embed=embed)


async def play(client, message, *args):
    voice_client = await ensure_in_voice_channel(message)
    guild_state = get_guild_state(message.guild)
    duration = 0
    if guild_state.now_playing is not None:
        duration += guild_state.now_playing.duration
    if len(guild_state.playlist) > 0:
        for i in guild_state.playlist:
            duration += i.duration
    if not voice_client:
        return
    if len(args) == 0:
        await message.channel.send(
            "Usage: `!play <url/search string>`. YouTube recommended."
        )
        return
    try:
        info = MusicInfo(' '.join(args), message.author, duration)
    except AssertionError:
        await message.channel.send(
            "Music was not found! If it is youtube, make sure it is a public video."
        )
        return
    if len(guild_state.playlist) != 0 or guild_state.now_playing is not None:
        guild_state.playlist.append(info)
        message = await message.channel.send(
            "Added to queue.", embed=info.get_embed())
    else:
        guild_state.playlist.append(info)
        await _play_music(message, voice_client, guild_state)


async def skip(client, message, *args):
    guild_state = get_guild_state(message.guild)
    voice_client = await ensure_in_voice_channel(message)
    if not voice_client:
        return
    if guild_state.now_playing is None:
        await message.channel.send("Not playing anything now.")
        return
    if len(guild_state.playlist) == 0:
        await message.channel.send("Skipped. Nothing remains in playlist. Exiting.")
        await voice_client.stop()
        await voice_client.disconnect()
    else:
        await message.channel.send("Skipped")
        await voice_client.stop()
        await _play_music(message, voice_client, guild_state)


async def leave(client, message, *args):
    if not message.author.guild_permissions.administrator:
        await message.channel.send("This command is restricted, to be used only by gods.")
        return
    voice_client = message.guild.voice_client
    if not voice_client:
        await message.channel.send("Not connected to any voice channels.")
        return
    summoners.pop(hash(voice_client))
    await voice_client.disconnect()


async def on_voice_state_update(member, before, after):
    voice_client = member.guild.voice_client
    if (voice_client and member in summoners.values() and
        before.channel == voice_client.channel and
            after.channel is None):
        summoners.pop(hash(voice_client))
        guild_states.pop(member.guild.id)
        await voice_client.stop()
        await voice_client.disconnect()


music_functions = {
    'play': (play, "Play some musix."),
    'leave': (leave, "Leave the voice channel."),
    'skip': (skip, "Skip the current song.")
}
