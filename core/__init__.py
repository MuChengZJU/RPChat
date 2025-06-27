"""
Core模块
RPChat应用程序的核心业务逻辑
"""

__version__ = "1.0.0"

from .config_manager import ConfigManager
from .api_client import OpenAIAPIClient, ChatMessage, ChatResponse

__all__ = [
    "ConfigManager",
    "OpenAIAPIClient", 
    "ChatMessage",
    "ChatResponse"
] 