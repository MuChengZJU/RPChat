"""
UI模块
RPChat应用程序的用户界面组件
"""

__version__ = "1.0.0"

from .main_window import MainWindow
from .chat_widget import ChatWidget
from .sidebar_widget import SidebarWidget

__all__ = [
    "MainWindow",
    "ChatWidget", 
    "SidebarWidget"
] 