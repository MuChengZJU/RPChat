import threading
import pyttsx3
import subprocess
import os
from loguru import logger
from . import TTSEngine

class Pyttsx3Engine(TTSEngine):
    """使用 pyttsx3 的本地TTS引擎"""

    def __init__(self, config_manager):
        super().__init__(config_manager)
        self.engine = None
        self.tts_rate = self.config.get("audio.tts_rate", 150)
        self.tts_volume = self.config.get("audio.tts_volume", 0.8)
        self.output_device_index = self.config.get("audio.output_device_index", -1)

    def initialize(self):
        try:
            # 首先确保USB扬声器是默认设备
            self._set_usb_speaker_as_default()
            
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

    def _set_usb_speaker_as_default(self):
        """设置USB扬声器为默认音频输出设备"""
        try:
            # 检查并设置USB扬声器为默认设备
            result = subprocess.run(['pactl', 'list', 'short', 'sinks'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if 'usb' in line.lower() and 'audio' in line.lower():
                        # 提取设备名称
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            device_name = parts[1]
                            # 设置为默认设备
                            subprocess.run(['pactl', 'set-default-sink', device_name], 
                                         timeout=5, check=False)
                            logger.info(f"Set USB speaker as default: {device_name}")
                            break
        except Exception as e:
            logger.warning(f"Failed to set USB speaker as default: {e}")

    def speak(self, text: str, async_mode: bool = True):
        if self._is_speaking:
            logger.warning("pyttsx3 is already speaking.")
            return

        def speak_worker():
            self._is_speaking = True
            if self.on_tts_started:
                self.on_tts_started()
            
            try:
                # 确保音频路由正确
                self._ensure_audio_routing()
                
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

    def _ensure_audio_routing(self):
        """确保音频正确路由到USB扬声器"""
        try:
            # 检查当前默认音频设备
            result = subprocess.run(['pactl', 'info'], capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Default Sink:' in line:
                        if 'usb' not in line.lower():
                            # 重新设置USB扬声器为默认
                            self._set_usb_speaker_as_default()
                        break
        except Exception as e:
            logger.warning(f"Failed to check audio routing: {e}")

    def stop_speaking(self):
        if self.engine:
            self.engine.stop()

    def cleanup(self):
        logger.info("pyttsx3 TTS engine cleaned up.") 