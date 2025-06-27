import threading
import pyaudio
import time
from fish_audio_sdk import Session
from loguru import logger
from . import TTSEngine

class FishAudioEngine(TTSEngine):
    """使用 Fish Audio API 的TTS引擎"""

    def __init__(self, config_manager):
        super().__init__(config_manager)
        self.api_key = self.config.get("audio.fish_audio.api_key")
        self.voice_id = self.config.get("audio.fish_audio.voice_id")
        self.session = None
        self.pyaudio_instance = None
        self.stream = None
        self.speak_thread = None

    def initialize(self):
        if not self.api_key or "your_fish_audio_api_key" in self.api_key:
            logger.warning("Fish Audio API key is not set. Fish Audio TTS will be disabled.")
            raise ValueError("Fish Audio API key not configured.")
        
        try:
            logger.info("正在连接Fish Audio服务...")
            # 创建session时可能会进行网络验证
            self.session = Session(self.api_key)
            
            # 初始化音频系统
            self.pyaudio_instance = pyaudio.PyAudio()
            
            # 简单的连接测试（可选）
            # 这里可以添加一个简单的ping测试，但现在先跳过避免阻塞
            
            logger.info("Fish Audio TTS engine initialized successfully.")
            
        except Exception as e:
            logger.error(f"Failed to initialize Fish Audio SDK: {e}")
            # 清理已创建的资源
            if self.pyaudio_instance:
                self.pyaudio_instance.terminate()
                self.pyaudio_instance = None
            raise

    def speak(self, text: str, async_mode: bool = True):
        if self._is_speaking:
            logger.warning("TTS is already speaking.")
            return

        if not self.session:
            logger.error("Fish Audio session is not initialized.")
            return

        def speak_worker():
            self._is_speaking = True
            if self.on_tts_started:
                self.on_tts_started()
            
            logger.info(f"Requesting TTS from Fish Audio for: {text[:30]}...")
            
            try:
                # 使用正确的TTS方法，添加超时处理
                start_time = time.time()
                audio_data = self.session.tts(text=text, reference_id=self.voice_id)
                request_time = time.time() - start_time
                
                logger.info(f"Received audio from Fish Audio in {request_time:.2f}s, starting playback.")
                
                # 检查音频数据
                if not audio_data:
                    logger.error("Received empty audio data from Fish Audio")
                    return
                
                self.stream = self.pyaudio_instance.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=44100,  # 通常的采样率
                    output=True
                )
                
                self.stream.write(audio_data)

            except Exception as e:
                logger.error(f"Fish Audio TTS failed: {e}")
                # 可以在这里添加重试逻辑或回退到其他TTS引擎
            finally:
                if self.stream:
                    try:
                        self.stream.stop_stream()
                        self.stream.close()
                    except Exception as e:
                        logger.error(f"Error closing audio stream: {e}")
                    finally:
                        self.stream = None
                
                self._is_speaking = False
                if self.on_tts_finished:
                    self.on_tts_finished()
                logger.info("Fish Audio playback finished.")

        if async_mode:
            self.speak_thread = threading.Thread(target=speak_worker, daemon=True)
            self.speak_thread.start()
        else:
            speak_worker()

    def stop_speaking(self):
        if self.stream and self.stream.is_active():
            try:
                self.stream.stop_stream()
            except Exception as e:
                logger.error(f"Error stopping audio stream: {e}")
        self._is_speaking = False

    def cleanup(self):
        logger.info("Cleaning up Fish Audio TTS engine...")
        self.stop_speaking()
        
        # 等待播放线程结束
        if self.speak_thread and self.speak_thread.is_alive():
            try:
                self.speak_thread.join(timeout=1.0)
            except Exception as e:
                logger.error(f"Error joining speak thread: {e}")
        
        if self.pyaudio_instance:
            try:
                self.pyaudio_instance.terminate()
            except Exception as e:
                logger.error(f"Error terminating PyAudio: {e}")
        
        logger.info("Fish Audio TTS engine cleaned up.") 