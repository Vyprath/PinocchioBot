import variables
from discord import AudioSource
import subprocess


class URLSource(AudioSource):
    stream_url = ""
    volume_mod = 1.0

    def __init__(self, stream_url, codec=None):
        self.stream_url = stream_url

    def read():
        pass
    
    def is_opus():
        return False