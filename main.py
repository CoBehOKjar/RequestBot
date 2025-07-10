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



#TODO навести порядок с капсом
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
REQTOPICID = 1388513660602814524
MODCHATID = 1389924810049589259
FORUMID = 1388512682147184691
#REQTOPICID = int(database.get_config("REQUEST_TOPIC_ID")) #TODO Сделать проверку превого запуска и наличия рабочего чата
#MODCHATID = int(database.get_config("MODERATION_CHAT_ID"))
#FORUMID = int(database.get_config("FORUM_ID"))

#* Bot's rights.
intents = discord.Intents.default()
intents.message_content = True
logger.info("Выданы права боту")

#* Create bot.
bot = commands.Bot(command_prefix="!!", intents=intents)
logger.info("Создана сущность бота")

REQTOPIC: discord.TextChannel = None
MODCHAT: discord.TextChannel = None
FORUM: discord.ForumChannel = None



#. Huh?
@bot.event
async def on_ready():
    await bot.tree.sync()
    logger.info(f"{bot.user} активен!")

    global REQTOPIC, MODCHAT, FORUM
    REQTOPIC = await bot.fetch_channel(REQTOPICID)
    MODCHAT = await bot.fetch_channel(MODCHATID)
    FORUM = await bot.fetch_channel(FORUMID)
    logger.info(f"Каналы инициализированы: {REQTOPIC}, {MODCHAT}, {FORUM}")


bot.run(TOKEN)