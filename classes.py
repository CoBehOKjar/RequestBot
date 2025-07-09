import discord
from typing import NamedTuple

class GameData(NamedTuple):
    name: str
    description: str
    image:str
    tags: list


class Request(NamedTuple):
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
    stroe: str = "Steam"
    store_link: str = ""
    #. Tech
    comment: str = ""
    ping: bool = True
    by: discord.User = None
    status: str = ""
    to_mod: bool = False
    mod_reasons: list = []
    to_mod_tags = []
    applied_tags = []