import asyncio
import os
import random
import re
import time

import discord
import openai
from discord.ext import tasks
from dotenv import find_dotenv, load_dotenv

from character_manager import CharacterManager
from llm_manager import LLMManager
from tts_manager import TTSManager
from voice_recognizer import StreamingSink

# 環境変数を読み込み
_ = load_dotenv(find_dotenv())
try:
    openai.api_key = os.environ['OPENAI_API_KEY']
    google_api_key = os.environ['google_api_key']
    cx = os.environ['cx']
    token = os.environ['Discord_TOKEN']
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



async def main(voice_msg, voice_client, user_id, ctx):
    global llm_manager
    global voice_cid
    if character_manager.char_select == False:
        # キャラクター選択処理
        if tts_manager.end_talk(voice_msg):
            tts_manager.talk_message("さようなら！", None, voice_client)
            voice_client.disconnect()

        # キャラを指定
        if any(name in voice_msg for name in character_manager.all_char_names):
            ai_name, ai_chara, ai_dialogues, voice_cid, greet, tts_type, emo_coef, emo_params = character_manager.get_character(voice_msg)
            tts_manager.tts_type = tts_type
            tts_manager.voice_cid = voice_cid
            tts_manager.emo_coef = emo_coef
            tts_manager.base_emo_params = emo_params
            
            # キャラプロンプトを読み込み
            llm_manager = LLMManager(ai_chara, ai_dialogues, google_api_key, cx, ai_name)
            
            tts_manager.talk_message(greet, None, voice_client)
            await ctx.send(f"<@{user_id}> {greet}")
            character_manager.char_select = True
        else:
            print("名前以外が呼ばれた")
    else:
        # 会話メイン処理
        if tts_manager.end_talk(voice_msg):
            tts_manager.talk_message("End", None, voice_client)
            print('talk終了')
            # 会話ログと要約を保存
            end = llm_manager.end_conversation()
            if end:
                tts_manager.talk_message(end, None, voice_client) # なんで書いたか忘れた処理
            character_manager.char_select = False

            # if voice_msg in ["PCをシャットダウン", "おやすみ"]:
            #     tts_manager.talk_message("おやすみなさい！",None, voice_client)
            #     os.system('shutdown /s /f /t 0')
            return
        elif voice_msg == "前回の続き":
            tts_manager.talk_message("ちょっと待ってね！", None, voice_client)
            
            # ログファイルから前回の会話を読み込んでmessagesに追加
            llm_manager.load_previous_chat()
            voice_msg = "今までどんなことを話していたっけ？30文字程度で教えて。"
        elif "検索して" in voice_msg:
            pass
        elif tts_manager.hallucination(voice_msg):
            return

        # GPTに対して返答を求める
        user_name = await bot.fetch_user(user_id)

        # GPTに対して返答を求める
        response_data = llm_manager.get_response(voice_msg)
        if isinstance(response_data, tuple):
            return_msg, emo_params = response_data
        else:
            return_msg = response_data
            emo_params = {}

        user_input = f"私の名前は\"{user_name}\"です。\n{voice_msg}"
        return_msg = llm_manager.get_response(user_input)
        await ctx.send(f"<@{user_id}> {return_msg}")
        tts_manager.talk_message(return_msg, emo_params, voice_client)


@bot.slash_command()
async def start_record(ctx: discord.ApplicationContext):
    # ボットがボイスチャンネルに接続しているか確認
    if ctx.voice_client is None:
        if ctx.author.voice:
            vc = await ctx.author.voice.channel.connect()
        else:
            await ctx.respond("ボイスチャンネルに入ってください。")
            return
    else:
        vc = ctx.voice_client

    await ctx.respond("録音を開始します...")
    print("なにか話してください ...")

    # StreamingSinkのインスタンスを作成
    sink = StreamingSink(vc)

    # 録音を開始
    vc.start_recording(sink, finished_callback, ctx)

    await asyncio.sleep(1)

    # 定期的に音声をチェック
    check_voice_loop.start(sink, ctx)

