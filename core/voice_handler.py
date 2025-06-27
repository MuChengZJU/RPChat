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
import pyttsx3
import pyaudio
from loguru import logger


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
        self.recognition_timeout = self.config.get("audio.recognition_timeout", 5)
        self.phrase_time_limit = self.config.get("audio.recognition_phrase_time_limit", 30)
        
        # TTS配置
        self.tts_enabled = self.config.get("audio.tts_enabled", True)
        self.tts_engine_name = self.config.get("audio.tts_engine", "espeak")
        self.tts_voice = self.config.get("audio.tts_voice", "zh")
        self.tts_rate = self.config.get("audio.tts_rate", 150)
        self.tts_volume = self.config.get("audio.tts_volume", 0.8)
        
        # 音频设备配置
        self.input_device_index = self.config.get("audio.input_device_index", -1)
        self.output_device_index = self.config.get("audio.output_device_index", -1)
        
        # 组件初始化
        self.recognizer = None
        self.microphone = None
        self.tts_engine = None
        self._is_listening = False
        self._is_speaking = False
        
        # 回调函数
        self.on_speech_recognized: Optional[Callable[[str], None]] = None
        self.on_speech_error: Optional[Callable[[str], None]] = None
        self.on_tts_started: Optional[Callable[[], None]] = None
        self.on_tts_finished: Optional[Callable[[], None]] = None
        
        logger.info("语音处理器初始化完成")
    
    def initialize(self):
        """初始化语音组件"""
        try:
            if self.recognition_enabled:
                self._init_speech_recognition()
            
            if self.tts_enabled:
                self._init_tts_engine()
            
            logger.info("语音组件初始化成功")
            
        except Exception as e:
            logger.error(f"语音组件初始化失败: {e}")
            raise
    
    def _init_speech_recognition(self):
        """初始化语音识别"""
        try:
            self.recognizer = sr.Recognizer()
            
            # 设置识别参数
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
            
            # 初始化麦克风
            device_index = None if self.input_device_index == -1 else self.input_device_index
            self.microphone = sr.Microphone(device_index=device_index)
            
            # 环境噪音校准
            with self.microphone as source:
                logger.info("正在校准环境噪音...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            logger.info(f"语音识别初始化完成 - 语言: {self.recognition_language}")
            
        except Exception as e:
            logger.error(f"语音识别初始化失败: {e}")
            raise VoiceRecognitionError(f"语音识别初始化失败: {e}")
    
    def _init_tts_engine(self):
        """初始化TTS引擎"""
        try:
            self.tts_engine = pyttsx3.init(driverName=self.tts_engine_name)
            
            # 设置TTS参数
            self.tts_engine.setProperty('rate', self.tts_rate)
            self.tts_engine.setProperty('volume', self.tts_volume)
            
            # 设置语音
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # 尝试找到中文语音
                chinese_voice = None
                for voice in voices:
                    if 'zh' in voice.id.lower() or 'chinese' in voice.name.lower():
                        chinese_voice = voice
                        break
                
                if chinese_voice:
                    self.tts_engine.setProperty('voice', chinese_voice.id)
                    logger.info(f"使用中文语音: {chinese_voice.name}")
                else:
                    logger.warning("未找到中文语音，使用默认语音")
            
            logger.info("TTS引擎初始化完成")
            
        except Exception as e:
            logger.error(f"TTS引擎初始化失败: {e}")
            raise TTSError(f"TTS引擎初始化失败: {e}")
    
    def get_audio_devices(self) -> List[AudioDevice]:
        """
        获取可用的音频设备列表
        
        Returns:
            List[AudioDevice]: 音频设备列表
        """
        devices = []
        
        try:
            p = pyaudio.PyAudio()
            
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                
                if info['maxInputChannels'] > 0:
                    device = AudioDevice(
                        index=i,
                        name=info['name'],
                        channels=info['maxInputChannels'],
                        sample_rate=int(info['defaultSampleRate']),
                        is_input=True
                    )
                    devices.append(device)
                
                if info['maxOutputChannels'] > 0:
                    device = AudioDevice(
                        index=i,
                        name=info['name'],
                        channels=info['maxOutputChannels'],
                        sample_rate=int(info['defaultSampleRate']),
                        is_input=False
                    )
                    devices.append(device)
            
            p.terminate()
            
        except Exception as e:
            logger.error(f"获取音频设备失败: {e}")
        
        return devices
    
    def start_listening(self):
        """开始语音识别监听"""
        if not self.recognition_enabled or not self.recognizer or not self.microphone:
            logger.warning("语音识别未启用或未初始化")
            return
        
        if self._is_listening:
            logger.warning("已在监听状态")
            return
        
        self._is_listening = True
        
        def listen_worker():
            """语音监听工作线程"""
            try:
                with self.microphone as source:
                    logger.info("开始语音监听...")
                    
                    while self._is_listening:
                        try:
                            # 监听音频
                            audio = self.recognizer.listen(
                                source, 
                                timeout=self.recognition_timeout,
                                phrase_time_limit=self.phrase_time_limit
                            )
                            
                            if not self._is_listening:
                                break
                            
                            # 识别语音
                            self._recognize_audio(audio)
                            
                        except sr.WaitTimeoutError:
                            # 超时继续监听
                            continue
                        except sr.UnknownValueError:
                            logger.debug("无法识别语音内容")
                            if self.on_speech_error:
                                self.on_speech_error("无法识别语音内容")
                        except sr.RequestError as e:
                            logger.error(f"语音识别服务错误: {e}")
                            if self.on_speech_error:
                                self.on_speech_error(f"语音识别服务错误: {e}")
                        except Exception as e:
                            logger.error(f"语音识别异常: {e}")
                            if self.on_speech_error:
                                self.on_speech_error(f"语音识别异常: {e}")
                            break
                            
            except Exception as e:
                logger.error(f"语音监听线程异常: {e}")
                self._is_listening = False
            
            logger.info("语音监听已停止")
        
        # 在后台线程中启动监听
        listen_thread = threading.Thread(target=listen_worker, daemon=True)
        listen_thread.start()
    
    def stop_listening(self):
        """停止语音识别监听"""
        if self._is_listening:
            self._is_listening = False
            logger.info("正在停止语音监听...")
    
    def _recognize_audio(self, audio):
        """
        识别音频内容
        
        Args:
            audio: 音频数据
        """
        try:
            # 使用Google语音识别
            text = self.recognizer.recognize_google(audio, language=self.recognition_language)
            logger.info(f"识别到语音: {text}")
            
            if self.on_speech_recognized:
                self.on_speech_recognized(text)
                
        except sr.UnknownValueError:
            raise
        except sr.RequestError as e:
            # 如果Google识别失败，尝试其他引擎
            try:
                text = self.recognizer.recognize_sphinx(audio, language=self.recognition_language)
                logger.info(f"识别到语音(本地): {text}")
                
                if self.on_speech_recognized:
                    self.on_speech_recognized(text)
                    
            except:
                raise sr.RequestError(f"所有语音识别服务都不可用: {e}")
    
    def recognize_from_file(self, audio_file_path: str) -> str:
        """
        从音频文件识别语音
        
        Args:
            audio_file_path: 音频文件路径
            
        Returns:
            str: 识别的文本
            
        Raises:
            VoiceRecognitionError: 识别失败
        """
        if not self.recognition_enabled or not self.recognizer:
            raise VoiceRecognitionError("语音识别未启用")
        
        try:
            with sr.AudioFile(audio_file_path) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio, language=self.recognition_language)
                logger.info(f"从文件识别到语音: {text}")
                return text
                
        except Exception as e:
            logger.error(f"文件语音识别失败: {e}")
            raise VoiceRecognitionError(f"文件语音识别失败: {e}")
    
    def speak(self, text: str, async_mode: bool = True):
        """
        文本转语音播放
        
        Args:
            text: 要播放的文本
            async_mode: 是否异步播放
        """
        if not self.tts_enabled or not self.tts_engine:
            logger.warning("TTS未启用或未初始化")
            return
        
        if self._is_speaking:
            logger.warning("TTS正在播放中")
            return
        
        def speak_worker():
            """TTS播放工作线程"""
            try:
                self._is_speaking = True
                
                if self.on_tts_started:
                    self.on_tts_started()
                
                logger.info(f"开始TTS播放: {text[:50]}...")
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
                
                if self.on_tts_finished:
                    self.on_tts_finished()
                
                logger.debug("TTS播放完成")
                
            except Exception as e:
                logger.error(f"TTS播放失败: {e}")
            finally:
                self._is_speaking = False
        
        if async_mode:
            # 异步播放
            speak_thread = threading.Thread(target=speak_worker, daemon=True)
            speak_thread.start()
        else:
            # 同步播放
            speak_worker()
    
    def stop_speaking(self):
        """停止TTS播放"""
        if self.tts_engine and self._is_speaking:
            try:
                self.tts_engine.stop()
                self._is_speaking = False
                logger.info("TTS播放已停止")
            except Exception as e:
                logger.error(f"停止TTS播放失败: {e}")
    
    def save_speech_to_file(self, text: str, output_path: str):
        """
        将文本转换为语音文件
        
        Args:
            text: 要转换的文本
            output_path: 输出文件路径
        """
        if not self.tts_enabled or not self.tts_engine:
            raise TTSError("TTS未启用或未初始化")
        
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.tts_engine.save_to_file(text, str(output_path))
            self.tts_engine.runAndWait()
            
            logger.info(f"语音文件已保存: {output_path}")
            
        except Exception as e:
            logger.error(f"保存语音文件失败: {e}")
            raise TTSError(f"保存语音文件失败: {e}")
    
    def test_microphone(self) -> bool:
        """
        测试麦克风功能
        
        Returns:
            bool: 测试是否成功
        """
        if not self.recognition_enabled or not self.recognizer or not self.microphone:
            return False
        
        try:
            with self.microphone as source:
                logger.info("正在测试麦克风...")
                audio = self.recognizer.listen(source, timeout=2, phrase_time_limit=3)
                logger.info("麦克风测试成功")
                return True
                
        except Exception as e:
            logger.error(f"麦克风测试失败: {e}")
            return False
    
    def test_tts(self) -> bool:
        """
        测试TTS功能
        
        Returns:
            bool: 测试是否成功
        """
        if not self.tts_enabled or not self.tts_engine:
            return False
        
        try:
            test_text = "这是TTS测试"
            self.speak(test_text, async_mode=False)
            logger.info("TTS测试成功")
            return True
            
        except Exception as e:
            logger.error(f"TTS测试失败: {e}")
            return False
    
    def update_config(self, config_manager):
        """
        更新配置
        
        Args:
            config_manager: 新的配置管理器
        """
        self.config = config_manager
        
        # 更新配置参数
        self.recognition_enabled = self.config.get("audio.speech_recognition_enabled", True)
        self.recognition_language = self.config.get("audio.recognition_language", "zh-CN")
        self.recognition_timeout = self.config.get("audio.recognition_timeout", 5)
        self.phrase_time_limit = self.config.get("audio.recognition_phrase_time_limit", 30)
        
        self.tts_enabled = self.config.get("audio.tts_enabled", True)
        self.tts_rate = self.config.get("audio.tts_rate", 150)
        self.tts_volume = self.config.get("audio.tts_volume", 0.8)
        
        # 更新TTS引擎参数
        if self.tts_engine:
            self.tts_engine.setProperty('rate', self.tts_rate)
            self.tts_engine.setProperty('volume', self.tts_volume)
        
        logger.info("语音处理器配置已更新")
    
    @property
    def is_listening(self) -> bool:
        """获取监听状态"""
        return self._is_listening
    
    @property 
    def is_speaking(self) -> bool:
        """获取播放状态"""
        return self._is_speaking
    
    def cleanup(self):
        """清理资源"""
        logger.info("正在清理语音处理器资源...")
        
        # 停止监听和播放
        self.stop_listening()
        self.stop_speaking()
        
        # 等待线程结束
        time.sleep(0.5)
        
        # 清理TTS引擎
        if self.tts_engine:
            try:
                self.tts_engine.stop()
            except:
                pass
            self.tts_engine = None
        
        logger.info("语音处理器资源清理完成") 