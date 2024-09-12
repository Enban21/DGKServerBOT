import discord
from discord import app_commands
from dotenv import load_dotenv
import os
import requests
import json
import asyncio

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

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
                print(f'コマンドをサーバー `{guild.name}` に同期しました')
            except Exception as e:
                print(f'サーバー `{guild.name}` へのコマンド同期に失敗しました: {e}')

        try:
            await self.tree.sync()
            print('グローバルコマンドを同期しました')
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

def message(
    title=None,
    description=None,
    color=discord.Color.blue(),
    footer="pappape Server System Ver.1.2.5\nDeveloped by Enban21 & pappape\nCopyright © 2024 pappape & Enban21. All rights reserved.",  # デフォルトのフッター
    author=None,
    thumbnail=None,
    image=None,
    field1=None,
    field2=None,
    field3=None
):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )

    if footer:
        embed.set_footer(text=footer)

    if author:
        embed.set_author(name=author.get("name", "Unknown"), icon_url=author.get("icon_url"))

    if thumbnail:
        embed.set_thumbnail(url=thumbnail)

    if image:
        embed.set_image(url=image)

    if field1:
        embed.add_field(name=field1["name"], value=field1["value"], inline=field1.get("inline", False))
    
    if field2:
        embed.add_field(name=field2["name"], value=field2["value"], inline=field2.get("inline", False))

    if field3:
        embed.add_field(name=field3["name"], value=field3["value"], inline=field3.get("inline", False))

    return embed
"""
この message は discord へのメッセージ送信をきれいにデザインするためのものです。
なお message を動かすだけでは送信されません。
この message は、送信前のデザインの指定を楽にするためのものです。


message() 関数が Embed メッセージを生成します。/no-use が指定されたフィールドは無視され、含めません。

message() 関数には、以下のオプションを提供しています:
    title: Embedのタイトル
    description: Embedの説明
    color: Embedの色（デフォルトは青）
    footer: フッターのテキスト
    author: 作成者の情報（辞書形式で、name と icon_url を指定可能）
    thumbnail: サムネイル画像のURL
    image: メイン画像のURL
    field1, field2, field3: 各フィールド情報（辞書形式で name と value、および inline を指定可能）

以下は使用例です:
embed_message = message(
    title="サーバー情報",
    description="以下はサーバーの詳細情報です。",
    color=discord.Color.blue(),
    footer="最終更新: 2024-08-30",
    author={"name": "pappape", "icon_url": "https://mc-status.pappape.f5.si/pappape-icon"}
    thumbnail="https://mc-status.pappape.f5.si/pappape-icon",
    image="https://example.com/server_image.png",
    field1={"name": "IPアドレス", "value": "192.168.1.1", "inline": True},
    field2={"name": "ステータス", "value": "稼働中 :green_circle:", "inline": True},
    field3={"name": "稼働時間", "value": "12時間30分", "inline": False}
)
await interaction.response.send_message(embed=embed_message, ephemeral=True) #ここでDiscordにメッセージを送信する

"""

