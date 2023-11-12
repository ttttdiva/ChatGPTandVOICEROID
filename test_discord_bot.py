import os
import time

import discord
import openai
from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

_ = load_dotenv(find_dotenv())
try:
    # openai.api_key = os.environ['OPENAI_API_KEY']
    # token = os.environ['Discord_TOKEN']
    text_channel = os.environ['Discord_text_channel']
except KeyError as e:
    print(f"環境変数{e}が設定されていません。")
    input()

client_openai = OpenAI()

# アシスタントリストを取得して特定のアシスタントIDを見つける
assistant_list = client_openai.beta.assistants.list(
    order="desc",
    limit=100
)
assistant_id = None
for assistant in assistant_list.data:
    if assistant.name == "琴葉葵":
        assistant_id = assistant.id
        break

thread = client_openai.beta.threads.create()

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
            user_input = message.content.replace("@Aoi ", "")
            
            client_openai.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_input,
            )

            run = client_openai.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant.id,
            )

            while True:
                run = client_openai.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                print(run.status)
                if run.status == "completed":
                    break
                time.sleep(1)

            messages = client_openai.beta.threads.messages.list(
                thread_id=thread.id
            )

            return_msg = messages.data[0].content[0].text.value
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



# intents = discord.Intents.default()
# intents.members = True
# intents.message_content = True
# intents.voice_states = True

# client = MyClient(intents=intents)
# client.run(token)
