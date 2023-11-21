import asyncio
import os
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
tts_manager = TTSManager("discord", character_manager.tts_type)

intents = discord.Intents().all()
bot = discord.Bot(intents=intents)









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
    sink = StreamingSink(vc, ctx)

    # 録音を開始
    vc.start_recording(sink, finished_callback, ctx)

    await asyncio.sleep(1)

    # 定期的に音声をチェック
    check_voice_loop.start(sink)

@tasks.loop(seconds=0.8)
async def check_voice_loop(sink):
    # print("Checking voice...")
    current_time = time.time()
    if current_time - sink.last_voice_received >= 0.8:  # 0.8秒以上音声データが受信されていない場合
        # print("No sound detected for 1 second.")
        if sink.is_voice_active:
            # print("Voice End!")
            audio_file = "./temp/record.wav"
            sink.save_to_file(audio_file)
            if sink.voice_data:
                voice_msg = sink.transcribe_audio()
                await main(sink, voice_msg)
                sink.buffer.clear()
                sink.is_voice_active = False
                print("なにか話してください ...")
            else:
                print("なにか話してください ...")
        # else:
            # print("No Sound")
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






async def main(sink, voice_msg):
    if sink.char_select == False:
        if tts_manager.end_talk(voice_msg):
            tts_manager.talk_message("さようなら！", character_manager.voice_cid, sink.voice_client)
            sink.voice_client.disconnect()

        # キャラを指定
        if any(name in voice_msg for name in character_manager.all_char_names):
            # キャラの情報を取得
            sink.ai_name, sink.ai_chara, sink.ai_dialogues, sink.voice_cid, greet, tts_type = character_manager.get_character(voice_msg)
            tts_manager.tts_type = tts_type
            
            # キャラプロンプトを読み込み
            sink.llm_manager = LLMManager(sink.ai_chara, sink.ai_dialogues, google_api_key, cx, sink.ai_name)
            
            tts_manager.talk_message(greet, sink.voice_cid, sink.voice_client)
            sink.char_select = True
        else:
            print("名前以外が呼ばれた")
    else:
        # 特殊処理
        if tts_manager.end_talk(voice_msg):
            tts_manager.talk_message("End", sink.voice_cid, sink.voice_client)
            print('talk終了')
            # 会話ログと要約を保存
            end = sink.llm_manager.end_conversation()
            if end:
                tts_manager.talk_message(end, sink.voice_cid, sink.voice_client) # なんで書いたか忘れた処理
            sink.char_select = False

            if voice_msg in ["PCをシャットダウン", "おやすみ"]:
                tts_manager.talk_message("おやすみなさい！",sink.voice_cid, sink.voice_client)
                os.system('shutdown /s /f /t 0')
            return
        elif voice_msg == "前回の続き":
            tts_manager.talk_message("ちょっと待ってね！", sink.voice_cid. sink.voice_client)
            
            # ログファイルから前回の会話を読み込んでmessagesに追加
            sink.llm_manager.load_previous_chat()
            voice_msg = "今までどんなことを話していたっけ？30文字程度で教えて。"
        elif "検索して" in voice_msg:
            return_msg = sink.llm_manager.get_response(voice_msg)
            tts_manager.talk_message(return_msg, sink.voice_cid, sink.voice_client)
            await sink.ctx.send(f"<@{sink.user}> {return_msg}")
            return
        elif tts_manager.hallucination(voice_msg):
            return

        # GPTに対して返答を求める
        return_msg = sink.llm_manager.get_response(voice_msg)
        tts_manager.talk_message(return_msg, sink.voice_cid, sink.voice_client)
        await sink.ctx.send(f"<@{sink.user}> {return_msg}")















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
            tts_manager.talk_message("起動しました！", character_manager.voice_cid, voice_client)
        else:
            print("指定されたチャンネルが見つかりません。")
    else:
        print("指定されたギルド（サーバー）が見つかりません。")

# on_member_joinイベントのリスナー
@bot.event
async def on_member_join(member):
    # メッセージを送信するテキストチャンネルを指定
    channel = bot.get_channel(text_channel)
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

# on_messageイベントのリスナー
@bot.event
async def on_message(message):
    # don't respond to ourselves
    if message.author == bot.user:
        return

    if message.content == 'ping':
        await message.channel.send('pong')

    elif bot.user.mentioned_in(message):
        # 通話お知らせくんからのメッセージは無視
        if message.author.display_name == "通話お知らせくん":
            return
        user_name = message.author.display_name
        clean_content = re.sub(r'<@!?(\d+)> ', '', message.content)
        user_input = f"私の名前は\"{user_name}\"です。\n{clean_content}"
        print(user_input)
        return_msg = llm_manager.get_response(user_input)
        print(return_msg)
        await message.channel.send(f'{message.author.mention} {return_msg}')

        # 読み上げ
        voice_client = discord.utils.get(bot.voice_clients)
        tts_manager.talk_message(return_msg, character_manager.voice_cid, voice_client)




bot.run(token)
