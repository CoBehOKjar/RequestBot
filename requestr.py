import os
import time
import logging
import re
import requests
import discord
import io
from PIL import Image
#~ from discord.ext import commands
#~ from discord import app_commands
#~ from dotenv import load_dotenv
from bs4 import BeautifulSoup
import classes

import database



#TODO Suggesting logic
async def suggesting(req):
    if req.FORUM is None:
        print("Форум не выбран или не найден!")
        return "Ошибка: Форум не выбран или не найден.\nНапиши техадмину."
    if not isinstance(req.FORUM, discord.ForumChannel):
        print("Указанный форум не является форумом!")
        return f"Ошибка: Указанный канал не форум, а: {type(req.FORUM)}\nНапиши техадмину."


    #. Getting AppID & check validation
    print("Получение AppID...")
    req.app_id = get_appid(req.game)
    if req.app_id == None:
        print("Игра не найдена!")
        return f"Ошибка: Игра не найдена."
    # If have AppID - create Steam link 
    req.store_link = f"https://store.steampowered.com/app/{req.app_id}"
    

    #. Getting game data
    print("Получение информации об игре...")
    req, game_data = get_game_data(req)

    req.name = game_data.name
    req.description = game_data.description
    image = game_data.image
    tags = game_data.tags


    #. Editing image
    print("Редактирование изображения...")
    req.image = edit(req, image)


    #. Tags sync
    print("Синхронизация тегов...")
    req.tags = tag_converter(req, tags)


    #. Message construct
    print("Сборка предложения...")
    content = f"{req.description}\n\n"

    if req.comment:
        print("Добавление комментария...")
        content += f"Комментарий: {req.comment}\n"

    print("Добавление автора...")
    content += f"[{req.store}]({req.store_link})\nПредложено:"
    
    print("Проверка пинга...")
    if req.ping:
        print("Пинг включен")
        content += f" {req.by.mention}"

    print("Создание топика...")
    thread, starter_message = await req.FORUM.create_thread(
        name=req.name,
        content=content,
        #applied_tags=dtags,
        file=req.image,
        suppress_embeds=True
    )

    if not req.ping:
        print("Пинг выключен")
        await starter_message.edit(content=content + f" {req.by.mention}")

    print("Игра добавлена в предложку.")
    if not req.to_mod:
        req.status = "Игра добавлена в предложку."
    return req #TODO система кодов ошибок и статусов



#? AppID processing
#* Getting AppID
def get_appid(link: str):
    raw_link = link.strip()

    #. Is no link check
    print("Проверка на ID...")
    if raw_link.isdigit():
        print("ID найден")
        return valid_appid(int(raw_link))

    # Allowed URL Patterns
    patterns = [
        r"store\.steampowered\.com/app/(\d+)",
        r"s\.team/a/(\d+)"
    ]

    #. Search ID in link
    print("Поиск AppID в ссылке...")
    for pattern in patterns:
        match = re.search(pattern, raw_link)
        if match:
            print("AppID найден")
            return valid_appid(int(match.group(1)))

    return None #TODO обработка ошибок


#* Check ID validate
def valid_appid(app_id):
    print("Проверка валидности AppID...")
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
    response = requests.get(url)
    time.sleep(1)
    data = response.json()
    
    if str(app_id) in data and data[str(app_id)]['success']:
        print("AppID валидна")
        return app_id
    print("AppID не валидна!")
    return None #TODO обработка ошибок



#? Game data pocessing
#* Getting game name, description, tags, image
def get_game_data(req):
    print("Запрос информации...")
    app_url = f"https://store.steampowered.com/api/appdetails?appids={req.app_id}&l=english"
    response = requests.get(app_url)
    time.sleep(1)
    data = response.json()
    data = data[str(req.app_id)]['data']

    #. Get English game name
    print("Получение названия игры...")
    name = data.get('name', '')

    #. Get header image
    print("Получение ссылки на изображение...")
    image = data.get('header_image', '')

    #. Get Russian description.
    print("Получение описания...")
    req, description = get_description(req)

    #. Get tags
    print("Получение тегов...")
    req, tags = get_tags(req)

    return req, classes.GameData(
        name=name,
        description=description,
        image=image,
        tags=tags
    )


#* Getting russian description
def get_description(req):
    print("Запрос описания...")
    app_url = f"https://store.steampowered.com/api/appdetails?appids={req.app_id}&l=russian"
    response = requests.get(app_url)
    time.sleep(1)
    data = response.json()
    data = data[str(req.app_id)]['data']

    #. Get description
    print("Выкорчевывание описания...")
    description = data.get('short_description', '')

    #. Check russian lang
    print("Проверка языка описания...")
    if description and re.search(r'[а-яА-Я]', description):
        print("Русский")
        return req, description
    print("Не русский")
    return req, None #TODO обработка ошибок

#* Getting game tags
def get_tags(req):
    print("Запрос тегов...")
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
            print("Теги не найдены!")
            return []
        
        tags = [a.text.lower().strip() for a in tag_section.find_all('a')[:6]]
        print("Теги найдены")
        return req, tags
    
    except Exception:
        print("Ошибка при получении тегов!")
        return req, [] #TODO обработка ошибок
   


#? Image processing
#* Downloading and editing image
def edit(req, link):
    print("Запрос изображения...")
    response = requests.get(link)
    if response.status_code != 200:
        print("Изображение не получено!")
        return f"Ошибка при получении изображения: {response.status_code}"
    
    #. Get image from link
    print("Выкорчевывание изображения...")
    link_image = Image.open(io.BytesIO(response.content)).convert("RGBA")

    #. New canvas
    print("Создание холста...")
    canvas = Image.new("RGBA", (460, 310), (0, 0, 0, 0))

    #. Paste image from link
    print("Вставка изображения...")
    canvas.paste(link_image, (0, 20), link_image)

    #. Save changes
    print("Сохранение изображения...")
    edited_image = io.BytesIO()
    canvas.save(edited_image, format="PNG")
    edited_image.seek(0)

    #. Convert & return
    print("Конвертация изображения...")
    image = discord.File(fp=edited_image, filename="banner.png")
    edited_image.close()

    print("Изображение получено")
    return req, image


#? Tags processing
#* Converter steam tags to discord tags
def tag_converter(req, tags):
    print("Конвертация тегов...")

    for t in tags:
        tag = database.get_steam_tag_connection(t)
        if tag != None:
            req.applied_tags.insert(tag)
        else:
            req.to_mod = True
            req.to_mod_tags.insert(tag)

    return req, tags