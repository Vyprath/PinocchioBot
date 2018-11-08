from .utils import MusicInfo, GuildState
import discord
import asyncio


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
        return voice_client
    elif voice_client.channel == voice_state.channel:
        return voice_client
    else:
        await message.channel.send("""
Bot is already connected to a voice channel.
Make the bot leave previous voice channel with `!leave`. Requires **administrator** permission.
Or ask everyone to leave the previous voice channel.
""")
        return None


async def _play_music(message, voice_client, guild_state):
    if len(guild_state.playlist) == 0:
        await stop_bot(voice_client, message.guild.id)
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


async def stop_bot(voice_client, guild_id):
    if voice_client.is_playing():
        voice_client.stop()
    if guild_id in guild_states:
        guild_states.pop(guild_id)
    await voice_client.disconnect()


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
    if voice_client is None:
        return
    if guild_state.now_playing is None:
        await message.channel.send("Not playing anything now.")
        return
    if len(guild_state.playlist) == 0:
        await message.channel.send("Skipped. Nothing remains in playlist. Exiting.")
        await stop_bot(voice_client, message.guild.id)
    else:
        await message.channel.send("Skipped")
        if voice_client.is_playing():
            voice_client.stop()
        await _play_music(message, voice_client, guild_state)


async def leave(client, message, *args):
    if not message.author.guild_permissions.administrator:
        await message.channel.send("This command is restricted, to be used only by gods.")
        return
    voice_client = message.guild.voice_client
    if voice_client is None:
        await message.channel.send("Not connected to any voice channels.")
        return
    await stop_bot(voice_client, message.guild.id)


async def queue(client, message, *args):
    voice_client = await ensure_in_voice_channel(message)
    guild_state = get_guild_state(message.guild)
    if not voice_client:
        return
    playlist = guild_state.playlist
    if guild_state.now_playing is not None:
        playlist.insert(0, guild_state.now_playing)
    if playlist == []:
        await message.channel.send("Playlist is empty.")
    else:
        msg = "Current Queue:\n"
        duration = 0
        for i, v in enumerate(playlist):
            hours = duration//3600
            mins = duration//60 - hours*60
            secs = duration - mins*60 - hours*3600
            plays_in_txt = (
                "Plays in: {0:>02d}:{1:>02d}:{2:>02d}".format(hours, mins, secs)
                if duration > 0 else "Now Playing")
            msg += "{0}. **{1}** by *{2}*. Duration: {3}. {4}.\n".format(
                i + 1, v.title, v.uploader, v.duration, plays_in_txt)
            duration += v.duration
            if len(msg) > 1800:
                await message.channel.send(msg)
                msg = ""
        if msg != "":
            await message.channel.send(msg)


async def volume(client, message, *args):
    voice_client = ensure_in_voice_channel(message)
    if voice_client is None:
        return
    guild_state = get_guild_state(message.guild)
    if len(args) != 1 or not args[0].isdigit() or not (1 <= int(args[0]) <= 200):
        await message.channel.send("Usage: !volume <volume % between 1 to 200>")
        return
    volume = int(args[0])/100
    guild_state.volume = volume
    await message.channel.send(
        "Set volume to {0}%. Please skip current song. :thumbsup:".format(args[0]))


async def on_voice_state_update(member, before, after):
    voice_client = member.guild.voice_client
    if voice_client:
        members_list = [x for x in voice_client.channel.members if not x.bot]
    else:
        members_list = 0
    if voice_client is not None and len(members_list) == 0:
        await stop_bot(voice_client, member.guild.id)


music_functions = {
    'p': (play, "Play some musix."),
    'play': (play, "Play some musix."),
    'leave': (leave, "Leave the voice channel."),
    'skip': (skip, "Skip the current song."),
    'queue': (queue, "View current queue."),
    'volume': (volume, "Set volume (default 100%).")
}
