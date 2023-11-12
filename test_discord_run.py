import asyncio
import os

import discord
import openai
from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

from discord_bot import MyClient

_ = load_dotenv(find_dotenv())
try:
    openai.api_key = os.environ['OPENAI_API_KEY']
    token = os.environ['Discord_TOKEN']
except KeyError as e:
    print(f"環境変数{e}が設定されていません。")
    input()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True

client = MyClient(intents=intents)
client_openai = OpenAI()

async def run_bot():
    await client.start(token)

async def background_task():
    while True:
        # ここにバックグラウンドで実行したい処理を追加
        print("バックグラウンドタスクを実行中...")
        await asyncio.sleep(1)  # asyncio.sleepを使用して非同期に待機

loop = asyncio.get_event_loop()

# run_botをバックグラウンドで実行
bot_task = loop.create_task(run_bot())

# background_taskをバックグラウンドで実行
bg_task = loop.create_task(background_task())

try:
    loop.run_forever()
except KeyboardInterrupt:
    print("プログラムを終了します...")
finally:
    bot_task.cancel()
    bg_task.cancel()
    loop.run_until_complete(client.close())
    loop.close()