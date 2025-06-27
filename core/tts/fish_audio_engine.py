import threading
import subprocess
import time
import tempfile
import os
import pyaudio
from fish_audio_sdk import Session, TTSRequest
from loguru import logger
from . import TTSEngine
from utils.audio_utils import suppress_alsa_errors
import wave

class FishAudioEngine(TTSEngine):
    """使用 Fish Audio API 的TTS引擎，通过调用系统音频播放"""

    def __init__(self, config_manager):
        super().__init__(config_manager)
        self.api_key = self.config.get("audio.fish_audio.api_key")
        self.reference_id = self.config.get("audio.fish_audio.voice_id")
        self.sample_rate = self.config.get("audio.fish_audio.sample_rate", 32000)
        self.session = None
        self.speak_thread = None
        self.usb_device_name = None

    def _find_usb_audio_device(self):
        """查找USB音频设备"""
        try:
            logger.info("Scanning audio output devices:")
            with suppress_alsa_errors():
                p = pyaudio.PyAudio()
            
            try:
                for i in range(p.get_device_count()):
                    device_info = p.get_device_info_by_index(i)
                    if device_info['maxOutputChannels'] > 0:
                        logger.info(f"Device {i}: {device_info['name']} - Output channels: {device_info['maxOutputChannels']}")
                        if 'usb' in device_info['name'].lower() and 'audio' in device_info['name'].lower():
                            logger.info(f"Found USB audio device: {device_info['name']} (index: {i}, sample_rate: {device_info['defaultSampleRate']})")
                            return i, device_info['name'], int(device_info['defaultSampleRate'])
            finally:
                p.terminate()

        except Exception as e:
            logger.error(f"Error scanning audio devices: {e}")
        return None, None, 44100

    def _set_usb_speaker_as_default(self):
        """设置USB扬声器为默认音频输出设备"""
        try:
            # 查找USB音频设备
            result = subprocess.run(['pactl', 'list', 'short', 'sinks'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if 'usb' in line.lower() and 'audio' in line.lower():
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            device_name = parts[1]
                            subprocess.run(['pactl', 'set-default-sink', device_name], 
                                         timeout=5, check=False)
                            logger.info(f"Set USB speaker as default for Fish Audio: {device_name}")
                            self.usb_device_name = device_name
                            break
        except Exception as e:
            logger.warning(f"Failed to set USB speaker as default: {e}")

    def initialize(self):
        if not self.api_key or "your_fish_audio_api_key" in self.api_key:
            logger.warning("Fish Audio API key is not set.")
            raise ValueError("Fish Audio API key not configured.")
        
        try:
            # 扫描音频设备
            usb_device_idx, usb_device_name, sample_rate = self._find_usb_audio_device()
            if usb_device_idx is not None:
                self.sample_rate = sample_rate
            
            logger.info("正在连接Fish Audio服务...")
            self.session = Session(self.api_key)
            
            # 设置USB扬声器为默认设备
            self._set_usb_speaker_as_default()
            
            logger.info("Fish Audio TTS engine initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Fish Audio SDK: {e}")
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
            
            tmp_file = None
            try:
                logger.info(f"正在生成语音: {text[:50]}...")
                request = TTSRequest(text=text, reference_id=self.reference_id, format="wav")
                audio_stream = self.session.tts(request)

                # 将单声道数据转换为双声道
                mono_data = b''.join(list(audio_stream))
                
                # 每个采样点是2个字节（16位）
                sampwidth = 2 
                stereo_data = b''.join(
                    mono_data[i:i+sampwidth] * 2 for i in range(0, len(mono_data), sampwidth)
                )

                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                    tmp_file = f.name
                    # 使用wave模块写入正确的双声道WAV文件头
                    with wave.open(f, 'wb') as wf:
                        wf.setnchannels(2) # 双声道
                        wf.setsampwidth(sampwidth) # 16-bit
                        wf.setframerate(self.sample_rate)
                        wf.writeframes(stereo_data)
                
                logger.info(f"音频已保存到临时文件: {tmp_file}")

                # 尝试多种播放方式
                success = False
                
                # 方法1: 使用aplay直接播放到USB设备
                if not success:
                    try:
                        command = ["aplay", "-D", "plughw:CARD=Device,DEV=0", tmp_file]
                        logger.info(f"尝试使用aplay播放: {' '.join(command)}")
                        result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=30)
                        logger.info("aplay播放成功")
                        success = True
                    except subprocess.CalledProcessError as e:
                        logger.warning(f"aplay播放失败: {e.stderr}")
                    except subprocess.TimeoutExpired:
                        logger.warning("aplay播放超时")

                # 方法2: 使用系统默认播放器
                if not success:
                    try:
                        command = ["aplay", tmp_file]
                        logger.info(f"尝试使用系统默认播放器: {' '.join(command)}")
                        result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=30)
                        logger.info("系统默认播放器播放成功")
                        success = True
                    except subprocess.CalledProcessError as e:
                        logger.warning(f"系统默认播放器播放失败: {e.stderr}")

                # 方法3: 使用mpv播放器
                if not success:
                    try:
                        command = ["mpv", "--no-video", "--audio-device=pulse", tmp_file]
                        logger.info(f"尝试使用mpv播放: {' '.join(command)}")
                        result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=30)
                        logger.info("mpv播放成功")
                        success = True
                    except subprocess.CalledProcessError as e:
                        logger.warning(f"mpv播放失败: {e.stderr}")

                if not success:
                    logger.error("所有播放方法都失败了")

            except Exception as e:
                logger.error(f"Fish Audio TTS failed: {e}", exc_info=True)
            finally:
                if tmp_file and os.path.exists(tmp_file):
                    os.remove(tmp_file)
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
        # 停止所有音频播放进程
        try:
            subprocess.run(["pkill", "aplay"], check=False)
            subprocess.run(["pkill", "mpv"], check=False)
            logger.info("尝试停止音频播放进程")
        except Exception as e:
            logger.error(f"停止音频播放失败: {e}")
        self._is_speaking = False

    def cleanup(self):
        logger.info("Cleaning up Fish Audio TTS engine...")
        self.stop_speaking()
        if self.speak_thread and self.speak_thread.is_alive():
            try:
                self.speak_thread.join(timeout=1.0)
            except Exception as e:
                logger.error(f"Error joining speak thread: {e}")
        logger.info("Fish Audio TTS engine cleaned up.") 