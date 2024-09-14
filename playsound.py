import discord
import os
import sqlite3
import datetime
import logging
import requests
import hashlib
from discord import app_commands
from urllib.parse import urlparse

# データベース名
DATABASE_NAME = 'sound_effects.db'

# ログの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def initialize_db():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sound_effects (
            guild_id INTEGER,
            name TEXT,
            file TEXT,
            PRIMARY KEY (guild_id, name)
        )
    ''')
    conn.commit()
    conn.close()

initialize_db()

def execute_db_query(query, params=(), commit=False):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute(query, params)
    if commit:
        conn.commit()
    result = c.fetchall()
    conn.close()
    return result

def log_database_contents():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    try:
        c.execute('SELECT * FROM sound_effects')
        rows = c.fetchall()
        if rows:
            for row in rows:
                logger.info(f"Database row: {row}")
        else:
            logger.info("No data found in the database.")
    except sqlite3.Error as e:
        logger.error(f"Error occurred while reading the database: {e}")
    finally:
        conn.close()

def download_sound_file(url, guild_id):
    response = requests.get(url)
    if response.status_code == 200:
        # URLからファイル名を安全に生成
        parsed_url = urlparse(url)
        file_name = hashlib.sha256(url.encode('utf-8')).hexdigest()
        extension = os.path.splitext(parsed_url.path)[-1]
        sound_file_name = f"{file_name}{extension}"
        save_path = f"./data/sounds/{guild_id}/{sound_file_name}"
        
        # ディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        return save_path
    else:
        raise Exception(f"Failed to download file from URL: {url}, Status Code: {response.status_code}")
    
def get_sound_file(guild_id, name):
    result = execute_db_query('SELECT file FROM sound_effects WHERE guild_id = ? AND name = ?', (guild_id, name))
    if result:
        return result[0][0]
    return None



# VC参加コマンド
async def join_vc(interaction: discord.Interaction):
    if interaction.user.voice is not None:
        channel = interaction.user.voice.channel
        if interaction.guild.voice_client is None:
            await channel.connect()
            await interaction.response.send_message(f"ボイスチャンネル `{channel.name}` に参加しました。")
        else:
            await interaction.response.send_message("ボットはすでにボイスチャンネルに参加しています。")
    else:
        await interaction.response.send_message("ボイスチャンネルに参加していません。")

# VC切断コマンド
async def disc_vc(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client is not None:
        await voice_client.disconnect()
        await interaction.response.send_message("ボイスチャンネルから切断しました。")
    else:
        await interaction.response.send_message("ボットは現在、どのボイスチャンネルにも接続していません。")

# 効果音登録コマンド
async def sound_add(interaction: discord.Interaction, name: str, url: str):
    guild_id = interaction.guild.id
    try:
        file_path = download_sound_file(url, guild_id)
        execute_db_query('INSERT OR REPLACE INTO sound_effects (guild_id, name, file) VALUES (?, ?, ?)', (guild_id, name, file_path), commit=True)
        await interaction.response.send_message(f"効果音 `{name}` を登録しました。")
    except Exception as e:
        await interaction.response.send_message(f"効果音 `{name}` の登録に失敗しました: {str(e)}")

# 効果音削除コマンド
async def sound_del(interaction: discord.Interaction, name: str):
    guild_id = interaction.guild.id
    execute_db_query('DELETE FROM sound_effects WHERE guild_id = ? AND name = ?', (guild_id, name), commit=True)
    await interaction.response.send_message(f"効果音 `{name}` を削除しました。")

# 効果音一覧コマンド
async def soundlist(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    sound_list = execute_db_query('SELECT name, file FROM sound_effects WHERE guild_id = ?', (guild_id,))
    if sound_list:
        sound_list_text = "\n".join([f"{name}: {url}" for name, url in sound_list])
        await interaction.response.send_message(f"登録されている効果音:\n{sound_list_text}")
    else:
        await interaction.response.send_message("登録されている効果音はありません。")