async def check_start(interaction: discord.Interaction):
    for _ in range(180):  # 5分間のループ
        try:
            with open("status.json", "r", encoding="utf-8") as f:
                status_data = json.load(f)

            # 指定されたサーバーのステータスを確認
            server_2_status = next((server for server in status_data if server["name"] in ["Server 2 - DGK3", "Server 2 - DGK4"]), None)

            if server_2_status and server_2_status.get("status") == "動作中":
                embed_message = message(
                    title=":white_check_mark: サーバーが起動しました",
                    description="Server2 は正常に起動しました\n5分以内にサーバーに参加してください",
                    color=discord.Color.green()
                )
                await interaction.followup.send(embed=embed_message)
                return
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            embed_message = message(
                title="サーバー起動確認プログラムエラー",
                description=f":x: ステータスファイルのチェック中にエラーが発生しました: {e}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed_message)
            return
        
        await asyncio.sleep(1)  # 1秒おきにチェック

    # 5分間のチェック後、起動確認できなかった場合のメッセージ
    embed_message = message(
        title=":x: 起動の確認が取れません",
        description="サーバー2の起動が3分前にDiscordから開始されましたが、サーバーが起動されていません\n再試行する場合はもう一度 /start を実行してください",
        color=discord.Color.red()
    )
    await interaction.followup.send(embed=embed_message)

@bot.tree.command(name='start', description="サーバー2を起動します")
async def start(interaction: discord.Interaction):
    try:
        response = requests.get("https://mc-status.pappape.f5.si/wake")
        if response.status_code == 204:
            embed_message = message(
                title=":arrows_counterclockwise: 起動を開始しました",
                description="起動するまで数分かかります しばらくお待ちください\n起動が確認され次第、Discordに通知が来ます\n起動後は5分以内に接続してください 接続がない場合は自動で電源が落ちます",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed_message)
            
            await check_start(interaction)
        elif response.status_code == 500:
            embed_message = message(
                title=":x: 起動に失敗しました",
                description="もう一度お試しください\n解決しない場合は管理者までご連絡ください",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed_message)
        elif response.status_code == 429:
            embed_message = message(
                title="サーバーは現在起動中です",
                description="3分以内にサイトまたはDiscordにて起動が開始されています\nしばらくお待ちください",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed_message, ephemeral=True)
        elif response.status_code == 400:
            embed_message = message(
                title="サーバーはすでに起動しています",
                description="Server 2 は現在動作中です\n/status にて起動状況を確認できます",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed_message, ephemeral=True)
        elif response.status_code == 403:
            data = response.json()
            detailed_message = data.get('message', '現在メンテナンス中か営業を停止しています')
            embed_message = message(
                title=":x: サーバー2は現在ご利用になれません",
                description=f"{detailed_message}\n\n詳しくはDiscordサーバーやサイトを確認するか、管理者までお問い合わせください",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed_message, ephemeral=True)
        else:
            embed_message = message(
                title=":x: 起動に失敗しました",
                description="サーバーの起動に失敗しました エラー: Get Unknown ID",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed_message)
    except requests.RequestException as e:
        embed_message = message(
            title=":x: 起動に失敗しました",
            description=f"サーバーの起動に失敗しました エラー: {e}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed_message)

@bot.tree.command(name='status', description="サーバーの動作状況を表示します")
async def status(interaction: discord.Interaction):
    try:
        with open("status.json", "r", encoding="utf-8") as f:
            status_data = json.load(f)
        
        status_message = ""
        for server in status_data:
            name = server.get("name", "不明なサーバー")
            if isinstance(name, str): # HTML上での改行ができるようにしたため、Botでも同様に改行されるよう<br>を\nに置き換えます。
                name = name.replace("<br>", "\n")
            status = server.get("status", "不明")
            if isinstance(status, str):
                status = status.replace("<br>", "\n")
            players_online = server.get("players_online", "不明")
            if isinstance(players_online, str):
                players_online = players_online.replace("<br>", "\n")
            players_max = server.get("players_max", "不明")
            if isinstance(players_max, str):
                players_max = players_max.replace("<br>", "\n")
            version = server.get("version", "不明")
            if isinstance(version, str):
                version = version.replace("<br>", "\n")
            
            if status == "営業停止中":
                server_info = (
                    f"**{name}**\n"
                    f"ステータス: {status}\n"
                    f"{version}\n"
                    "\n"
                )
            elif status == "メンテナンス中":
                server_info = (
                    f"**{name}**\n"
                    f"ステータス: {status}\n"
                    f"{version}\n"
                    "\n"
                )
            elif "ポート開放状態" in name:
                server_info = (
                    f"**{name}**\n"
                    f"ステータス: {status}\n"
                    f"バージョン: {version}\n"
                    "\n"
                )
            else:
                server_info = (
                    f"**{name}**\n"
                    f"ステータス: {status}\n"
                    f"プレイヤー数: {players_online}/{players_max}\n"
                    f"バージョン: {version}\n"
                    "\n"
                )
                
            status_message += server_info
        
        embed_message = message(
            title="サーバーの動作状況",
            description=status_message,
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed_message, ephemeral=True)
    except FileNotFoundError:
        embed_message = message(
            title="エラー",
            description=":x: ステータスファイルが見つかりません",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed_message, ephemeral=True)
    except json.JSONDecodeError:
        embed_message = message(
            title="エラー",
            description=":x: ステータスファイルの読み込みに失敗しました",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed_message, ephemeral=True)

@bot.tree.command(name='help', description="コマンド一覧を表示します")
async def help_command(interaction: discord.Interaction):
    help_message = (
        "**コマンド一覧**\n\n"
        "/start: サーバー2を起動します\n"
        "/status: サーバーの動作状況を表示します\n"
        "/help: コマンド一覧を表示します"
    )
    embed_message = message(
        title="ヘルプ",
        description=help_message,
        color=discord.Color.blue(),
    )
    await interaction.response.send_message(embed=embed_message, ephemeral=True)

bot.run(TOKEN)
