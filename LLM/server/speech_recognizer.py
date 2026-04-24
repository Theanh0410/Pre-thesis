import wave
import json
import numpy as np
from vosk import Model, KaldiRecognizer
import os
import sounddevice as sd

def speech_to_text(model_path, timeout=5, sample_rate=16000):
    try:
        model = Model(model_path)
        recognizer = KaldiRecognizer(model, sample_rate)

        print(f"Recording audio for {timeout} seconds...")
        audio = sd.rec(int(timeout * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
        sd.wait()

        # audio sang byte
        audio_data = audio.tobytes()

        # Nhận diện giọng nói
        recognizer.AcceptWaveform(audio_data)
        result = json.loads(recognizer.Result())
        text = result.get("text", "")

     
        del recognizer
        del model
        import gc
        gc.collect()

        return text

    except Exception as e:
        print(f"Error in speech_to_text: {e}")
        return ""