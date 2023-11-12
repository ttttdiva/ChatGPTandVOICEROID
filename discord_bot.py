import os
import re

import discord
import openai
from dotenv import find_dotenv, load_dotenv

from llm_manager import LLMManager

_ = load_dotenv(find_dotenv())
try:
    openai.api_key = os.environ['OPENAI_API_KEY']
    google_api_key = os.environ['google_api_key']
    cx = os.environ['cx']
    token = os.environ['Discord_TOKEN']
    text_channel = os.environ['Discord_text_channel']
except KeyError as e:
    print(f"環境変数{e}が設定されていません。")
    input()

llm_manager = LLMManager("ai_chara", "ai_dialogues", google_api_key, cx, ["琴葉葵", "葵", "あおい", "アオイ", "蒼井", "碧", "Aoi"])

class MyClient(discord.Client):
    async def on_ready(self):
        print('Discord Bot起動：', self.user)

    async def on_message(self, message):
        # don't respond to ourselves
        if message.author == self.user:
            return

        if message.content == 'ping':
            await message.channel.send('pong')

        if self.user.mentioned_in(message):
            user_name = message.author.display_name
            clean_content = re.sub(r'<@!?(\d+)> ', '', message.content)
            user_input = f"今から話しかけるユーザーの名前は「{user_name}」です。\n{clean_content}"
            print(user_input)
            return_msg = llm_manager.get_response(user_input)
            print(return_msg)
            await message.channel.send(f'{message.author.mention} {return_msg}')

    async def on_member_join(self, member):
        # メッセージを送信するテキストチャンネルを指定
        channel = self.get_channel(text_channel)
        if channel:  # チャンネルが見つかった場合
            await channel.send(f'ようこそ{member.mention}さん！')

    async def on_voice_state_update(self, member, before, after):
        if before.channel is None and after.channel is not None:
            channel = self.get_channel(text_channel)
            if channel:
                await channel.send(f'おはよう！ {member.mention}')



intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True

client = MyClient(intents=intents)
client.run(token)
