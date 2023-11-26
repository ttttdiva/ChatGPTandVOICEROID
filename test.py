import os
import random
import re

import discord
import openai
from dotenv import find_dotenv, load_dotenv

from character_manager import CharacterManager
from llm_manager import LLMManager
from tts_manager import TTSManager

# 環境変数を読み込み
_ = load_dotenv(find_dotenv())
try:
    openai.api_key = os.environ['OPENAI_API_KEY']
    google_api_key = os.environ['google_api_key']
    cx = os.environ['cx']
    token = "MTE3NTEzMTY0MzgyNTEwMjg3OA.G52tW4.2DtbJ4C8ZRnSlwaCKlAYfz_7UN9qgs9Q42KN1M"
    text_channel = os.environ['Discord_Text_Channel_ID']
    voice_channel = os.environ['Discord_Voice_Channel_ID']
    server_id = os.environ['Discord_Server_ID']
except KeyError as e:
    print(f"環境変数{e}が設定されていません。")
    input()

character_manager = CharacterManager()
llm_manager = LLMManager(character_manager.ai_chara, character_manager.ai_dialogues, google_api_key, cx, character_manager.ai_name)
tts_manager = TTSManager("discord", character_manager.tts_type, character_manager.voice_cid, character_manager.emo_coef, character_manager.emo_params)

intents = discord.Intents().all()
bot = discord.Bot(intents=intents)

# 起動時に特定のボイスチャンネルに接続し、読み上げる
@bot.event
async def on_ready():
    print('Discord Bot起動：', bot.user)
    # 特定のギルド（サーバー）とチャンネルでのみ動作可能
    guild = bot.get_guild(int(server_id))
    if guild:
        channel = guild.get_channel(int(voice_channel))
        if channel:
            await channel.connect()
        else:
            print("指定されたチャンネルが見つかりません。")
    else:
        print("指定されたギルド（サーバー）が見つかりません。")

# on_messageイベントのリスナー
@bot.event
async def on_message(message):
    if message.content == 'ping':
        await message.channel.send('pong')

    if "test" in message.content:
        clean_content = re.sub(r'<@!?(\d+)> ', '', message.content).replace("test","")
        voice_client = discord.utils.get(bot.voice_clients)
        tts_manager.talk_message(clean_content, None, voice_client)

    # メンションまたは5分の1でテキストチャンネルに流れたメッセージに反応
    elif bot.user.mentioned_in(message) or random.randint(0, 4) == 0:
        user_name = message.author.display_name
        user_id = message.author.id

        # don't respond to ourselves
        if message.author == bot.user:
            return

        # 通話お知らせくんからのメッセージは無視
        if user_name == "通話お知らせくん":
            return

        clean_content = re.sub(r'<@!?(\d+)> ', '', message.content)
        print(f"You said: {clean_content}")


bot.run(token)
