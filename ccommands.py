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
    req = classes.Request(FORUM=FORUM, MODCHAT=MODCHAT, link=game)
    req.params.author = interaction.user
    req.params.comment = comment
    req.params.ping = ping
    req.params.by = by
    
    logger.info(f"Запуск предложения по: {req.link}")
    #. Is forum check
    logger.debug("Проверка на форум...")
    if (
        interaction.channel_id != REQTOPICID
    ):
        await interaction.response.send_message(
            "Это не предложка!",
            ephemeral=True
        )
        logger.warning(f"{req.params.author} попытался вызвать реквест не в предложке!")
        return

    
    #. Admin check
    logger.debug("Проверка админки если использовано авторство...")
    if req.params.by is not None and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "Не для тебя поле сделано!",
            ephemeral=True
        )
        logger.warning(f"{req.params.author} попытался зареквестить от лица {req.params.by} !")
        return


    #. Status message sending
    logger.debug("Создание сообщения о предложении...")
    message = f"Создание предложения по {game} ..."
    if req.params.comment:
        message += f"\nС комментарием:\n> {req.params.comment}"
    if req.params.by:
        message += f"\nОт лица: {req.params.by}"

    await interaction.response.send_message(message, ephemeral=True)


    #. Creating topic
    logger.debug("Запуск создания топика...")
    #TODO сделать систему ошибок
    #TODO 404 - not found app
    try:
        requesting = await requestr.suggesting(req)

        await interaction.edit_original_response(content=f"{message}\n\n{requesting.tech.status}")
        
        channel = "Topic" #TODO сделать получение id топика после создания await bot.fetch_channel(req.tech.topic_id)
        logger.info(f"Создан топик: {channel} ({req.tech.topic_id}). Сообщение бота: {req.tech.message_id}")


    except Exception as e:
        await interaction.edit_original_response(content=f"{message}\n\nОшибка: {str(e)}")
        logger.error(f"Ошибка при создании топика: {str(e)}")


#? Edit request command
#TODO ...


#! Moderation commands
#TODO ...