@tasks.loop(seconds=0.8)
async def check_voice_loop(sink, ctx):
    current_time = time.time()
    if current_time - sink.last_voice_received >= 0.8:  # 0.8秒以上音声データが受信されていない場合
        if sink.is_voice_active:
            audio_file = "./temp/record.wav"
            sink.save_to_file(audio_file)
            if sink.is_voice_active:
                voice_msg = sink.transcribe_audio(audio_file)
                await main(voice_msg, sink.voice_client, sink.user, ctx)
                sink.buffer.clear()
                sink.is_voice_active = False
                print("なにか話してください ...")
            else:
                print("なにか話してください ...")
    else:
        sink.is_voice_active = True

@bot.slash_command()
async def stop_recording(ctx: discord.ApplicationContext):
    if ctx.voice_client:
        ctx.voice_client.stop_recording()
        check_voice_loop.cancel()
        await ctx.respond("録音を停止しました。")
    else:
        await ctx.respond("録音していません。")

# 録音終了時に呼び出される関数
async def finished_callback(sink:discord.sinks.MP3Sink, ctx:discord.ApplicationContext):
    pass

@bot.command(description="Botがボイスチャンネルに接続します。")
async def join(ctx):
    # ユーザーがボイスチャンネルに接続しているか確認
    if ctx.author.voice is None:
        await ctx.send("ボイスチャンネルに接続していないため、接続できません。")
        return

    channel = ctx.author.voice.channel
    # チャンネルが存在するか確認
    if channel is not None:
        # ここでBotが既にそのボイスチャンネルに接続しているかどうかを確認
        if ctx.voice_client and ctx.voice_client.channel == channel:
            await ctx.send("既にそのボイスチャンネルに接続しています。")
        else:
            await channel.connect()
    else:
        await ctx.send("ボイスチャンネルが見つかりません。")

@bot.command(description="Botがボイスチャンネルから切断します。")
async def leave(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
    else:
        await ctx.send("ボットはボイスチャンネルに接続していません。")

# 起動時に特定のボイスチャンネルに接続し、読み上げる
@bot.event
async def on_ready():
    print('Discord Bot起動：', bot.user)
    # 特定のギルド（サーバー）とチャンネルでのみ動作可能
    guild = bot.get_guild(int(server_id))
    if guild:
        channel = guild.get_channel(int(voice_channel))
        if channel:
            voice_client = await channel.connect()
            # 読み上げ
            tts_manager.talk_message("起動しました！", None, voice_client)
            # StreamingSinkのインスタンスを作成
            sink = StreamingSink(voice_client)
            ctx = bot.get_channel(int(text_channel))

            # 録音を開始
            voice_client.start_recording(sink, finished_callback, ctx)

            await asyncio.sleep(1)

            # 定期的に音声をチェック
            check_voice_loop.start(sink, ctx)
        else:
            print("指定されたチャンネルが見つかりません。")
    else:
        print("指定されたギルド（サーバー）が見つかりません。")

# on_member_joinイベントのリスナー
@bot.event
async def on_member_join(member):
    # メッセージを送信するテキストチャンネルを指定
    channel = bot.get_channel(int(text_channel))
    if channel:  # チャンネルが見つかった場合
        await channel.send(f'ようこそ{member.mention}さん！')

# on_voice_state_updateイベントのリスナー
@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is None and after.channel:
        voice_client = discord.utils.get(bot.voice_clients, guild=member.guild)
        channel = after.channel
        # ボットが既にボイスチャンネルに接続していないことを確認
        if voice_client is None or voice_client.channel != channel:
            await channel.connect()
            # StreamingSinkのインスタンスを作成
            sink = StreamingSink(voice_client)
            ctx = bot.get_channel(int(text_channel))

            # 録音を開始
            voice_client.start_recording(sink, finished_callback, ctx)

            await asyncio.sleep(1)

            # 定期的に音声をチェック
            check_voice_loop.start(sink, ctx)


# on_messageイベントのリスナー
@bot.event
async def on_message(message):
    if message.content == 'ping':
        await message.channel.send('pong')

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

        voice_client = discord.utils.get(bot.voice_clients)

        await main(clean_content, voice_client, user_id, message.channel)


bot.run(token)
