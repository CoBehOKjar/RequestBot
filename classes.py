import discord
from typing import NamedTuple
from dataclasses import dataclass, field
from loguru import logger

class GameData(NamedTuple):
    #. Raw game data from steam
    name: str
    description: str
    image:str
    tags: list



@dataclass
class GameInfo:
    #. Game
    app_id: int = None
    name: str = None
    description: str = None
    image: discord.File = None
    tags: list = None
    store: str = "Steam"
    store_link: str = ""


@dataclass
class RequestParams:
    #. Params
    author: discord.User
    comment: str
    ping: bool = True
    by: discord.User = None


@dataclass
class TechInfo:
    #. Tech
    topic_id: int = 0
    message_id: int = 0
    status: str = ""
    to_mod: bool = False
    mod_reasons: list = field(default_factory=list)
    to_mod_tags: list = field(default_factory=list)
    applied_tags: list = field(default_factory=list)


@dataclass
class Errors:
    user_output: list[str] = field(default_factory=list)
    dev_output: list[str] = field(default_factory=list)

    def add_user(self, msg: str):
        logger.error(f"UserError: {msg}")
        self.user_output.append(msg)
    
    def add_dev(self, msg: str):
        logger.error(f"DevError: {msg}")
        self.dev_output.append(msg)
    
    def has_errors(self) -> bool:
        return bool(self.user_output or self.dev_output)
    
    def format_to_user(self) -> str:
        return "\n".join(self.user_output)


@dataclass
class Request:
    #. Base
    FORUM: discord.ForumChannel
    MODCHAT: discord.TextChannel
    link: str

    info: GameInfo = field(default_factory=GameInfo)
    params: RequestParams = field(default_factory=RequestParams)
    tech: TechInfo = field(default_factory=TechInfo)
    errors: Errors = field(default_factory=Errors)