import json
import re
import time

import pyaudio
import requests


def adjust_voice_parameters(query_data, speed, pitch, intonation):
    """
    話速、ピッチ、抑揚のパラメータを調整します。

    :param speed_scale: 話速のスケール係数。0.5～2.0まで設定可能（1.0がデフォルト）
    :param pitch_scale: ピッチのスケール係数-0.15～0.15まで設定可能（0がデフォルト）
    :param intonation_scale: 抑揚のスケール係数0～2.0まで設定可能（1.0がデフォルト）
    """
    query_data['speedScale'] = speed
    query_data['pitchScale'] = pitch
    query_data['intonationScale'] = intonation

    return query_data

def audio_query(text, speaker, max_retry):
    # 音声合成用のクエリを作成する
    query_payload = {"text": text, "speaker": speaker}
    for query_i in range(max_retry):
        r = requests.post("http://127.0.0.1:50021/audio_query", 
                        params=query_payload, timeout=(10.0, 300.0))
        if r.status_code == 200:
            query_data = r.json()
            break
    else:
        raise ConnectionError("リトライ回数が上限に到達しました。 audio_query : ", "/", text[:30], r.text)
    return query_data

def synthesis(speaker, query_data, max_retry):
    # 音声ファイルを生成する
    synth_payload = {"speaker": speaker,}
    for synth_i in range(max_retry):
        r = requests.post("http://127.0.0.1:50021/synthesis", params=synth_payload, 
                            data=json.dumps(query_data), timeout=(10.0, 300.0))
        if r.status_code == 200:
            #音声ファイルを返す
            return r.content
    else:
        raise ConnectionError("音声エラー：リトライ回数が上限に到達しました。 synthesis : ", r)

def talk_voicevox(texts, speaker=4, speed=1.0, pitch=0, intonation=1.0, max_retry=20):
    # 音声ファイルを読み上げる
    if not texts:
        texts = "ちょっと、通信状態悪いかも？"
    texts = re.split("(?<=！|。|？)", texts)
    for text in texts:
        if text:  # 空のテキストをスキップ
            # audio_query
            query_data = audio_query(text, speaker, max_retry)
            # 話速、音高、抑揚を設定
            query_data = adjust_voice_parameters(query_data, speed, pitch, intonation)
            # synthesis
            voice_data = synthesis(speaker, query_data, max_retry)
            # 音声の再生
            p = pyaudio.PyAudio()
            # Open the stream
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)
            # 再生を少し遅らせる（開始時ノイズが入るため）
            time.sleep(0.2) # 0.2秒遅らせる
            # Play the stream
            stream.write(voice_data)
            # Close the stream
            stream.stop_stream()
            stream.close()
            p.terminate()