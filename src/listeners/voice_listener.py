import json
import os
import queue
import threading
import time
import winsound
from typing import Optional
import numpy as np
import sounddevice as sd
from openwakeword.model import Model as OwwModel
from vosk import Model as VoskModel, KaldiRecognizer
from src.router.command_router import CommandRouter

def play_beep():
    threading.Thread(target=lambda: winsound.Beep(1200,80), daemon=True).start()

class VoiceListener:
    COMMANDS = [
        "pause", "stop",
        "resume", "play", "continue", "unpause",
        "next", "skip",
        "back", "previous",
        "[unk]"
    ]

    def __init__(
        self,
        router: CommandRouter,
        vosk_model_path: str = "model",
        wake_word_model: str = "hey_jarvis",
        wake_threshold: float = 0.15,  # 0.35 is optimal for hey_jarvis natural speech
        command_timeout: float = 4.0,
    ):
        self.router = router
        self.vosk_model_path = os.path.abspath(vosk_model_path)
        self.wake_word_model = wake_word_model
        self.wake_threshold = wake_threshold
        self.command_timeout = command_timeout

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._audio_queue: queue.Queue[bytes] = queue.Queue()
        self._enabled = True

        # State tracking: False = waiting for wake word, True = listening for command
        self._is_active = False
        self._active_start_time = 0.0

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value
        if not value:
            self._is_active = False
            while not self._audio_queue.empty():
                try:
                    self._audio_queue.get_nowait()
                except queue.Empty:
                    break

    def _audio_callback(self, indata, frames, time_info, status):
        """sounddevice callback capturing 1280-frame chunks (80ms at 16kHz)."""
        if self._running and self._enabled:
            self._audio_queue.put(bytes(indata))

    def _worker(self):
        # 1. Initialize openWakeWord with official pre-trained model
        print(f"[Voice] Initializing openWakeWord with '{self.wake_word_model}'...")
        try:
            oww = OwwModel(
                wakeword_models=[self.wake_word_model],
                inference_framework="onnx"
            )
        except Exception as e:
            print(f"[Voice] openWakeWord init error: {e}")
            print("[Voice] Run: python -c \"import openwakeword.utils; openwakeword.utils.download_models(['hey_jarvis.onnx'])\"")
            return

        # 2. Initialize Vosk
        if not os.path.exists(self.vosk_model_path):
            print(f"[Voice] ERROR: Vosk model not found at '{self.vosk_model_path}'")
            return

        print("[Voice] Loading Vosk acoustic model...")
        vosk_model = VoskModel(self.vosk_model_path)
        recognizer = KaldiRecognizer(vosk_model, 16000.0, json.dumps(self.COMMANDS))
        recognizer.SetWords(False)

        print("[Voice] Ready! Say 'Hey Jarvis' to activate, then say your command.")

        # Blocksize 1280 samples = 80ms at 16kHz
        with sd.RawInputStream(
            samplerate=16000,
            blocksize=1280,
            dtype="int16",
            channels=1,
            callback=self._audio_callback,
        ):
            while self._running:
                try:
                    raw_bytes = self._audio_queue.get(timeout=0.2)
                except queue.Empty:
                    continue

                if not self._enabled:
                    oww.reset()
                    recognizer.Reset()
                    continue

                # STATE 1: Standby -> Waiting for "Hey Jarvis"
                if not self._is_active:
                    audio_chunk = np.frombuffer(raw_bytes, dtype=np.int16)
                    oww.predict(audio_chunk)

                    score = oww.prediction_buffer[self.wake_word_model][-1]
                    if score >= self.wake_threshold:
                        self._is_active = True
                        self._active_start_time = time.time()
                        play_beep()
                        print(f"\n[Wake Word Triggered!] (Confidence: {score:.2f}) - Listening for command...")
                        recognizer.Reset()
                        oww.reset()

                # STATE 2: Awake -> Listening for Media Command
                else:
                    # Timeout back to standby if no command is heard within 4 seconds
                    if time.time() - self._active_start_time > self.command_timeout:
                        print("[Voice Timeout] Standby.\n")
                        self._is_active = False
                        recognizer.Reset()
                        continue

                    # Feed speech to Vosk
                    if recognizer.AcceptWaveform(raw_bytes):
                        result = json.loads(recognizer.Result())
                        text = result.get("text", "").strip()

                        if text and text != "[unk]":
                            print(f"[Command Executed]: '{text}'")
                            self.router.post(text)
                            self._is_active = False
                            recognizer.Reset()

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)