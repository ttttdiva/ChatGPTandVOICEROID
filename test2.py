import queue

import numpy as np
import speech_recognition as sr
import torch
import whisper


class VoiceRecognizer:
    def __init__(self):
        self.model = "large-v3"
        self.verbose = False
        self.energy = 300
        self.dynamic_energy = False
        self.pause = 0.8

        self.r = sr.Recognizer()
        self.mic = sr.Microphone(sample_rate=12000, device_index=1)
        self.r.energy_threshold = self.energy
        self.r.pause_threshold = self.pause
        self.r.dynamic_energy_threshold = self.dynamic_energy

        self.audio_model = whisper.load_model(self.model, device="cuda")
        self.audio_queue = queue.Queue()
        self.result_queue = queue.Queue()

    def recognize_whisper(self):
        verbose = self.verbose
        energy = self.energy
        dynamic_energy = self.dynamic_energy
        pause = self.pause
        audio_model = self.audio_model
        audio_queue = self.audio_queue
        result_queue = self.result_queue
        
        self.record_audio(audio_queue)
        self.transcribe_forever(audio_queue, result_queue, audio_model, verbose)
        return result_queue.get()

    def record_audio(self, audio_queue):
        r = self.r
        with self.mic as source:
            # 一回だけ音声を取得
            print("なにか話してください ...")
            audio = r.listen(source)
            torch_audio = torch.from_numpy(np.frombuffer(
                audio.get_raw_data(), np.int16).flatten().astype(np.float32) / 32768.0)
            audio_data = torch_audio
            audio_queue.put_nowait(audio_data)

    def transcribe_forever(self, audio_queue, result_queue, audio_model, verbose):
        # 一回だけ音声データを取得して処理
        audio_data = audio_queue.get()
        result = audio_model.transcribe(audio_data, language='japanese')
        if not verbose:
            predicted_text = result["text"]
            print("You said: " + predicted_text)
            result_queue.put_nowait(predicted_text)
        else:
            result_queue.put_nowait(result)

voice_recognizer = VoiceRecognizer()
while True:
    voice_recognizer.recognize_whisper()