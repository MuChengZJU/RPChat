"""
语音处理模块
实现语音识别和TTS（文本转语音）功能
"""

import asyncio
import threading
import time
from typing import Optional, Callable, List
from dataclasses import dataclass
from pathlib import Path

import speech_recognition as sr
import pyaudio
from loguru import logger

from core.tts.pyttsx3_engine import Pyttsx3Engine
from core.tts.fish_audio_engine import FishAudioEngine
from utils.audio_utils import suppress_alsa_errors


@dataclass
class AudioDevice:
    """音频设备信息"""
    index: int
    name: str
    channels: int
    sample_rate: int
    is_input: bool


class VoiceRecognitionError(Exception):
    """语音识别异常"""
    pass


class TTSError(Exception):
    """TTS异常"""
    pass


class VoiceHandler:
    """语音处理器"""
    
    def __init__(self, config_manager):
        """
        初始化语音处理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config = config_manager
        
        # 语音识别配置
        self.recognition_enabled = self.config.get("audio.speech_recognition_enabled", True)
        self.recognition_language = self.config.get("audio.recognition_language", "zh-CN")
        self.recognition_timeout = int(self.config.get("audio.recognition_timeout", 5))
        self.phrase_time_limit = int(self.config.get("audio.recognition_phrase_time_limit", 30))
        
        # TTS配置
        self.tts_enabled = self.config.get("audio.tts_enabled", True)
        self.tts_engine_name = self.config.get("audio.tts_engine", "espeak")
        
        # 音频设备配置 (确保转换为整数)
        self.input_device_index = int(self.config.get("audio.input_device_index", -1))
        self.output_device_index = int(self.config.get("audio.output_device_index", -1))
        
        # 组件初始化
        self.recognizer = None
        self.microphone = None
        self.tts_engine = None
        self._is_listening = False
        self._listen_thread = None
        self._stop_listening_event = None
        self._microphone_lock = threading.Lock()
        
        # 回调函数
        self.on_speech_recognized: Optional[Callable[[str], None]] = None
        self.on_speech_error: Optional[Callable[[str], None]] = None
        self.on_tts_started: Optional[Callable[[], None]] = None
        self.on_tts_finished: Optional[Callable[[], None]] = None
        self.on_listening_stopped: Optional[Callable[[], None]] = None
        
        logger.info("语音处理器初始化完成")
    
    def initialize(self):
        """初始化语音组件"""
        logger.debug("开始初始化语音组件...")
        try:
            if self.recognition_enabled:
                logger.debug("正在初始化语音识别...")
                self._init_speech_recognition()
            
            if self.tts_enabled:
                logger.debug("正在初始化TTS引擎...")
                self._init_tts_engine()
            
            logger.info("语音组件初始化成功")
            
        except Exception as e:
            logger.error(f"语音组件初始化失败: {e}")
            logger.exception("语音组件初始化失败的完整堆栈信息：")
            raise
    
    def _init_speech_recognition(self):
        """初始化语音识别"""
        try:
            logger.debug("开始初始化 speech_recognition.Recognizer...")
            with suppress_alsa_errors():
                self.recognizer = sr.Recognizer()
            logger.debug("speech_recognition.Recognizer 初始化成功.")

            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
            
            device_index = None if self.input_device_index == -1 else self.input_device_index
            logger.debug(f"准备初始化 sr.Microphone, device_index: {device_index}")
            with suppress_alsa_errors():
                self.microphone = sr.Microphone(device_index=device_index)
            logger.debug("sr.Microphone 初始化成功.")
            
            with self.microphone as source:
                logger.info("正在校准环境噪音(最多5秒)...")
                self.recognizer.adjust_for_ambient_noise(source, duration=5)
            
            logger.info(f"语音识别初始化完成 - 语言: {self.recognition_language}")
            
        except Exception as e:
            logger.error(f"语音识别初始化失败: {e}")
            logger.exception("语音识别初始化失败的完整堆栈信息：")
            raise VoiceRecognitionError(f"语音识别初始化失败: {e}")
    
    def _init_tts_engine(self):
        """初始化TTS引擎"""
        try:
            logger.info(f"正在初始化TTS引擎: {self.tts_engine_name}")

            if self.tts_engine_name == "fish_audio":
                try:
                    logger.debug("尝试初始化 Fish Audio TTS 引擎...")
                    self.tts_engine = FishAudioEngine(self.config)
                    self.tts_engine.initialize()
                    logger.info("Fish Audio TTS引擎初始化成功")
                except Exception as e:
                    logger.warning(f"Fish Audio TTS引擎初始化失败: {e}")
                    logger.info("回退到本地pyttsx3引擎")
                    logger.debug("尝试初始化 Pyttsx3Engine 作为回退...")
                    self.tts_engine = Pyttsx3Engine(self.config)
                    self.tts_engine.initialize()
                    logger.info("Pyttsx3Engine 作为回退初始化成功")
            else:
                logger.debug("尝试初始化 Pyttsx3Engine...")
                self.tts_engine = Pyttsx3Engine(self.config)
                self.tts_engine.initialize()
                logger.info("Pyttsx3Engine 初始化成功")
            
            # 绑定回调
            if self.tts_engine:
                logger.debug("为TTS引擎绑定回调函数...")
                self.tts_engine.on_tts_started = lambda: self.on_tts_started() if self.on_tts_started else None
                self.tts_engine.on_tts_finished = lambda: self.on_tts_finished() if self.on_tts_finished else None
                logger.info(f"TTS引擎初始化成功")
            else:
                logger.warning("TTS引擎未被创建。")

        except Exception as e:
            logger.error(f"所有TTS引擎初始化都失败: {e}")
            logger.exception("TTS引擎初始化失败的完整堆栈信息：")
            # 不抛出异常，让程序继续运行，只是禁用TTS功能
            self.tts_engine = None
            self.tts_enabled = False
    
    def get_audio_devices(self) -> List[AudioDevice]:
        """获取可用的音频设备列表"""
        devices = []
        try:
            with suppress_alsa_errors():
                p = pyaudio.PyAudio()
            
            try:
                for i in range(p.get_device_count()):
                    info = p.get_device_info_by_index(i)
                    is_input = info['maxInputChannels'] > 0
                    device = AudioDevice(
                        index=i,
                        name=info['name'],
                        channels=info['maxInputChannels'] if is_input else info['maxOutputChannels'],
                        sample_rate=int(info['defaultSampleRate']),
                        is_input=is_input
                    )
                    devices.append(device)
            finally:
                p.terminate()

        except Exception as e:
            logger.error(f"获取音频设备失败: {e}")
        return devices
    
    def start_listening(self):
        """开始语音识别监听"""
        logger.debug("start_listening 调用")
        if not self._microphone_lock.acquire(blocking=False):
            logger.warning("无法获取麦克风锁，可能已在监听中。")
            return

        if not self.recognition_enabled or not self.recognizer or not self.microphone:
            logger.warning(f"语音识别未启用或未初始化. recognition_enabled={self.recognition_enabled}, recognizer is None: {self.recognizer is None}, microphone is None: {self.microphone is None}")
            self._microphone_lock.release()
            return
        
        self._is_listening = True
        self._stop_listening_event = threading.Event()
        self._listen_thread = threading.Thread(
            target=self._listen_in_background, 
            args=(self._stop_listening_event,),
            daemon=True
        )
        self._listen_thread.start()
        logger.info("语音监听线程已启动")

    def _listen_in_background(self, stop_event):
        """在后台线程中运行的监听循环"""
        try:
            with self.microphone as source:
                while not stop_event.is_set():
                    try:
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=self.phrase_time_limit)
                        if stop_event.is_set(): break
                        self._recognize_audio(audio)
                    except sr.WaitTimeoutError:
                        continue
        except Exception as e:
            logger.error(f"麦克风或语音识别出错: {e}")
            if self.on_speech_error:
                self.on_speech_error(f"麦克风错误: {e}")
        finally:
            self._is_listening = False
            self._microphone_lock.release()
            if self.on_listening_stopped:
                self.on_listening_stopped()
            logger.info("语音监听线程已结束，麦克风锁已释放。")

    def stop_listening(self):
        """停止语音识别监听"""
        if not self._is_listening:
            return

        if self._stop_listening_event:
            self._stop_listening_event.set()
        
        logger.info("已发送停止监听信号")
    
    def _recognize_audio(self, audio):
        """识别音频内容"""
        try:
            text = self.recognizer.recognize_google(audio, language=self.recognition_language)
            logger.info(f"识别到语音: {text}")
            if self.on_speech_recognized: self.on_speech_recognized(text)
        except sr.UnknownValueError:
            logger.warning("无法识别语音内容")
            if self.on_speech_error: self.on_speech_error("无法识别语音内容")
        except sr.RequestError as e:
            error_msg = f"语音服务请求失败: {e}"
            logger.error(error_msg)
            if self.on_speech_error: self.on_speech_error(error_msg)
    
    def speak(self, text: str, async_mode: bool = True):
        """文本转语音播放"""
        logger.debug(f"speak 调用, 文本: '{text[:30]}...', 异步: {async_mode}")
        if self.tts_engine and not self.tts_engine.is_speaking:
            logger.debug(f"使用引擎 {self.tts_engine.__class__.__name__} 进行语音合成")
            self.tts_engine.speak(text, async_mode)
            logger.debug("speak 方法调用完成")
        elif not self.tts_engine:
            logger.warning("TTS引擎未初始化，无法播放语音")
        elif self.tts_engine.is_speaking:
            logger.warning("TTS正在播放中，忽略新的请求")
    
    def stop_speaking(self):
        """停止TTS播放"""
        if self.tts_engine and self.tts_engine.is_speaking:
            self.tts_engine.stop_speaking()
    
    def update_config(self, config_manager):
        """更新配置"""
        self.config = config_manager
        # ... (识别参数更新) ...
        
        # 重新初始化TTS引擎以应用新配置
        new_tts_engine_name = self.config.get("audio.tts_engine", "espeak")
        if new_tts_engine_name != self.tts_engine_name and self.tts_enabled:
            self.tts_engine_name = new_tts_engine_name
            try:
                if self.tts_engine: self.tts_engine.cleanup()
                self._init_tts_engine()
            except Exception as e:
                logger.error(f"切换TTS引擎失败: {e}")
        
        logger.info("语音处理器配置已更新")
    
    @property
    def is_listening(self) -> bool:
        return self._is_listening
    
    @property 
    def is_speaking(self) -> bool:
        return self.tts_engine.is_speaking if self.tts_engine else False
    
    def cleanup(self):
        """清理资源"""
        logger.info("正在清理语音处理器资源...")
        self.stop_listening()
        if self.tts_engine:
            self.tts_engine.cleanup()
        logger.info("语音处理器资源清理完成") 