import os
import re
import subprocess
from time import sleep

import psutil
import yaml

from voicevox_util import talk_voicevox


class TTSManager:
    def __init__(self):
        # 設定ファイルを読み込み
        with open("config.yaml", 'r') as f:
            config = yaml.safe_load(f)
        self.text_only = config['Text_Only']
        self.Assistant_Seika_flag = config['tts_settings']['Assistant_Seika_flag']
        self.Assistant_Seika = os.path.expandvars(config['tts_settings']['Assistant_Seika'])
        self.Assistant_Seika_path = os.path.expandvars(config['tts_settings']['Assistant_Seika_path'])
        self.SeikaSay2 = os.path.expandvars(config['tts_settings']['SeikaSay2'])
        self.SeikaCtl = os.path.expandvars(config['tts_settings']['SeikaCtl'])
        
        self.VOICEROID = os.path.expandvars(config['tts_settings']['VOICEROID'])
        self.VOICEVOX = os.path.expandvars(config['tts_settings']['VOICEVOX'])

        self.tts_type = "VOICEVOX"

        self.wakeup_app()

    def wakeup_app(self):
        # 現在実行中のプロセス一覧を取得
        running_processes = [p.name() for p in psutil.process_iter()]

        # VOICEVOX が実行中かどうかを判定
        parts = self.VOICEVOX.split("\\")
        last_part = parts[-1].replace("\"","")
        if last_part in running_processes:
            print("VOICEVOX.exe は実行中です。")
        else:
            subprocess.Popen(self.VOICEVOX)

        # AssistantSeika.exe が実行中かどうかを判定
        parts = self.Assistant_Seika.split("\\")
        last_part = parts[-1].replace("\"","")
        if last_part in running_processes:
            print("AssistantSeika.exe は実行中です。")
        else:
            if self.Assistant_Seika_flag == False:
                pass
            else:
                # 実行中でなければ起動
                print("AssistantSeika.exe は実行されていません。")
                subprocess.Popen(f"{self.SeikaCtl} boot {self.Assistant_Seika_path}")
                subprocess.Popen(self.VOICEROID)
                subprocess.run(f"{self.SeikaCtl} waitboot 60")
                sleep(15)
                subprocess.run(f"{self.SeikaCtl} prodscan")

    # メッセージを喋らせる
    def talk_message(self, msg:str, cid:int):
        print(f"「{msg}」")
        if self.text_only is True:
            return
        
        if self.tts_type == "VOICEROID":
            subprocess.run(f"{self.SeikaSay2} -cid {cid} -t \"{msg}\"")
        elif self.tts_type == "VOICEVOX":
            talk_voicevox(msg, cid, speed=1.0, pitch=0.03, intonation=2.0)

    # 会話を終了する
    def end_talk(self, voice_msg):
        pattern = "^(会話.?終了.?|対話.?終了.?|ストップ|エンド|PCをシャットダウン|おやすみ)$"
        if re.search(pattern, voice_msg):
            return True
        else:
            return False

    # 無言時に発生する幻聴をスルー
    def hallucination(self, voice_msg):
        pattern = "^(ご視聴ありがとうございました.?|ありがとうございました.?|バイバイ|)$"
        if re.search(pattern, voice_msg):
            return True
        else:
            return False
