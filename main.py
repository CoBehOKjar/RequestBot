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



#TODO Slash commands:
#? First launch command
#TODO ... команда для установки форума, топика, канала модерации


#? Request command
#TODO ...
# Command description
@bot.tree.command(name="request", description="Предложить игру на канал.")
@app_commands.describe(
     game = "Ссылка на игру или Steam AppID",
     comment = "*Комментарий",
     ping = "*Пинговать при создании?",
     by = "*Для админов!"
)


# Command params
async def request(
    interaction: discord.Interaction,
    game: str,
    comment: str = "",
    ping: bool = True,
    by: discord.User = None
):
    req = classes.Request(FORUM=FORUM,
                          MODCHAT=MODCHAT,
                          game=game,
                          comment=comment,
                          ping=ping,
                          by=by
                          )
    
    logger.info("Запуск предложения...")
    #. Is forum check
    logger.debug("Проверка на форум...")
    if (
        interaction.channel_id != REQTOPICID
    ):
        await interaction.response.send_message(
            "Это не предложка!",
            ephemeral=True
        )
        logger.warning("Попытка вызова реквеста не в предложке!")
        return

    
    #. Admin check
    logger.debug("Проверка админки если использовано авторство...")
    if req.by is not None and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "Не для тебя поле сделано!",
            ephemeral=True
        )
        logger.warning("Попытка не админа предложить от другого лица!")
        return


    #. Status message sending
    logger.debug("Создание сообщения о предложении...")
    message = f"Создание предложения по {game} ..."
    if req.comment:
        message += f"\nС комментарием:\n> {req.comment}"
    if req.by:
        message += f"\nОт лица: {req.by}"

    await interaction.response.send_message(message, ephemeral=True)


    #. Creating topic
    logger.debug("Запуск создания топика...")
    #TODO сделать систему ошибок
    #TODO 404 - not found app
    try:
        requesting = await requestr.suggesting(req)

        await interaction.edit_original_response(content=f"{message}\n\n{requesting.status}")
        logger.info("Топик создан")

    except Exception as e:
        await interaction.edit_original_response(content=f"{message}\n\nОшибка: {str(e)}")
        logger.warning("Ошибка при создании топика")


#? Edit request command
#TODO ...


#! Moderation commands
#TODO ...


bot.run(TOKEN)