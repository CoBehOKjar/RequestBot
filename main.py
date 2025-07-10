# Request bot

#~ import os
import discord
from loguru import logger
from discord.ext import commands
#~ from discord import app_commands
#~ from dotenv import load_dotenv

#~ import requestr
#~ import db.database as database
#~ import classes
#~ import ccommands
import globals as GB

#. Huh?
@GB.bot.event
async def on_ready():
    await GB.bot.tree.sync()
    logger.info(f"{GB.bot.user} активен!")
    await GB.gb_init()