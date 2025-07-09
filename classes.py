import discord
from typing import NamedTuple
from dataclasses import dataclass, field

class GameData(NamedTuple):
    name: str
    description: str
    image:str
    tags: list


@dataclass
class Request:
    #. Base
    FORUM: discord.ForumChannel
    MODCHAT: discord.TextChannel
    #. Game
    game: str = None
    app_id: int = None
    name: str = None
    description: str = None
    image: discord.File = None
    tags: list = None
    store: str = "Steam"
    store_link: str = ""
    #. Tech
    comment: str = ""
    ping: bool = True
    by: discord.User = None
    status: str = ""
    to_mod: bool = False
    mod_reasons: list = field(default_factory=list)
    to_mod_tags: list = field(default_factory=list)
    applied_tags: list = field(default_factory=list)