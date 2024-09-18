import os
import discord
from dotenv import load_dotenv
from discord import app_commands
from server_status import start_server, get_server_status
from format import message
from playsound import join_vc, disc_vc, sound_add, sound_del, soundlist, get_sound_file
from gtts import gTTS
import asyncio
import random

# .env ファイルから環境変数をロード
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

# デフォルトの読み上げ速度
Default_Reading_Speed = 1.2

# 必要なインテントの設定
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

class MyBot(discord.Client):
    def __init__(self, intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.my_voice_clients = {}
        self.queue = asyncio.Queue()  # メッセージキューを追加
        self.reading_speed = Default_Reading_Speed  # 初期速度
        self.user_pitches = {}  # ユーザーごとのピッチを管理する辞書

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
                while getattr(self, 'playing', False):
                    await asyncio.sleep(1)
                # 再生中の確認
                if voice_client.is_playing():
                    return
                def on_finish(_):
                    os.remove("message.mp3")
                    self.playing = False
                self.playing = True
                voice_client.play(discord.FFmpegPCMAudio(sound_file), after=on_finish)
            except Exception as e:
                await message.channel.send(f"効果音 `{message.content}` の再生に失敗しました: {str(e)}")
                on_finish()
            return

        # メッセージが音声送信チャンネルで送られた場合、読み上げ
        if message.channel.name == "読み上げbot":
            await self.queue.put(message)  # メッセージをキューに追加
            if not self.queue.empty():
                if not getattr(self, 'reading_message', False):  # 読み上げ中でなければ処理を開始
                    await self.process_queue()

    async def process_queue(self):
        self.reading_message = True
        while not self.queue.empty():
            message = await self.queue.get()
            await self.read_message_aloud(message)
            # 読み上げが完了するまで待つ
            while getattr(self, 'playing', False):
                await asyncio.sleep(1)
        self.reading_message = False

    async def announce_user_change(self, channel, user, action):
        # channel が None かどうか確認
        if channel is None:
            return  # channel が None の場合は処理を終了

        # guild と voice_client の存在を確認
        if channel.guild is None or channel.guild.voice_client is None:
            return  # voice_client がない場合も処理を終了

        """ユーザーの参加または離脱をアナウンスする"""
        if channel.guild.voice_client is None:
            print("参加アナウンスエラー: ボイスチャンネルへの参加が確認できませんでした。")
            return

        text = f"{user.name} が {action} しました"
        tts = gTTS(text=text, lang='ja')  # 日本語で読み上げ
        tts.save("announcement.mp3")

        def on_finish(_):
            os.remove("announcement.mp3")
            self.playing = False

        self.playing = True
        ffmpeg_opts = "-af 'atempo=1.4,asetrate=24000'"  # ピッチはデフォルトの1.0
        channel.guild.voice_client.play(discord.FFmpegPCMAudio("announcement.mp3", **{"options": ffmpeg_opts}), after=on_finish)


    async def on_voice_state_update(self, member, before, after):
        # ユーザーが通話を開始した場合
        if after.channel and member != self.user:
            if self.user not in after.channel.members:
                voice_client = await after.channel.connect()
                self.my_voice_clients[after.channel.id] = voice_client
                print(f'{after.channel.name} に参加しました')
                self.reading_speed = Default_Reading_Speed  # 参加時に速度リセット

            # ピッチをランダムに設定し、ユーザーごとのピッチ辞書に追加
            if member.id not in self.user_pitches:
                self.user_pitches[member.id] = random.uniform(0.6, 1.4)
                print(f"ユーザー {member.name} にピッチ {self.user_pitches[member.id]} を割り当てました")


            # 参加者アナウンス
            await self.announce_user_change(after.channel, member, "参加")

        # ユーザーが通話から離脱した場合
        if before.channel and len(before.channel.members) == 1 and self.user in before.channel.members:
            voice_client = before.channel.guild.voice_client
            if voice_client:
                await voice_client.disconnect()
                print(f'{before.channel.name} から離脱しました')

            # ピッチ辞書をクリア（通話から離脱時）
            self.user_pitches.clear()

        else:
            # 離脱者アナウンス
            await self.announce_user_change(before.channel, member, "離脱")


    async def read_message_aloud(self, message):
        text = message.content
        user_id = message.author.id

        if message.author.id not in self.user_pitches:
            self.user_pitches[message.author.id] = random.uniform(0.6, 1.4)
            print(f"ユーザー {message.author.name} にピッチ {self.user_pitches[message.author.id]} を割り当てました")

        pitch = self.user_pitches.get(user_id, random.uniform(0.6, 1.4))  # ユーザーごとのピッチを使用（なければランダム）
        speed = self.reading_speed

        try:
            tts = gTTS(text=text, lang='ja')  # 日本語で読み上げ
        except:
            return
        try:
            tts.save("message.mp3")
        except:
            return

        voice_client = message.guild.voice_client
        if voice_client is None:
            channel = message.author.voice.channel
            voice_client = await channel.connect()

        # 再生中の確認
        if voice_client.is_playing():
            return

        def on_finish(_):
            os.remove("message.mp3")
            self.playing = False

        self.playing = True
        ffmpeg_opts = f"-af 'atempo={speed},asetrate=24000*{pitch}'"
        voice_client.play(discord.FFmpegPCMAudio("message.mp3", **{"options": ffmpeg_opts}), after=on_finish)

    
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

        # ボイスチャンネルに既に参加しているユーザーにピッチを割り当てる
        for guild in self.guilds:
            for channel in guild.voice_channels:
                # チャンネルに既にメンバーがいる場合、自動的に接続する
                if channel.members:
                    voice_client = await channel.connect()
                    self.my_voice_clients[channel.id] = voice_client
                    print(f'{channel.name} に自動接続しました')

                # ピッチの割り当て
                for member in channel.members:
                    if member.id != self.user.id:
                        if member.id not in self.user_pitches:
                            self.user_pitches[member.id] = random.uniform(0.6, 1.4)
                            print(f"ユーザー {member.name} にピッチ {self.user_pitches[member.id]} を割り当てました")


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

# 読み上げ速度設定コマンド
@bot.tree.command(name="set_speed", description="読み上げ速度を設定します デフォルトは1.2です")
async def set_speed(interaction: discord.Interaction, speed: float):
    global Default_Reading_Speed
    Default_Reading_Speed = speed
    bot.reading_speed = speed
    await interaction.response.send_message(f"読み上げ速度が {speed} に設定されました")

# ヘルプコマンド
@bot.tree.command(name="help", description="ヘルプを表示します")
async def help(interaction: discord.Interaction):
    await interaction.response.send_message("コマンド一覧:\n/start - サーバー2を起動します\n/status - サーバーの動作状況を表示します\n/join - ボイスチャンネルに参加します\n/disc - ボイスチャンネルからボットが切断します\n/se_add - 効果音を登録します\n/se_del - 効果音を削除します\n/se_list - 登録されている効果音の一覧表示します\n/set_speed - 読み上げ速度を設定します デフォルトは1.2です", ephemeral=True)

# bot を起動
bot.run(TOKEN)
