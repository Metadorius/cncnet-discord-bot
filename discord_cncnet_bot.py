import discord
import os.path
import asyncio
import logging
import signal

from irc_client import IRCClient
from discord.ext import commands
from discord.ext.commands import has_permissions
from typing import *
from data_classes import *
from discord_utils import *
from utils import *


GAME_TIMEOUT = 35
UPDATE_INTERVAL = 30


class DiscordCnCNetBot(object):

    def __init__(self, config_path: str = 'config.json', event_loop=None):
        self.config_path = config_path

        if os.path.isfile(self.config_path):
            self.config = BotConfig.read_from_file(self.config_path)
        else:
            self.config = BotConfig()

        if not self.config.discord_token:
            logging.warning("No Discord token set")

        self.event_loop = event_loop if event_loop else asyncio.new_event_loop()

        self.hosted_games: Dict[str, GameMessagePair] = {}

        self.irc_client = IRCClient(
            nickname=self.config.irc_name,
            eventloop=self.event_loop)
        self.setup_irc_client()

        self.discord_client = commands.Bot(
            command_prefix=self.config.discord_prefix,
            loop=self.event_loop)
        self.setup_discord_client()

        self.irc_user_count_cache: int = 0
        # self.discord_user_count_cache: int = 0

        self.event_handlers = {}

        super().__init__(*args, **kwargs)


    def event_handler(self, f):
        self.event_handlers[f.__name__] = f
        return f


    async def update_online_counts(self):
        self.irc_user_count_cache = len(self.irc_client.channels[self.config.irc_lobby_channel].users)
        self.event_handlers["on_online_count_update"](self)


    @self.event_handler
    async def on_online_count_update(self):
        self.discord_client.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name=f"{self.config.game_short_name} | {self.irc_user_count_cache} players"))


    async def cleanup_obsolete_games(self):
        to_remove = []

        for sender in self.hosted_games:
            if (datetime.utcnow() - self.hosted_games[sender].game.timestamp).seconds > GAME_TIMEOUT:
                to_remove.append(sender)

        for sender in to_remove:
            try:
                await self.hosted_games[sender].message.edit(embed=None, content=f"A game hosted by **`<{sender}>`** was abandoned.")
                self.hosted_games.pop(sender, None)
            except:
                pass


    async def retrieve_game_message(self, sender, hosted_game):

        list_id = self.config.discord_list_channel
        list_channel = self.discord_client.get_channel(list_id)

        msg = await list_channel.send(embed=hosted_game.get_embed(host=sender))

        if not msg:
            # workaround for when the message is sent but discord returns 503
            msg = await list_channel.history().find(lambda m: m.author == self.discord_client.user and m.embed.author.name == sender)

        return msg


    def setup_irc_client(self):

        @self.irc_client.event_handler
        async def on_connect():
            await self.irc_client.join(self.config.irc_lobby_channel)
            await self.irc_client.join(self.config.irc_broadcast_channel)

        @self.irc_client.event_handler
        async def on_message(channel, sender, message):
            """Forward IRC message to Discord channel."""
            if sender == self.irc_client.nickname:
                return

            # Remove color index from the message
            if message[0] == '':
                message = message[3:]

            if self.config.discord_message_channel:
                msg_channel = self.discord_client.get_channel(self.config.discord_message_channel)
                await msg_channel.send(f"**`<{sender}>`** {message}")

        @self.irc_client.event_handler
        async def on_ctcp_game_reply(sender, channel, contents):
            """Handle CTCP GAME message broadcasted by clients when they host a game."""
            logging.info("Received a CTCP GAME message")

            try:
                hosted_game = HostedGame(contents,
                    CnCNetGame(self.config.game_name, self.config.game_icon_url, self.config.game_url))
                
                if hosted_game.is_closed:
                    if sender in self.hosted_games:
                        # if we have it in game list - remove the message and the game
                        if self.hosted_games[sender].message:
                            msg = self.hosted_games[sender].message
                            await msg.edit(embed=None, content=f"A game hosted by **`<{sender}>`** was abandoned.")

                        self.hosted_games.pop(sender, None)

                else:
                    if sender in self.hosted_games:
                        # update the message if already listed
                        self.hosted_games[sender].game = hosted_game

                        if self.config.discord_list_channel:
                            try:
                                msg = self.hosted_games[sender].message
                                if not msg:
                                    list_channel = self.discord_client.get_channel(list_id)
                                    self.hosted_games[sender].message = await list_channel.send(
                                        embed=hosted_game.get_embed(host=sender))
                                else:
                                    await msg.edit(embed=hosted_game.get_embed(host=sender))

                            except discord.errors.NotFound:
                                # if for some reason it wasn't found - send it
                                self.hosted_games[sender].message = await self.retrieve_game_message(sender, hosted_game)
                                    
                    else:
                        # post a new message in the list channel and announce the game (if channels are set)
                        self.hosted_games[sender] = GameMessagePair(hosted_game)

                        if self.config.discord_list_channel:
                            self.hosted_games[sender].message = await self.retrieve_game_message(sender, hosted_game)
                            
                        # if self.config.discord_announce_channel:
                        #     announce_id = self.config.discord_announce_channel
                        #     announce_channel = self.discord_client.get_channel(announce_id)
                        #     await announce_channel.send(self.config.discord_announce_message)
                    
            except Exception as e:
                logging.error(e, exc_info=True)


    def setup_discord_client(self):

        @self.discord_client.event
        async def on_message(message):
            if (self.config.irc_lobby_channel and
                message.author != self.discord_client.user and
                message.channel.id == self.config.discord_message_channel):

                await self.irc_client.message(self.config.irc_lobby_channel, f"<{message.author}> {message.content}")

            await self.discord_client.process_commands(message)


        @self.discord_client.command()
        @has_permissions(administrator=True)
        async def config(context, key, value):
            """Sets certain config variables via a chat command."""

            # if key == "discord_prefix":
            #     self.config.discord_prefix = value
            if key == "discord_message_channel":
                self.config.discord_message_channel = parse_channel(value)
            # elif key == "discord_announce_channel":
            #     self.config.discord_announce_channel = parse_channel(value)
            elif key == "discord_list_channel":
                self.config.discord_list_channel = parse_channel(value)
            elif key == "discord_announce_message":
                self.config.discord_announce_message = value
            else:
                return

            self.config.write_to_file(self.config_path)

            response = f"The value for key `{key}` is now `{value}`. "
            await context.send(response)


    def run(self):
        try:
            if not self.config.discord_token:
                raise NotConfiguredException(f"Discord token isn't set in {self.config_path}")

            self.event_loop.create_task(self.irc_client.connect(
                self.config.irc_host,
                self.config.irc_port,
                reconnect=False))

            self.event_loop.create_task(self.discord_client.start(
                self.config.discord_token))

            schedule_task_periodically(GAME_TIMEOUT, self.cleanup_obsolete_games, self.event_loop)
            schedule_task_periodically(UPDATE_INTERVAL, self.update_online_counts, self.event_loop)

            logging.info(f"Running main loop")
            self.event_loop.run_forever()

        except KeyboardInterrupt:
            logging.info(f"Caught interrupt")

        finally:
            logging.info(f"Finishing and cleaning up")
            self.event_loop.run_until_complete(asyncio.gather(
                self.discord_client.logout(),
                self.irc_client.disconnect(),
                loop=self.event_loop))

            self.config.write_to_file(self.config_path)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.default_int_handler)
    logging.basicConfig(level=logging.WARN)
    bot = DiscordCnCNetBot()
    bot.run()
