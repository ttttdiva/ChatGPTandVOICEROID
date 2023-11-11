import io
import os
import queue
import tempfile

import numpy as np
import speech_recognition as sr
import torch
import whisper
import yaml
from pydub import AudioSegment

from audio_transcriber import AudioTranscriber
from audio_utils import display_valid_input_devices, get_valid_input_devices


class VoiceRecognizer:
    def __init__(self):
        # 設定ファイルを読み込み
        with open("config.yaml", 'r') as f:
            config = yaml.safe_load(f)
        self.text_only = config['Text_Only']
        self.model_type = config['record_model']
        device_index = config['device_index']

        if self.text_only is True:
            return
        self.device_type(device_index)
        self.initialize_model()
    
    def initialize_model(self):
        if self.model_type == "whisper":
            self.model = "large-v3"
            self.english = False
            self.verbose = False
            self.energy = 300
            self.dynamic_energy = False
            self.pause = 0.8
            self.save_file = False
            self.temp_dir = tempfile.mkdtemp() if self.save_file else None

            self.r = sr.Recognizer()
            self.mic = sr.Microphone(sample_rate=12000, device_index=self.device_index)
            self.r.energy_threshold = self.energy
            self.r.pause_threshold = self.pause
            self.r.dynamic_energy_threshold = self.dynamic_energy

            self.audio_model = whisper.load_model(self.model, device="cuda")
            self.audio_queue = queue.Queue()
            self.result_queue = queue.Queue()
            # threading.Thread(target=record_audio,
            #                 args=(audio_queue, energy, pause, dynamic_energy, save_file, temp_dir)).start()
            # threading.Thread(target=transcribe_forever,
            #                 args=(audio_queue, result_queue, audio_model, english, verbose, save_file)).start()
        elif self.model_type == "Google Speech Recognition":
            self.r = sr.Recognizer()
            self.mic = sr.Microphone(device_index=self.device_index)
            # 使用するマイクを指定
            self.transcriber = AudioTranscriber()
        elif self.model_type == "faster-whisper":
            self.transcriber = AudioTranscriber()    
    
    def device_type(self, device_index):
        self.device_index = device_index

    def voiceToText(self):
        if self.text_only is True:
            return input("User: ")

        method_map = {
            "whisper": self.recognize_whisper,
            "google_speech": self.recognize_google_speech,
            "faster_whisper": self.recognize_faster_whisper
        }
        method = method_map[self.model_type]
        return method()


    def recognize_whisper(self):
        english = self.english
        verbose = self.verbose
        energy = self.energy
        dynamic_energy = self.dynamic_energy
        pause = self.pause
        save_file = self.save_file
        audio_model = self.audio_model
        audio_queue = self.audio_queue
        result_queue = self.result_queue
        temp_dir = self.temp_dir
        
        self.record_audio(audio_queue, energy, pause, dynamic_energy, save_file, temp_dir)
        self.transcribe_forever(audio_queue, result_queue, audio_model, english, verbose, save_file)
        return result_queue.get()

    def recognize_google_speech(self):
        r = self.r
        mic = self.mic
        while True:
            print("なにか話してください ...")
            with mic as source:
                r.adjust_for_ambient_noise(source) #ノイズ除去
                audio = r.listen(source)
            print ("認識中...")
            try:
                request_msg = r.recognize_google(audio, language='ja-JP')
                print("You said: " + request_msg)
                return request_msg
            except sr.UnknownValueError:
                return ""
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service; {e}")

    def recognize_faster_whisper(self):
        while True:
            print("なにか話してください ...")
            try:
                request_msg = self.transcriber.start_transcription(self.device_index)
                print("You said: " + request_msg)
                return request_msg
            except Exception as e:
                print(e)
                print(f"Could not request results from Faster-Whisper service; {e}")
                continue

    def record_audio(self, audio_queue, energy, pause, dynamic_energy, save_file, temp_dir):
        r = self.r
        with self.mic as source:
            # 一回だけ音声を取得
            print("なにか話してください ...")
            audio = r.listen(source)
            if save_file:
                data = io.BytesIO(audio.get_wav_data())
                audio_clip = AudioSegment.from_file(data)
                filename = os.path.join(temp_dir, "temp.wav")
                audio_clip.export(filename, format="wav")
                audio_data = filename
            else:
                torch_audio = torch.from_numpy(np.frombuffer(
                    audio.get_raw_data(), np.int16).flatten().astype(np.float32) / 32768.0)
                audio_data = torch_audio
            audio_queue.put_nowait(audio_data)

    def transcribe_forever(self, audio_queue, result_queue, audio_model, english, verbose, save_file):
        # 一回だけ音声データを取得して処理
        audio_data = audio_queue.get()
        if english:
            result = audio_model.transcribe(audio_data, language='english')
        else:
            result = audio_model.transcribe(audio_data, language='japanese')
        if not verbose:
            predicted_text = result["text"]
            print("You said: " + predicted_text)
            result_queue.put_nowait(predicted_text)
        else:
            result_queue.put_nowait(result)
        if save_file:
            os.remove(audio_data)

    # def record_audio(audio_queue, energy, pause, dynamic_energy, save_file, temp_dir):
    #     # load the speech recognizer and set the initial energy threshold and pause threshold
    #     r = sr.Recognizer()
    #     r.energy_threshold = energy
    #     r.pause_threshold = pause
    #     r.dynamic_energy_threshold = dynamic_energy
    #     # r.non_speaking_duration = 0.1
    #     # r.phrase_threshold = 0.1

    #     with sr.Microphone(sample_rate=16000) as source:
    #         i = 0
    #         while True:
    #             # get and save audio to wav file
    #             print ("認識中...")
    #             audio = r.listen(source)
    #             if save_file:
    #                 data = io.BytesIO(audio.get_wav_data())
    #                 audio_clip = AudioSegment.from_file(data)
    #                 filename = os.path.join(temp_dir, f"temp{i}.wav")
    #                 audio_clip.export(filename, format="wav")
    #                 audio_data = filename
    #             else:
    #                 torch_audio = torch.from_numpy(np.frombuffer(
    #                     audio.get_raw_data(), np.int16).flatten().astype(np.float32) / 32768.0)
    #                 audio_data = torch_audio

    #             audio_queue.put_nowait(audio_data)
    #             i += 1

    # def transcribe_forever(audio_queue, result_queue, audio_model, english, verbose, save_file):
    #     while True:
    #         audio_data = audio_queue.get()
    #         if english:
    #             result = audio_model.transcribe(audio_data, language='english')
    #         else:
    #             result = audio_model.transcribe(audio_data, language='japanese')

    #         if not verbose:
    #             predicted_text = result["text"]
    #             print("You said: " + predicted_text)
    #             result_queue.put_nowait(predicted_text)
    #         else:
    #             result_queue.put_nowait(result)

    #         if save_file:
    #             os.remove(audio_data)
