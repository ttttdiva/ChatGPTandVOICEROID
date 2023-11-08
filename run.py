#!usr/bin/env python
# -*- coding: utf-8 -*-

import os
from time import sleep

import openai
import yaml
from dotenv import find_dotenv, load_dotenv

from character_manager import CharacterManager
from llm_manager import LLMManager
from tts_manager import TTSManager
from voice_recognizer import VoiceRecognizer
from web_search import WebSearch

# 環境変数を読み込み
_ = load_dotenv(find_dotenv())
try:
    # OpenAIとGoogleのAPIキー
    openai.api_key = os.environ['OPENAI_API_KEY']
    google_api_key = os.environ['google_api_key']
    cx = os.environ['cx']
except KeyError as e:
    print(f"環境変数{e}が設定されていません。")
    input()

# 設定ファイルを読み込み
with open("config.yaml", 'r') as f:
    config = yaml.safe_load(f)

# 音声認識モデルの選択
record_moel = config['record_model']
device_index = config['device_index']
text_only = config['Text_Only']

character_manager = CharacterManager()
voice_recognizer = VoiceRecognizer(record_moel, device_index, text_only)
tts_manager = TTSManager()

def main():
    tts_manager.talk_message("起動しました！",character_manager.voice_cid)
    # try:
    while True:
        request_msg = voice_recognizer.voiceToText()
        if tts_manager.end_talk(request_msg):
            tts_manager.talk_message("さようなら！",character_manager.voice_cid)
            break

        # キャラを指定
        if any(name in request_msg for name in character_manager.all_char_names):
            # キャラの情報を取得
            ai_name, ai_chara, ai_dialogues, voice_cid, greet, tts_type = character_manager.get_character(request_msg)
            tts_manager.tts_type = tts_type
            
            # キャラプロンプトを読み込み
            llm_manager = LLMManager(ai_chara, ai_dialogues, config["llm_model"], ai_name[0])
            web_search = WebSearch(google_api_key, cx, ai_name)
            
            print(llm_manager.conversation.prompt)
            tts_manager.talk_message(greet,voice_cid)

        else:
            print("名前以外が呼ばれた")
            continue

        while True:
            # 音声認識
            voice_msg = voice_recognizer.voiceToText()

            # 特殊処理
            if tts_manager.end_talk(voice_msg):
                tts_manager.talk_message("End",voice_cid)
                print('talk終了')
                # 会話ログと要約を保存
                llm_manager.save_summary_conversation()
                tts_manager.talk_message("要約完了", voice_cid)
                
                if voice_msg in ["PCをシャットダウン", "おやすみ"]:
                    tts_manager.talk_message("おやすみなさい！",voice_cid)
                    os.system('shutdown /s /f /t 0')
                break
            elif voice_msg == "前回の続き":
                tts_manager.talk_message("ちょっと待ってね！", voice_cid)
                
                # ログファイルから前回の会話を読み込んでmessagesに追加
                llm_manager.load_previous_chat()
                voice_msg = "前回はどんなことを話していたっけ？30文字程度で教えて。"
            elif "検索して" in voice_msg:
                return_msg = web_search.bing_gpt(ai_chara, ai_dialogues, voice_msg)
                llm_manager.add_messages(voice_msg, return_msg)
                tts_manager.talk_message(return_msg, voice_cid)
                continue
            elif tts_manager.hallucination(voice_msg):
                continue

            # GPTに対して返答を求める
            return_msg = llm_manager.get_response(voice_msg)
            tts_manager.talk_message(return_msg,voice_cid)
    # except Exception as e:
    #     tts_manager.talk_message("エラーが発生しました。",character_manager.voice_cid)
    #     print('talk終了')
    #     # 会話を保存
    #     llm_manager.save_conversation(ai_name[0])
    #     print(e)


if __name__ == '__main__':
    main()