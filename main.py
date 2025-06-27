#!/usr/bin/env python3
"""
RPChat - 基于PyQt的智能语音对话前端
主程序入口
"""

import sys
import asyncio
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread
from loguru import logger

# 添加项目路径到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.config_manager import ConfigManager
from ui.main_window import MainWindow


class RPChatApplication:
    """RPChat应用程序主类"""
    
    def __init__(self):
        self.app = None
        self.main_window = None
        self.config_manager = None
        
    def setup_logging(self):
        """配置日志系统"""
        log_dir = project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logger.add(
            log_dir / "rpchat.log",
            rotation="10 MB",
            retention="7 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
        )
        
    def initialize(self):
        """初始化应用程序"""
        try:
            # 设置日志
            self.setup_logging()
            logger.info("正在启动 RPChat 应用程序...")
            
            # 创建PyQt6应用程序
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("RPChat")
            self.app.setApplicationVersion("1.0.0")
            self.app.setOrganizationName("RPChat Team")
            
            # 初始化配置管理器
            self.config_manager = ConfigManager()
            self.config_manager.load_config()
            
            # 创建主窗口
            self.main_window = MainWindow(self.config_manager)
            
            logger.info("RPChat 应用程序初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"应用程序初始化失败: {e}")
            return False
    
    def run(self):
        """运行应用程序"""
        if not self.initialize():
            return 1
            
        try:
            # 显示主窗口
            self.main_window.show()
            
            logger.info("RPChat 应用程序启动成功")
            
            # 运行应用程序事件循环
            return self.app.exec()
            
        except Exception as e:
            logger.error(f"应用程序运行错误: {e}")
            return 1
        finally:
            self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        logger.info("正在清理应用程序资源...")
        
        if self.main_window:
            self.main_window.cleanup()
        
        logger.info("应用程序已退出")


def main():
    """主函数"""
    app = RPChatApplication()
    return app.run()


if __name__ == "__main__":
    sys.exit(main()) 