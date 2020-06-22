import discord
import os.path
import asyncio
import logging

from configparser import ConfigParser
from irc_client import IRCClient
# from discord_client import DiscordClient
from discord.ext import commands

from data_classes import *
from discord_utils import *


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

        self.hosted_games = {}

        self.irc_client = IRCClient(
            nickname=self.config.irc_name,
            eventloop=self.event_loop)
        self.setup_irc_client()

        self.discord_client = commands.Bot(
            command_prefix=self.config.discord_prefix,
            loop=self.event_loop)
        self.setup_discord_client()


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

            # clean up some garbo
            trimmed_msg = message[3:]
            if self.config.discord_message_channel:
                msg_channel = self.discord_client.get_channel(self.config.discord_message_channel)
                await msg_channel.send(f"**<{sender}>** {trimmed_msg}")

        @self.irc_client.event_handler
        async def on_ctcp_game_reply(sender, channel, contents):
            """Handle CTCP GAME message broadcasted by clients when they host a game."""
            logging.info("Received a CTCP GAME message")

            try:
                hosted_game = HostedGame(contents, CnCNetGame(self.config.game_name, self.config.game_icon_url, self.config.game_url))
                if hosted_game.is_closed:
                    self.hosted_games.pop(sender, None)
                else:
                    self.hosted_games[sender] = hosted_game
                    logging.info(f"{sender} has broadcasted a {hosted_game.display_name} game in {channel}")
            except Exception as e:
                logging.warning(f"Got error when parsing game message: {e}")


    def setup_discord_client(self):

        @self.discord_client.event
        async def on_message(message):
            if (self.config.irc_lobby_channel and
                message.author != self.discord_client.user and
                message.channel.id == self.config.discord_message_channel):
                await self.irc_client.message(self.config.irc_lobby_channel, f"<{message.author}> {message.content}")

            await self.discord_client.process_commands(message)

        @self.discord_client.command()
        async def config(ctx, key, value):
            if key == "discord_prefix":
                self.config.discord_prefix = value
            elif key == "discord_message_channel":
                self.config.discord_message_channel = parse_channel(value)
            elif key == "discord_announce_channel":
                self.config.discord_announce_channel = parse_channel(value)
            elif key == "discord_list_channel":
                self.config.discord_list_channel = parse_channel(value)
            else:
                return

            response = f"The value for key `{key}` is now `{value}`. "
            await ctx.send(response)

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
    logging.basicConfig(level=logging.INFO)
    bot = DiscordCnCNetBot()
    bot.run()
