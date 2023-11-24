import os
import re
import subprocess
from time import sleep

import psutil
import yaml

from voicevox_util import talk_voicevox_file, talk_voicevox_stream


class TTSManager:
    def __init__(self, caller, tts_type, voice_cid, emo_coef, emo_params):
        self.caller = caller
        self.tts_type = tts_type
        self.voice_cid = voice_cid
        self.emo_coef = emo_coef
        self.base_emo_params = emo_params
        self.emo_params = emo_params
        # 感情値のEMAを管理するインスタンスを作成
        self.emotion_history_ema = EmotionHistoryEMA()

        if self.caller == "local":
            pass
        elif self.caller == "discord":
            import discord
            self.discord = discord

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
    def talk_message(self, msg:str=None, emo_params:dict=None, voice_client:bytes=None, cid:int=None):
        print(f"{msg}")
        if self.text_only is True:
            return

        if emo_params == None:
            emo_params = self.base_emo_params
        else:
            # 文字列の場合はfloat型に直す
            emo_params = {emotion: float(value) for emotion, value in emo_params.items()}
            
            # 定義されている可能性のある感情のキーを含むリスト
            expected_keys = ['happy', 'sad', 'anger', 'speed', 'pitch', 'intonation']

            # 不足しているキーを確認し、存在しない場合は0.00で補完する
            for key in expected_keys:
                if key not in emo_params:
                    emo_params[key] = 0.00

            # 想定していないキーがあれば削除する
            keys_to_remove = [key for key in emo_params if key not in expected_keys]
            for key in keys_to_remove:
                del emo_params[key]

            emo_params = self.calculate_emotion_values(self.base_emo_params, emo_params, self.emo_coef)

        if cid == None:
            cid = self.voice_cid

        if self.caller == "local":
            if self.tts_type == "VOICEROID":
                self.talk_voiceroid(msg, cid, emo_params)
            elif self.tts_type == "VOICEVOX":
                talk_voicevox_stream(msg, cid, speed=1.0, pitch=0.03, intonation=2.0)
        elif self.caller == "discord":
            audio_file = "./temp/voice.wav"
            if self.tts_type == "VOICEROID":
                self.talk_voiceroid(msg, cid, emo_params, audio_file)
            elif self.tts_type == "VOICEVOX":
                talk_voicevox_file(msg, audio_file, cid, speed=1.0, pitch=0.03, intonation=2.0)

            if voice_client and voice_client.is_connected():
                audio_source = self.discord.FFmpegPCMAudio(audio_file)
                voice_client.play(audio_source)

    def talk_voiceroid(self, msg, cid, emo_params, audio_file=None):
        # emo_paramsを適切な範囲で値を収める処理
        for emotion, value in emo_params.items():
            if emotion in ['happy', 'sad', 'anger']:
                # happy, sad, anger の場合、0～1の範囲に収める
                adjusted_value = min(max(value, 0.0), 1.0)
            elif emotion in 'speed':
                # speed の場合、0.5～4の範囲に収める
                adjusted_value = min(max(value, 0.5), 4.0)
            elif emotion in 'pitch':
                # pitch の場合、0.5～2の範囲に収める
                adjusted_value = min(max(value, 0.5), 2.0)
            else:
                # intonation の場合、0～2の範囲に収める
                adjusted_value = min(max(value, 0.0), 2.0)
            
            emo_params[emotion] = round(adjusted_value, 2)

        if audio_file is None:
            # SeikaSay2.exe -cid 2158 -speed 1.35 -pitch 1.1 -intonation 1.6 -emotion "喜び" 0.65 -t "おはよう！"
            # subprocess.run(f"{self.SeikaSay2} -cid {cid} -t \"{msg}\"")
            print(emo_params)
            subprocess.run(f"{self.SeikaSay2} -cid {cid} -speed {emo_params['speed']} -pitch {emo_params['pitch']} -intonation {emo_params['intonation']} -emotion '喜び' {emo_params['happy']} -emotion '怒り' {emo_params['anger']} -emotion '悲しみ' {emo_params['sad']} -t \"{msg}\"")
        else:
            # subprocess.run(f"{self.SeikaSay2} -cid {cid} -save {audio_file} -t \"{msg}\"")
            print(emo_params)
            subprocess.run(f"{self.SeikaSay2} -cid {cid} -speed {emo_params['speed']} -pitch {emo_params['pitch']} -intonation {emo_params['intonation']} -emotion '喜び' {emo_params['happy']} -emotion '怒り' {emo_params['anger']} -emotion '悲しみ' {emo_params['sad']} -save \"{audio_file}\" -t \"{msg}\"")

    # 会話を終了する
    def end_talk(self, voice_msg):
        pattern = "^(会話.?終了.?|対話.?終了.?|ストップ|エンド|PCをシャットダウン|おやすみ)$"
        if re.search(pattern, voice_msg):
            return True
        else:
            return False

    # 無言時に発生する幻聴をスルー
    def hallucination(self, voice_msg):
        pattern = "^(ご視聴ありがとうございました.?|ありがとうございました.?|バイバイ| |)$"
        if re.search(pattern, voice_msg):
            return True
        else:
            return False

    # 新しい感情値を計算してEMAを更新する関数
    def calculate_emotion_values(self, base_emo_params, dynamic_emo_params, emo_coef):
        combined_values = {}
        
        # ベースの感情値と動的感情値を組み合わせる
        for emotion, base_value in base_emo_params.items():
            dynamic_value = dynamic_emo_params.get(emotion, 0) * emo_coef
            combined_value = base_value + dynamic_value
            combined_values[emotion] = combined_value

        # EMAを更新して最新の感情値を取得
        ema_values = self.emotion_history_ema.update_ema(combined_values)

        # 最終的な感情値を調整（小数点の制御）
        final_emotion_values = {emotion: round(value, 2) for emotion, value in ema_values.items()}
        return final_emotion_values

# 感情値の移動指数平均を取得
class EmotionHistoryEMA:
    def __init__(self, smoothing_factor=0.65):
        self.smoothing_factor = smoothing_factor
        self.ema_values = {}

    def update_ema(self, current_values):
        if not self.ema_values:  # 初回の場合は現在の値をそのまま使用
            self.ema_values = current_values
            return self.ema_values

        updated_ema = {}
        for emotion, current_value in current_values.items():
            previous_ema = self.ema_values.get(emotion, current_value)
            new_ema = self.smoothing_factor * current_value + (1 - self.smoothing_factor) * previous_ema
            updated_ema[emotion] = round(new_ema, 2)  # 小数点第2位で切り捨て

        self.ema_values = updated_ema
        return updated_ema

