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
import globals as GB



#TODO Suggesting logic
async def suggesting(req: classes.Request) -> classes.Request:
    #? Check has forum & forum channel type
    if req.FORUM is None:
        req.errors.add_dev("Форум не выбран или не найден!")
        req.errors.add_user("Форум не выбран или не найден. Напиши техадмину.")
        req.errors.status = "Ошибка:"
        return req
    if not isinstance(req.FORUM, discord.ForumChannel):
        req.errors.add_dev(f"{req.FORUM} не форум, а: {type(req.FORUM)}")
        req.errors.add_user(f"Ошибка: Указанный канал не форум, а: {type(req.FORUM)}. Напиши техадмину.")
        req.errors.status = "Ошибка:"
        return req


    #. Getting AppID & check validation
    logger.debug("Получение AppID...")
    req = get_appid(req)
    if req.info.app_id == None:
        req.errors.add_dev("Игра не найдена!")
        return "Ошибка: Игра не найдена."
    # If have AppID - create Steam link 
    req.info.store_link = f"https://store.steampowered.com/app/{req.info.app_id}"
    

    #. Getting game data
    logger.debug("Получение информации об игре...")
    game_data = get_game_data(req)

    req.info.name = game_data.name
    req.info.description = game_data.description
    image = game_data.image
    tags = game_data.tags


    #. Editing image
    logger.debug("Редактирование изображения...")
    req.info.image = edit(image)


    #. Tags sync
    logger.debug("Синхронизация тегов...")
    req.info.tags = tag_converter(tags)


    #. Message construct
    logger.debug("Сборка предложения...")
    content = f"{req.info.description}\n\n"

    if req.params.comment:
        content += f"Комментарий: {req.params.comment}\n"

    content += f"[{req.info.store}]({req.info.store_link})\nПредложено:"

    #. Creating right mention
    mention = req.params.by.mention if req.params.by else req.params.author.mention

    if req.params.ping:
        logger.debug("Пинг включен")
        content += f" {mention}"

    logger.debug("Создание топика...")
    thread, starter_message = await req.FORUM.create_thread(
        name=req.info.name,
        content=content,
        #applied_tags=dtags,
        file=req.info.image,
        suppress_embeds=True
    )

    if not req.params.ping:
        logger.debug("Пинг выключен")
        await starter_message.edit(content=content + f" {mention}", suppress_embeds=True)


    if not req.tech.to_mod:
        req.tech.status = "Игра добавлена в предложку."
    return req #TODO система кодов ошибок и статусов



#? AppID processing
#* Getting AppID
def get_appid(link: str, req: classes.Request):
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

    errors.add_dev(f"Не найдена страница Steam по: {link}")
    errors.add_user(f"Не найдена страница Steam по: {link}")
    errors.status = "Ошибка:"
    return


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
def get_game_data(req: classes.Request):
    logger.debug("Запрос информации...")
    app_url = f"https://store.steampowered.com/api/appdetails?appids={req.info.app_id}&l=english"
    response = requests.get(app_url)
    time.sleep(1)
    data = response.json()
    data = data[str(req.info.app_id)]['data']

    #. Get English game name
    logger.debug("Получение названия игры...")
    name = data.get('name', '')

    #. Get header image
    logger.debug("Получение ссылки на изображение...")
    image = data.get('header_image', '')

    #. Get Russian description.
    logger.debug("Получение описания...")
    description = get_description(req)

    #. Get tags
    logger.debug("Получение тегов...")
    tags = get_tags(req)

    return classes.GameData(
        name=name,
        description=description,
        image=image,
        tags=tags
    )


#* Getting russian description
def get_description(req: classes.Request):
    logger.debug("Запрос описания...")
    app_url = f"https://store.steampowered.com/api/appdetails?appids={req.info.app_id}&l=russian"
    response = requests.get(app_url)
    time.sleep(1)
    data = response.json()
    data = data[str(req.info.app_id)]['data']

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
def get_tags(req: classes.Request):
    logger.debug("Запрос тегов...")
    app_url = f"https://store.steampowered.com/app/{req.info.app_id}"
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
def edit(link):
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
def tag_converter(tags):
    logger.debug("Конвертация тегов...")

    # for t in tags:
    #     tag = database.get_steam_tag_connection(t)
    #     if tag != None:
    #         req.applied_tags.insert(tag)
    #     else:
    #         req.to_mod = True
    #         req.to_mod_tags.insert(tag)

    return tags