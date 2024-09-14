import requests
import discord
import json
import asyncio
from format import message

async def check_start(interaction):
    for _ in range(180):  # 5分間のループ
        try:
            with open("status.json", "r", encoding="utf-8") as f:
                status_data = json.load(f)

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

    embed_message = message(
        title=":x: 起動の確認が取れません",
        description="サーバー2の起動が確認されていません。再試行する場合はもう一度 /start を実行してください。",
        color=discord.Color.red()
    )
    await interaction.followup.send(embed=embed_message)

async def start_server(interaction):
    try:
        response = requests.get("https://mc-status.pappape.f5.si/wake")
        if response.status_code == 204:
            embed_message = message(
                title=":arrows_counterclockwise: 起動を開始しました",
                description="サーバーが起動するまで数分かかります。",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed_message)
            await check_start(interaction)
        else:
            await handle_server_error(response, interaction)
    except requests.RequestException as e:
        embed_message = message(
            title=":x: 起動に失敗しました",
            description=f"サーバーの起動に失敗しました。エラー: {e}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed_message)

async def handle_server_error(response, interaction):
    if response.status_code == 500:
        embed_message = message(
            title=":x: 起動に失敗しました",
            description="もう一度お試しください。",
            color=discord.Color.red()
        )
    elif response.status_code == 429:
        embed_message = message(
            title="サーバーは現在起動中です",
            description="起動中ですので、しばらくお待ちください。",
            color=discord.Color.orange()
        )
    elif response.status_code == 400:
        embed_message = message(
            title="サーバーはすでに起動しています",
            description="サーバーは既に動作中です。",
            color=discord.Color.green()
        )
    else:
        embed_message = message(
            title=":x: 起動に失敗しました",
            description="サーバーの起動に失敗しました。",
            color=discord.Color.red()
        )
    await interaction.response.send_message(embed=embed_message)

async def get_server_status(interaction):
    try:
        with open("status.json", "r", encoding="utf-8") as f:
            status_data = json.load(f)
        
        status_message = ""
        for server in status_data:
            name = server.get("name", "不明なサーバー")
            status = server.get("status", "不明")
            players_online = server.get("players_online", "不明")
            players_max = server.get("players_max", "不明")
            version = server.get("version", "不明")

            server_info = (
                f"**{name}**\n"
                f"ステータス: {status}\n"
                f"プレイヤー数: {players_online}/{players_max}\n"
                f"バージョン: {version}\n\n"
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
            description="ステータスファイルが見つかりません。",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed_message, ephemeral=True)
    except json.JSONDecodeError:
        embed_message = message(
            title="エラー",
            description="ステータスファイルの読み込みに失敗しました。",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed_message, ephemeral=True)
