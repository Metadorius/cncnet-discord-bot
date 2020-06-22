import pydle
import logging
from data_classes import *

Base = pydle.featurize(pydle.features.RFC1459Support, pydle.features.TLSSupport, pydle.features.CTCPSupport)
class IRCClient(Base):

    def __init__(self, *args, **kwargs):

        self.event_handlers = {}

        super().__init__(*args, **kwargs)

    def event_handler(self, f):
        self.event_handlers[f.__name__] = f
        return f

    async def on_connect(self):
        await super().on_connect()
        await self.event_handlers["on_connect"]()

    async def on_message(self, channel, sender, message):
        await super().on_message(channel, sender, message)
        await self.event_handlers["on_message"](channel, sender, message)

    async def on_ctcp_game_reply(self, sender, channel, contents):
        await self.event_handlers["on_ctcp_game_reply"](sender, channel, contents)