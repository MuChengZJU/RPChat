"""
聊天组件模块
实现文本对话界面和消息显示
"""

import asyncio
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QLineEdit, QPushButton, QScrollArea, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from loguru import logger

from core.api_client import ChatMessage


class ChatWidget(QWidget):
    """聊天组件类"""
    
    # 信号定义
    message_sent = pyqtSignal(str)
    
    def __init__(self, config_manager):
        """
        初始化聊天组件
        
        Args:
            config_manager: 配置管理器实例
        """
        super().__init__()
        
        self.config = config_manager
        self.api_client = None
        self.conversation_history = []
        self.voice_mode = False
        
        self._init_ui()
        self._apply_config()
        
        logger.info("聊天组件初始化完成")
    
    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        
        # 消息显示区域
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText("对话将在这里显示...")
        layout.addWidget(self.chat_display)
        
        # 输入区域
        input_layout = QHBoxLayout()
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("输入消息...")
        self.message_input.returnPressed.connect(self._send_message)
        input_layout.addWidget(self.message_input)
        
        self.send_button = QPushButton("发送")
        self.send_button.clicked.connect(self._send_message)
        input_layout.addWidget(self.send_button)
        
        layout.addLayout(input_layout)
        
        # 状态显示
        self.status_label = QLabel("就绪")
        layout.addWidget(self.status_label)
    
    def _apply_config(self):
        """应用配置设置"""
        # 字体设置
        font_family = self.config.get("ui.font_family", "Microsoft YaHei")
        font_size = self.config.get("ui.font_size", 12)
        
        font = QFont(font_family, font_size)
        self.chat_display.setFont(font)
        self.message_input.setFont(font)
    
    def set_api_client(self, api_client):
        """设置API客户端"""
        self.api_client = api_client
        logger.debug("聊天组件已设置API客户端")
    
    def _send_message(self):
        """发送消息"""
        message = self.message_input.text().strip()
        if not message:
            return
        
        # 清空输入框
        self.message_input.clear()
        
        # 添加用户消息到显示区域
        self._add_message("用户", message)
        
        # 发送信号
        self.message_sent.emit(message)
        
        # 如果有API客户端，发送到AI
        if self.api_client:
            self._handle_ai_request(message)
    
    def _add_message(self, sender: str, content: str):
        """
        添加消息到显示区域
        
        Args:
            sender: 发送者名称
            content: 消息内容
        """
        # 简单的HTML格式化
        if sender == "用户":
            formatted_message = f'<p><b style="color: #4CAF50;">{sender}:</b> {content}</p>'
        else:
            formatted_message = f'<p><b style="color: #2196F3;">{sender}:</b> {content}</p>'
        
        self.chat_display.append(formatted_message)
        
        # 滚动到底部
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _handle_ai_request(self, message: str):
        """
        处理AI请求
        
        Args:
            message: 用户消息
        """
        self.status_label.setText("AI正在思考...")
        self.send_button.setEnabled(False)
        
        # 添加到对话历史
        self.conversation_history.append(ChatMessage(role="user", content=message))
        
        # 简化处理：显示模拟响应
        # TODO: 实现真正的异步API调用
        QTimer.singleShot(1000, lambda: self._simulate_ai_response())
    
    def _simulate_ai_response(self):
        """模拟AI响应（临时实现）"""
        response = "这是一个模拟的AI响应。API客户端功能正在开发中。"
        
        self._add_message("AI助手", response)
        self.conversation_history.append(ChatMessage(role="assistant", content=response))
        
        self.status_label.setText("就绪")
        self.send_button.setEnabled(True)
    
    def new_conversation(self):
        """开始新对话"""
        self.conversation_history.clear()
        self.chat_display.clear()
        self.status_label.setText("开始新对话")
        logger.info("已开始新对话")
    
    def clear_conversation(self):
        """清空当前对话"""
        self.chat_display.clear()
        self.conversation_history.clear()
        self.status_label.setText("对话已清空")
    
    def save_conversation(self) -> bool:
        """保存对话"""
        # TODO: 实现对话保存功能
        logger.info("保存对话功能正在开发中")
        return True
    
    def load_conversation(self, conversation_id: str):
        """加载对话"""
        # TODO: 实现对话加载功能
        logger.info(f"加载对话功能正在开发中: {conversation_id}")
    
    def set_voice_mode(self, enabled: bool):
        """设置语音模式"""
        self.voice_mode = enabled
        if enabled:
            self.message_input.setPlaceholderText("点击录音或输入消息...")
        else:
            self.message_input.setPlaceholderText("输入消息...")
        
        logger.info(f"语音模式: {'启用' if enabled else '禁用'}")
    
    def cleanup(self):
        """清理资源"""
        logger.info("正在清理聊天组件资源...")
        # 清理相关资源 