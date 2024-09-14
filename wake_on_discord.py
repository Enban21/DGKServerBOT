import os
import discord
from dotenv import load_dotenv
from discord import app_commands
from server_status import start_server, get_server_status
from format import message
from playsound import join_vc, disc_vc, sound_add, sound_del, soundlist, get_sound_file

# .env ファイルから環境変数をロード
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

# 必要なインテントの設定
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

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
    
    async def on_message(self, message):
        if message.author == self.user:
            return

        guild_id = message.guild.id
        # get_sound_fileを呼び出して効果音ファイルを取得
        sound_file = get_sound_file(guild_id, message.content)

        if sound_file:
            voice_client = message.guild.voice_client

            if voice_client is None:
                if message.author.voice:
                    channel = message.author.voice.channel
                    voice_client = await channel.connect()
                else:
                    await message.channel.send("ボイスチャンネルに接続してください。")
                    return

            try:
                voice_client.play(discord.FFmpegPCMAudio(sound_file))
            except Exception as e:
                await message.channel.send(f"効果音 `{message.content}` の再生に失敗しました: {str(e)}")


# bot を作成
bot = MyBot(intents=intents)

# コマンド定義
@bot.tree.command(name='start', description="サーバー2を起動します")
async def start(interaction: discord.Interaction):
    await start_server(interaction)

@bot.tree.command(name='status', description="サーバーの動作状況を表示します")
async def status(interaction: discord.Interaction):
    await get_server_status(interaction)

@bot.tree.command(name="join", description="ボイスチャンネルに参加します")
async def join(interaction: discord.Interaction):
    await join_vc(interaction)

# VC切断コマンド
@bot.tree.command(name="disc", description="ボイスチャンネルからボットが切断します")
async def disc(interaction: discord.Interaction):
    await disc_vc(interaction)

# 効果音登録コマンド
@bot.tree.command(name="se_add", description="効果音を登録します")
async def se_add(interaction: discord.Interaction, name: str, url: str):
    await sound_add(interaction, name, url)

# 効果音削除コマンド
@bot.tree.command(name="se_del", description="効果音を削除します")
async def se_del(interaction: discord.Interaction, name: str):
    await sound_del(interaction, name)

# 効果音一覧コマンド
@bot.tree.command(name="se_list", description="登録されている効果音の一覧表示します")
async def se_view(interaction: discord.Interaction):
    await soundlist(interaction)

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

# bot の起動
bot.run(TOKEN)
