import threading
import pyttsx3
from loguru import logger
from . import TTSEngine

class Pyttsx3Engine(TTSEngine):
    """使用 pyttsx3 的本地TTS引擎"""

    def __init__(self, config_manager):
        super().__init__(config_manager)
        self.engine = None
        self.tts_rate = self.config.get("audio.tts_rate", 150)
        self.tts_volume = self.config.get("audio.tts_volume", 0.8)

    def initialize(self):
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', self.tts_rate)
            self.engine.setProperty('volume', self.tts_volume)

            voices = self.engine.getProperty('voices')
            if voices:
                chinese_voice = next((v for v in voices if 'zh' in v.id.lower() or 'chinese' in v.name.lower()), None)
                if chinese_voice:
                    self.engine.setProperty('voice', chinese_voice.id)
                    logger.info(f"Using Chinese voice for pyttsx3: {chinese_voice.name}")
                else:
                    logger.warning("No Chinese voice found for pyttsx3, using default.")
            
            logger.info("pyttsx3 TTS engine initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize pyttsx3 engine: {e}")
            raise

    def speak(self, text: str, async_mode: bool = True):
        if self._is_speaking:
            logger.warning("pyttsx3 is already speaking.")
            return

        def speak_worker():
            self._is_speaking = True
            if self.on_tts_started:
                self.on_tts_started()
            
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                logger.error(f"pyttsx3 speech failed: {e}")
            finally:
                self._is_speaking = False
                if self.on_tts_finished:
                    self.on_tts_finished()

        if async_mode:
            thread = threading.Thread(target=speak_worker, daemon=True)
            thread.start()
        else:
            speak_worker()

    def stop_speaking(self):
        if self.engine:
            self.engine.stop()

    def cleanup(self):
        logger.info("pyttsx3 TTS engine cleaned up.") 