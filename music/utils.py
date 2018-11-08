import youtube_dl
import discord

YTDL_OPTS = {
    "default_search": "ytsearch",
    "format": "bestaudio/best",
    "quiet": True,
    "extract_flat": "in_playlist"
}


class MusicInfo:
    def __init__(self, search_str, requested_by, time_left):
        info = self._get_info(search_str)
        self.title = info['title']
        self.duration = info['duration']
        self.uploader = info['uploader']
        self.thumbnail = info['thumbnail'] if 'thumbnail' in info else None
        self.video_url = info['webpage_url']
        self.requested_by = requested_by
        self.time_left = time_left
        formats = {x['abr']: x for x in info['formats'] if 'abr' in x and 'tbr' in x}
        assert formats is not None and formats != {}
        abr_max = max(formats.keys())
        source = formats[abr_max]
        self.stream_url = source['url']

    def _get_info(self, search_str):
        with youtube_dl.YoutubeDL(YTDL_OPTS) as ydl:
            try:
                info = ydl.extract_info(search_str, download=False)
                if "_type" in info and info["_type"] == "playlist":
                    return self._get_info(info['entries'][0]['url'])
                return info
            except youtube_dl.utils.DownloadError:
                raise AssertionError

    def get_embed(self):
        embed = discord.Embed(
            title=self.title,
            description="Uploaded by: {0}".format(self.uploader),
            url=self.video_url)
        mins = self.duration//60
        secs = self.duration - mins*60
        embed.add_field(
            name="Duration",
            value="{0:>02d}:{1:>02d}".format(mins, secs))
        if self.time_left:
            hours = self.time_left//3600
            mins = self.time_left//60 - hours*60
            secs = self.time_left - mins*60 - hours*3600
            embed.add_field(
                name="Will Play In",
                value="{0:>02d}:{1:>02d}:{2:>02d}".format(hours, mins, secs))
        if self.thumbnail:
            embed.set_thumbnail(url=self.thumbnail)
        embed.set_footer(text="Requested by: {0}".format(self.requested_by.name),
                         icon_url=self.requested_by.avatar_url)
        return embed


class GuildState:
    def __init__(self):
        self.volume = 1.0
        self.playlist = []
        self.now_playing = None

        def is_requester(self, member):
            return self.now_playing.requested_by == member
