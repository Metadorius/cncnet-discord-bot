import json
import discord

from distutils.util import strtobool
from typing import List
from datetime import datetime
from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class BotConfig(object):

    game_name: str = 'CnCNet game'
    game_short_name: str = ''
    game_url: str = 'https://cncnet.org'
    game_icon_url: str = 'https://avatars0.githubusercontent.com/u/11489929?s=200&v=4'

    discord_token: str = ''
    discord_prefix: str = '!'
    discord_announce_channel: int = None
    discord_list_channel: int = None
    discord_message_channel: int = None

    discord_announce_message: str = "Hey people, a new game has been hosted!"

    irc_host: str = 'irc.gamesurge.net'
    irc_port: int = 6667
    irc_name: str = 'discord_bot'
    irc_lobby_channel: str = ''
    irc_broadcast_channel: str = ''

    @staticmethod
    def read_from_file(json_path):
        with open(json_path) as json_file:
            return BotConfig.from_dict(json.load(json_file))

    def write_to_file(self, json_path):
        with open(json_path, 'w') as json_file:
            json.dump(self.to_dict(), json_file, indent=4)

@dataclass
class CnCNetGame(object):
    """Represents information about a game or mod on CnCNet."""

    name: str
    icon_url: str
    site_url: str

class NotConfiguredException(Exception):
    """An exception that is thrown when the bot hasn't been configured."""
    def __init__(self, msg="Bot wasn't confgiured via the config file.", *args, **kwargs):
        super().__init__(msg, *args, **kwargs)


class ParseException(Exception):
    """An exception that is thrown upon trying to parse incorrect CTCP GAME command message."""


@dataclass
class HostedGame(object):
    """Represents information about a game lobby hosted on CnCNet."""

    game: CnCNetGame

    protocol_version: str
    game_version: str
    max_players: int
    channel_name: str
    display_name: str
    is_locked: bool
    is_passworded: bool
    is_closed: bool
    is_loaded: bool
    is_ladder: bool
    players: List[str]
    map_name: str
    game_mode: str
    tunnel_address_and_port: str
    loaded_game_id: str

    def __init__(self, command_contents: str, game: CnCNetGame):
        self.parse_message_string(command_contents)
        self.game: CnCNetGame = game

    def parse_message_string(self, command_contents: str):
        """Parses CTCP GAME command message that's broadcasted by XNA client when the game is hosted."""

        self.timestamp = datetime.now()

        split: List[str] = command_contents.split(';')

        if (len(split) != 11):
            raise ParseException('The provided string has invalid amount of parameters')

        self.protocol_version: str = split[0]
        self.game_version: str = split[1]
        self.max_players: int = int(split[2])
        self.channel_name: str = split[3]
        self.display_name: str = split[4]
        self.is_locked: bool = bool(strtobool(split[5][0]))
        self.is_passworded: bool = bool(strtobool(split[5][1]))
        self.is_closed: bool = bool(strtobool(split[5][2]))
        self.is_loaded: bool = bool(strtobool(split[5][3]))
        self.is_ladder: bool = bool(strtobool(split[5][4]))
        self.players: List[str] = split[6].split(',')
        self.map_name: str = split[7]
        self.game_mode: str = split[8]
        self.tunnel_address_and_port: str = split[9]
        self.loaded_game_id: str = split[10]

    def get_embed(self, host: str = None) -> discord.Embed:
        """Returns hosted game information formatted as embed in form of discord.py Embed instance."""

        embed_title = self.display_name
        if self.is_locked:
            embed_title += "🔒"
        if self.is_passworded:
            embed_title += "🔑"

        embed: discord.Embed = discord.Embed(
            title=embed_title,
            # colour=Colour(0xd5d7da),
            description=f"[{self.game.name}]({self.game.site_url}) {self.game_version}"
        )

        embed.set_thumbnail(url=self.game.icon_url)
        if host:
            embed.set_author(name=host)
        # embed.set_footer(text="footer text", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")

        embed.add_field(name="🎮 Game mode", value=self.game_mode, inline=True)
        embed.add_field(name="🗺 Map", value=self.map_name, inline=True)
        # embed.add_field(name="🔢 Version", value=self.game_version, inline=True)
        embed.add_field(name=f"🧍 Players ({self.players} / {self.max_players})", value="\n".join(self.players), inline=True)

        # TODO write rest of the stuff

        return embed

@dataclass
class GameMessagePair(object):
    """A class which stores a hosted game and a corresponding Discord embed message."""

    game: HostedGame
    message: discord.Message = None
