# Request bot

import os
import discord
from loguru import logger
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

import requestr
import db.database as database
import classes
import ccommands
import globals as GB



#* Bot's rights.
intents = discord.Intents.default()
intents.message_content = True
logger.info("Выданы права боту")

#* Create bot.
bot = commands.Bot(command_prefix="!!", intents=intents)
logger.info("Создана сущность бота")


#. Huh?
@bot.event
async def on_ready():
    await bot.tree.sync()
    logger.info(f"{bot.user} активен!")

GB.gb_init(bot)

bot.run(GB.TOKEN)