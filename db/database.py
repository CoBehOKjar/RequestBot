# DB logic
import os
import sqlite3
import discord



#* Check folder
db_folder = "db"
os.makedirs(db_folder, exist_ok=True)

#* DB pathes
config_path = os.path.join(db_folder, "config.db")
games_path = os.path.join(db_folder, "games.db")
tags_path = os.path.join(db_folder, "tags.db")



#* Bot config
config_conn = sqlite3.connect(config_path)
config_cursor = config_conn.cursor()

config_cursor.execute(

"""--sql
CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT
)
"""
)

config_conn.commit()


#. Bot config processing
#? Get bot config
def get_config(key: str):
    config_cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
    result = config_cursor.fetchone()
    return result[0] if result else None


#? Edit bot config
def set_config(key: str, value: str):
    config_cursor.execute("REPLACE INTO config (key, value) VALUES (?, ?)", (key, value))
    config_conn.commit()



#* Games list
games_conn = sqlite3.connect(games_path)
games_cursor = games_conn.cursor()

games_cursor.execute(
    
"""--sql
CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_id TEXT NOT NULL,
    suggested_by INTEGER NOT NULL,
    comment TEXT,
    executed_by INTEGER,
    forum_topic_id INTEGER,
    bot_message_id INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
"""
)

games_conn.commit()


#. Games list processing
#? Adding new game
def add_game(app_id, suggested_by, comment=None, executed_by=None, forum_topic_id=None, bot_message_id=None):
    games_cursor.execute("""--sql
        INSERT INTO games (app_id, suggested_by, comment, executed_by, forum_topic_id, bot_message_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (app_id, suggested_by, comment, executed_by, forum_topic_id, bot_message_id))
    games_conn.commit()

#? Get game info
#TODO ...


#? Edit game info
#TODO ...


#? Delete game info
#TODO ...



#* Tags list
tags_conn = sqlite3.connect(tags_path)
tags_cursor = tags_conn.cursor()

tags_cursor.execute(

"""--sql
CREATE TABLE IF NOT EXISTS tags (
    steam_tag TEXT PRIMARY KEY,
    discord_tag INTEGER NOT NULL
)
"""
)

tags_conn.commit()


#. Tags list processing
#? Add new tag connect
#TODO ... доработать вывод
def add_tag(steam_tag: str, discord_tag: discord.ForumTag):
    try:
        tags_cursor.execute("""--sql
            INSERT INTO tags (steam_tag, discord_tag)
            VALUES (?, ?)
        """, (steam_tag, discord_tag))
        tags_conn.commit()
        print("Sucsess: Tag added.")

    except sqlite3.IntegrityError:
        print("Dublicate: Tag already added.")


#? Get discord tag connections
#TODO ...


#? Get steam tag connection
#TODO ...
def get_steam_tag_connection(steam_tag: str) -> tuple | None:
    tags_cursor.execute("""--sql
        SELECT steam_tag, discorf_tag FROM tags WHERE steam_tag = ?
    """, steam_tag)
    return tags_cursor.fetchone()


#? Edit tag connect
#TODO ...


#? Delete tag connect
#TODO ...