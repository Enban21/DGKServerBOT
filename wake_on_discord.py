import discord
from discord import app_commands
from dotenv import load_dotenv
import os
import requests
import time
import json

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
COOLDOWN_PERIOD = 180  # 180秒のクールダウン期間
last_pressed_time = 0

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

class MyBot(discord.Client):
    def __init__(self, intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        for guild in self.guilds:
            try:
                await self.tree.sync(guild=guild)
                print(f'コマンドをサーバー `{guild.name}` に同期しました。')
            except Exception as e:
                print(f'サーバー `{guild.name}` へのコマンド同期に失敗しました。: {e}')

        try:
            await self.tree.sync()
            print('グローバルコマンドを同期しました。')
        except Exception as e:
            print(f'グローバルコマンドの同期に失敗しました: {e}')

    async def on_ready(self):
        print('ログインしました')
        new_activity = discord.Game(name="DGKサーバー")
        await self.change_presence(activity=new_activity)

        try:
            commands = await self.tree.fetch_commands()
            print('登録されているコマンド:')
            for command in commands:
                print(f' - {command.name}')
        except Exception as e:
            print(f'コマンドの取得に失敗しました: {e}')

bot = MyBot(intents=intents)

@bot.tree.command(name='start', description="サーバー2を起動します。")
async def start(interaction: discord.Interaction):
    global last_pressed_time
    current_time = time.time()

    if current_time - last_pressed_time < COOLDOWN_PERIOD:
        await interaction.response.send_message(":clock4: 起動クールタイム中です。", ephemeral=True)
        return

    try:
        response = requests.get("https://mc-status.pappape.f5.si/wake")
        if response.status_code == 204:
            last_pressed_time = current_time
            await interaction.response.send_message(":white_check_mark: サーバー2を起動しました。",)
            return 204,
        elif response.status_code == 500:
            await interaction.response.send_message(":x: サーバーの起動に失敗しました。",)
            return 500,
        else:
            await interaction.response.send_message(":x: サーバーの起動に失敗しました。",)
    except requests.RequestException as e:
        await interaction.response.send_message(f":x: サーバーの起動に失敗しました。エラー: {e}",)

'''
-----サーバー起動関数について-----
現状サーバーが起動した状態でBOTを終了すると、"last_pressed_time"の値が消えてしまうため
/startを実行すると、":clock4: 起動クールタイム中です。" ではなく":x: サーバーの起動に失敗しました。"と表示される。

'''


@bot.tree.command(name='status', description="サーバーの動作状況を表示します。")
async def status(interaction: discord.Interaction):
    try:
        with open("status.json", "r", encoding="utf-8") as f:
            status_data = json.load(f)
        
        status_message = ""
        for server in status_data:
            name = server.get("name", "不明なサーバー")
            status = server.get("status", "不明")
            players = server.get("players", "不明")
            status_message += f"{name}：'{status}' プレイヤー：{players}\n"
        
        await interaction.response.send_message(f"サーバーの動作状況:\n{status_message}", ephemeral=True)
    except FileNotFoundError:
        await interaction.response.send_message(":x: ステータスファイルが見つかりません。", ephemeral=True)
    except json.JSONDecodeError:
        await interaction.response.send_message(":x: ステータスファイルの読み込みに失敗しました。", ephemeral=True)

@bot.tree.command(name='help', description="コマンド一覧を表示します。", )
async def help_command(interaction: discord.Interaction):
    help_message = (
        "**コマンド一覧**\n\n"
        "/start: サーバー2を起動します。\n"
        "/status: サーバーの動作状況を表示します。\n"
        "/help: コマンド一覧を表示します。"
    )
    await interaction.response.send_message(help_message, ephemeral=True)

bot.run(TOKEN)
