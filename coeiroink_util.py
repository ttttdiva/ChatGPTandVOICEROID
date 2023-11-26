import json
import re
import time
import wave

import discord
import numpy as np
import pyaudio
import requests


def adjust_voice_parameters(text, speaker, speaker_uuid, emo_params, volume):
    """
    話速、ピッチ、抑揚のパラメータを調整します。

    :param speed_scale: 話速のスケール係数。0.5～2.0まで設定可能（1.0がデフォルト）
    :param pitch_scale: ピッチのスケール係数-0.15～0.15まで設定可能（0がデフォルト）
    :param intonation_scale: 抑揚のスケール係数0～2.0まで設定可能（1.0がデフォルト）
    """

    payload = {
        "speakerUuid": speaker_uuid,
        "styleId": speaker,
        "text": text,
        "speedScale": emo_params["speed"],
        "volumeScale": volume,
        "pitchScale": emo_params["pitch"],
        "intonationScale": emo_params["intonation"],
        "prePhonemeLength": 0,
        "postPhonemeLength": 0,
        "outputSamplingRate": 24000
    }

    return payload

def get_speaker_uuid_from_style_id(style_id):
    r = requests.post(f"http://127.0.0.1:50032/v1/style_id_to_speaker_meta?styleId={style_id}")
    if r.status_code == 200:
        data = r.json()
        return data.get("speakerUuid")
    else:
        raise Exception("Failed to get speaker UUID: ", r.text)

def synthesis(query_data, max_retry):
    # 音声ファイルを生成する
    for synth_i in range(max_retry):
        r = requests.post("http://127.0.0.1:50032/v1/synthesis", json=query_data)
        if r.status_code == 200:
            #音声ファイルを返す
            return r.content
    else:
        raise ConnectionError("音声エラー：リトライ回数が上限に到達しました。 synthesis : ", r)

def select_voice_preset(emo_params, speaker):
    if emo_params == None:
        emo_params =  {'speed': 1, 'pitch': 0, 'intonation': 1}
        return emo_params, speaker
    params_copy = emo_params.copy()
    params_copy.pop('speed', None)
    params_copy.pop('pitch', None)
    params_copy.pop('intonation', None)

    
    # 指定された speaker の値に応じて voice_presets を代入
    # ナコ(MANA)
    if speaker in [1, 7, 40, 45, 41, 42, 43, 44]:
        voice_presets = {'happy': 40, 'anger': 44, 'sad': 42}
    # レコ(つくよみちゃん)
    elif speaker in [0, 5, 6]:
        voice_presets = {'happy': 6, 'anger': 0, 'sad': 5}
    # クロワ
    elif speaker in [110, 111, 112]:
        voice_presets = {'happy': 112, 'anger': 111, 'sad': 112}
    # 不明の場合はそのまま返す
    else:
        return emo_params, speaker

    # 最も高い感情値を持つ感情を見つける
    max_emo = max(params_copy, key=params_copy.get)

    # 感情値が1.5以上の場合のみボイスプリセットを反映
    if float(params_copy[max_emo]) >= 0.7:
        return emo_params, voice_presets.get(max_emo, speaker)
    else:
        return emo_params, speaker  # デフォルト

def trim_wav(file_path, trim_start_seconds=0.09):
    with wave.open(file_path, 'rb') as wav_file:
        frame_rate = wav_file.getframerate()
        n_channels = wav_file.getnchannels()
        samp_width = wav_file.getsampwidth()
        
        # スタート位置をフレーム単位で計算
        start_frame = int(frame_rate * trim_start_seconds)

        # 全体のフレーム数を取得し、トリムするフレーム数を引く
        n_frames = wav_file.getnframes() - start_frame

        # スタート位置までファイルを読み進める
        wav_file.setpos(start_frame)

        # 残りのフレームを読み込む
        frames = wav_file.readframes(n_frames)

    # 新しいファイルに書き込む
    with wave.open(file_path, 'wb') as output_wav:
        output_wav.setnchannels(n_channels)
        output_wav.setsampwidth(samp_width)
        output_wav.setframerate(frame_rate)
        output_wav.writeframes(frames)

def talk_coeiroink(texts, speaker, emo_params=None, audio_file=None, voice_client=None):
    if not texts:
        texts = "ちょっと、通信状態悪いかも？"

    if audio_file:
        volume = 2.0
    else:
        volume = 1.3

    emo_params, speaker = select_voice_preset(emo_params, speaker)

    max_retry = 20
    texts = re.split("(?<=！|。|？)", texts)
    for text in texts:
        if text:
            speaker_uuid = get_speaker_uuid_from_style_id(speaker)
            query_data = adjust_voice_parameters(text, speaker, speaker_uuid, emo_params, volume)
            voice_data = synthesis(query_data, max_retry)

            if audio_file:
                with wave.open(audio_file, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(24000)
                    wf.writeframes(voice_data)
                trim_wav(audio_file)

                # 現在の音声再生が終了するのを待つ
                while voice_client.is_playing():
                    time.sleep(1)  # 1秒間隔で再生状態を確認
                if voice_client and voice_client.is_connected():
                    audio_source = discord.FFmpegPCMAudio(audio_file)
                    voice_client.play(audio_source)
            else:
                p = pyaudio.PyAudio()
                stream = p.open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)
                time.sleep(0.2)
                stream.write(voice_data)
                stream.stop_stream()
                stream.close()
                p.terminate()
