from abc import ABC, abstractmethod
from typing import Optional, Callable

class TTSEngine(ABC):
    """TTS引擎抽象基类"""

    def __init__(self, config_manager):
        self.config = config_manager
        self._is_speaking = False
        self.on_tts_started: Optional[Callable[[], None]] = None
        self.on_tts_finished: Optional[Callable[[], None]] = None

    @abstractmethod
    def initialize(self):
        """初始化引擎"""
        pass

    @abstractmethod
    def speak(self, text: str, async_mode: bool = True):
        """播放语音"""
        pass

    @abstractmethod
    def stop_speaking(self):
        """停止播放"""
        pass

    @property
    def is_speaking(self) -> bool:
        """获取播放状态"""
        return self._is_speaking

    @abstractmethod
    def cleanup(self):
        """清理资源"""
        pass 