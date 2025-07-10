import os
import time
import re
import requests
import discord
import io
from loguru import logger
from PIL import Image
#~ from discord.ext import commands
#~ from discord import app_commands
#~ from dotenv import load_dotenv
from bs4 import BeautifulSoup


import classes
import db.database as database



#TODO Suggesting logic
async def suggesting(req):
    if req.FORUM is None:
        logger.error("Форум не выбран или не найден!")
        return "Ошибка: Форум не выбран или не найден.\nНапиши техадмину."
    if not isinstance(req.FORUM, discord.ForumChannel):
        logger.error("Указанный форум не является форумом!")
        return f"Ошибка: Указанный канал не форум, а: {type(req.FORUM)}\nНапиши техадмину."


    #. Getting AppID & check validation
    logger.debug("Получение AppID...")
    req.app_id = get_appid(req.game)
    if req.app_id == None:
        logger.error("Игра не найдена!")
        return "Ошибка: Игра не найдена."
    # If have AppID - create Steam link 
    req.store_link = f"https://store.steampowered.com/app/{req.app_id}"
    

    #. Getting game data
    logger.debug("Получение информации об игре...")
    game_data = get_game_data(req)

    req.name = game_data.name
    req.description = game_data.description
    image = game_data.image
    tags = game_data.tags


    #. Editing image
    logger.debug("Редактирование изображения...")
    req.image = edit(req, image)


    #. Tags sync
    logger.debug("Синхронизация тегов...")
    req.tags = tag_converter(req, tags)


    #. Message construct
    logger.debug("Сборка предложения...")
    content = f"{req.description}\n\n"

    if req.comment:
        content += f"Комментарий: {req.comment}\n"

    content += f"[{req.store}]({req.store_link})\nПредложено:"
    
    if req.ping:
        logger.debug("Пинг включен")
        content += f" {req.by.mention}"

    logger.debug("Создание топика...")
    thread, starter_message = await req.FORUM.create_thread(
        name=req.name,
        content=content,
        #applied_tags=dtags,
        file=req.image,
        suppress_embeds=True
    )

    if not req.ping:
        logger.debug("Пинг выключен")
        await starter_message.edit(content=content + f" {req.by.mention}")


    if not req.to_mod:
        req.status = "Игра добавлена в предложку."
    return req #TODO система кодов ошибок и статусов



#? AppID processing
#* Getting AppID
def get_appid(link: str):
    raw_link = link.strip()

    #. Is no link check
    logger.debug("Проверка на ID...")
    if raw_link.isdigit():
        return valid_appid(int(raw_link))

    # Allowed URL Patterns
    patterns = [
        r"store\.steampowered\.com/app/(\d+)",
        r"s\.team/a/(\d+)"
    ]

    #. Search ID in link
    logger.debug("Поиск AppID в ссылке...")
    for pattern in patterns:
        match = re.search(pattern, raw_link)
        if match:
            return valid_appid(int(match.group(1)))

    return None #TODO обработка ошибок


#* Check ID validate
def valid_appid(app_id):
    logger.debug("Проверка валидности AppID...")
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
    response = requests.get(url)
    time.sleep(1)
    data = response.json()
    
    if str(app_id) in data and data[str(app_id)]['success']:
        return app_id
    logger.error("AppID не валидна!")
    return None #TODO обработка ошибок



#? Game data pocessing
#* Getting game name, description, tags, image
def get_game_data(req):
    logger.debug("Запрос информации...")
    app_url = f"https://store.steampowered.com/api/appdetails?appids={req.app_id}&l=english"
    response = requests.get(app_url)
    time.sleep(1)
    data = response.json()
    data = data[str(req.app_id)]['data']

    #. Get English game name
    logger.debug("Получение названия игры...")
    name = data.get('name', '')

    #. Get header image
    logger.debug("Получение ссылки на изображение...")
    image = data.get('header_image', '')

    #. Get Russian description.
    logger.debug("Получение описания...")
    req, description = get_description(req)

    #. Get tags
    logger.debug("Получение тегов...")
    req, tags = get_tags(req)

    return classes.GameData(
        name=name,
        description=description,
        image=image,
        tags=tags
    )


#* Getting russian description
def get_description(req):
    logger.debug("Запрос описания...")
    app_url = f"https://store.steampowered.com/api/appdetails?appids={req.app_id}&l=russian"
    response = requests.get(app_url)
    time.sleep(1)
    data = response.json()
    data = data[str(req.app_id)]['data']

    #. Get description
    logger.debug("Выкорчевывание описания...")
    description = data.get('short_description', '')

    #. Check russian lang
    logger.debug("Проверка языка описания...")
    if description and re.search(r'[а-яА-Я]', description):
        logger.debug("Русский")
        return description
    logger.debug("Не русский")
    return None #TODO обработка ошибок

#* Getting game tags
def get_tags(req):
    logger.debug("Запрос тегов...")
    app_url = f"https://store.steampowered.com/app/{req.app_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.5'
    }

    try:
        response = requests.get(app_url, headers=headers)
        time.sleep(1)
        soup = BeautifulSoup(response.text, 'html.parser')

        tag_section = soup.find('div', class_='glance_tags popular_tags')

        if not tag_section:
            logger.error("Теги не найдены!")
            return []
        
        tags = [a.text.lower().strip() for a in tag_section.find_all('a')[:6]]
        logger.debug("Теги найдены")
        return tags
    
    except Exception:
        logger.error("Ошибка при получении тегов!")
        return [] #TODO обработка ошибок
   


#? Image processing
#* Downloading and editing image
def edit(req, link):
    logger.debug("Запрос изображения...")
    response = requests.get(link)
    if response.status_code != 200:
        logger.error("Изображение не получено!")
        return f"Ошибка при получении изображения: {response.status_code}"
    
    #. Get image from link
    logger.debug("Выкорчевывание изображения...")
    link_image = Image.open(io.BytesIO(response.content)).convert("RGBA")

    #. New canvas
    canvas = Image.new("RGBA", (460, 310), (0, 0, 0, 0))

    #. Paste image from link
    canvas.paste(link_image, (0, 20), link_image)

    #. Save changes
    edited_image = io.BytesIO()
    canvas.save(edited_image, format="PNG")
    edited_image.seek(0)

    #. Convert & return
    image = discord.File(fp=edited_image, filename="banner.png")
    edited_image.close()

    logger.debug("Изображение получено")
    return image


#? Tags processing
#* Converter steam tags to discord tags
def tag_converter(req, tags):
    logger.debug("Конвертация тегов...")

    # for t in tags:
    #     tag = database.get_steam_tag_connection(t)
    #     if tag != None:
    #         req.applied_tags.insert(tag)
    #     else:
    #         req.to_mod = True
    #         req.to_mod_tags.insert(tag)

    return tags