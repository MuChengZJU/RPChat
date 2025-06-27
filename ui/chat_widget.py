"""
聊天组件模块
实现文本对话界面和消息显示，支持语音输入和真实的AI对话
"""

import asyncio
from datetime import datetime, timezone
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QLineEdit, QPushButton, QScrollArea, QLabel, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from loguru import logger

from core.api_client import ChatMessage
from core.storage_manager import StorageManager, Conversation
from core.voice_handler import VoiceHandler
from utils.text_utils import TextProcessor
from utils.ui_utils import UIUtils


class ChatWidget(QWidget):
    """聊天组件类"""
    
    # 信号定义
    message_sent = pyqtSignal(str)
    conversation_updated = pyqtSignal(str)  # 对话更新信号，携带对话ID
    voice_input_started = pyqtSignal()
    voice_input_finished = pyqtSignal()
    
    def __init__(self, config_manager):
        """
        初始化聊天组件
        
        Args:
            config_manager: 配置管理器实例
        """
        super().__init__()
        
        self.config = config_manager
        self.api_client = None
        self.storage_manager = None
        self.voice_handler = None
        
        # 当前对话状态
        self.current_conversation = None
        self.conversation_history = []
        self.voice_mode = False
        self.is_processing = False
        
        # UI组件
        self.voice_button = None
        self.progress_bar = None
        self.loading_timer = None
        
        self._init_ui()
        self._init_storage()
        self._init_voice_handler()
        self._apply_config()
        
        logger.info("聊天组件初始化完成")
    
    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        
        # 消息显示区域
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText("对话将在这里显示...\n\n提示：\n- 按 Enter 发送消息\n- 点击语音按钮进行语音输入\n- 支持多轮对话上下文")
        layout.addWidget(self.chat_display)
        
        # 进度条（处理请求时显示）
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # 无限进度条
        layout.addWidget(self.progress_bar)
        
        # 输入区域
        input_layout = QHBoxLayout()
        
        # 语音按钮
        self.voice_button = QPushButton("🎤")
        self.voice_button.setFixedSize(40, 40)
        self.voice_button.setToolTip("点击开始语音输入")
        self.voice_button.setCheckable(True)
        self.voice_button.clicked.connect(self._toggle_voice_input)
        input_layout.addWidget(self.voice_button)
        
        # 文本输入框
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("输入消息... (Enter发送)")
        self.message_input.returnPressed.connect(self._send_message)
        input_layout.addWidget(self.message_input)
        
        # 发送按钮
        self.send_button = QPushButton("发送")
        self.send_button.clicked.connect(self._send_message)
        self.send_button.setDefault(True)
        input_layout.addWidget(self.send_button)
        
        layout.addLayout(input_layout)
        
        # 状态显示区域
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("就绪")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        # 模式指示器
        self.mode_label = QLabel("文本模式")
        self.mode_label.setStyleSheet("color: #666; font-size: 11px;")
        status_layout.addWidget(self.mode_label)
        
        layout.addLayout(status_layout)
    
    def _init_storage(self):
        """初始化存储管理器"""
        try:
            self.storage_manager = StorageManager(self.config)
            # 存储管理器的初始化将在第一次使用时进行（异步）
            logger.info("存储管理器初始化完成")
        except Exception as e:
            logger.error(f"存储管理器初始化失败: {e}")
            UIUtils.show_error_message(self, "错误", f"数据存储初始化失败: {e}")
    
    def _init_voice_handler(self):
        """初始化语音处理器"""
        try:
            logger.info("正在初始化语音处理器...")
            self.voice_handler = VoiceHandler(self.config)
            
            # 设置语音回调
            self.voice_handler.on_speech_recognized = self._on_speech_recognized
            self.voice_handler.on_speech_error = self._on_speech_error
            self.voice_handler.on_tts_started = self._on_tts_started
            self.voice_handler.on_tts_finished = self._on_tts_finished
            
            # 初始化语音组件（可能失败，但不影响文本功能）
            try:
                self.voice_handler.initialize()
                logger.info("语音处理器初始化完成")
                
                # 检查语音功能是否可用
                if not self.voice_handler.tts_enabled and not self.voice_handler.recognition_enabled:
                    logger.warning("语音识别和TTS都不可用，禁用语音按钮")
                    self.voice_button.setEnabled(False)
                    self.voice_button.setToolTip("语音功能不可用")
                elif not self.voice_handler.tts_enabled:
                    logger.warning("TTS不可用，语音输出功能将被禁用")
                elif not self.voice_handler.recognition_enabled:
                    logger.warning("语音识别不可用，语音输入功能将被禁用")
                    
            except Exception as e:
                logger.warning(f"语音处理器初始化失败，将禁用语音功能: {e}")
                self.voice_button.setEnabled(False)
                self.voice_button.setToolTip("语音功能不可用")
                # 不清空voice_handler，因为它可能部分可用
                
        except Exception as e:
            logger.error(f"语音处理器创建失败: {e}")
            self.voice_handler = None
            self.voice_button.setEnabled(False)
            self.voice_button.setToolTip("语音功能不可用")
    
    def _apply_config(self):
        """应用配置设置"""
        # 字体设置
        font_family = self.config.get("ui.font_family", "Microsoft YaHei")
        font_size = self.config.get("ui.font_size", 12)
        
        font = QFont(font_family, font_size)
        self.chat_display.setFont(font)
        self.message_input.setFont(font)
        
        # 应用主题
        theme = self.config.get("ui.theme", "light")
        if theme == "dark":
            UIUtils.apply_dark_theme(self)
        else:
            UIUtils.apply_light_theme(self)
    
    def set_api_client(self, api_client):
        """设置API客户端"""
        self.api_client = api_client
        logger.debug("聊天组件已设置API客户端")
    
    def _send_message(self):
        """发送消息"""
        message = self.message_input.text().strip()
        if not message or self.is_processing:
            return
        
        # 清空输入框
        self.message_input.clear()
        
        # 添加用户消息到显示区域
        self._add_message("用户", message, datetime.now(timezone.utc))
        
        # 发送信号
        self.message_sent.emit(message)
        
        # 如果有API客户端，发送到AI
        if self.api_client:
            self._handle_ai_request(message)
        else:
            self._show_api_unavailable_message()
    
    def _add_message(self, sender: str, content: str, timestamp: datetime):
        """
        添加消息到显示区域
        
        Args:
            sender: 发送者名称
            content: 消息内容
            timestamp: 时间戳
        """
        # 使用工具函数格式化消息
        formatted_message = TextProcessor.format_message_for_display(content, sender, timestamp)
        self.chat_display.append(formatted_message)
        
        # 滚动到底部
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # 如果启用了语音模式且是AI回复，播放语音
        if self.voice_mode and sender == "AI助手" and self.voice_handler:
            self.voice_handler.speak(content)
    
    def _handle_ai_request(self, message: str):
        """
        处理AI请求
        
        Args:
            message: 用户消息
        """
        if self.is_processing:
            return
        
        self.is_processing = True
        self._set_processing_ui(True)
        
        # 添加到对话历史
        user_message = ChatMessage(role="user", content=message)
        self.conversation_history.append(user_message)
        
        # 保存用户消息到数据库
        if self.storage_manager and self.current_conversation:
            UIUtils.run_async_task(
                self,
                self.storage_manager.add_message,
                None,  # on_finished - 用户消息保存不需要特殊处理
                self._on_storage_error,
                self.current_conversation.id,
                user_message
            )
        
        # 发送API请求
        UIUtils.run_async_task(
            self,
            self.api_client.chat_completion,
            self._on_ai_response_received,
            self._on_ai_request_error,
            self.conversation_history
        )
    
    def _on_ai_response_received(self, response):
        """AI响应接收回调"""
        try:
            ai_message = ChatMessage(role="assistant", content=response.content)
            self.conversation_history.append(ai_message)
            
            # 显示AI回复
            timestamp = datetime.now(timezone.utc)
            self._add_message("AI助手", response.content, timestamp)
            
            # 保存AI消息到数据库
            if self.storage_manager and self.current_conversation:
                UIUtils.run_async_task(
                    self,
                    self.storage_manager.add_message,
                    self._on_message_saved,
                    self._on_storage_error,
                    self.current_conversation.id,
                    ai_message
                )
            
            # 更新对话标题（如果是第一条消息）
            if len(self.conversation_history) == 2 and self.current_conversation:
                self._update_conversation_title()
            
            logger.info(f"收到AI回复: {response.content[:50]}...")
            
        except Exception as e:
            logger.error(f"处理AI响应失败: {e}")
            self._show_error("处理AI响应时出错")
        finally:
            self._set_processing_ui(False)
            self.is_processing = False
    
    def _on_ai_request_error(self, error_message: str):
        """AI请求错误回调"""
        logger.error(f"AI请求失败: {error_message}")
        self._show_error(f"AI请求失败: {error_message}")
        self._set_processing_ui(False)
        self.is_processing = False
    
    # UI 控制方法
    def _set_processing_ui(self, processing: bool):
        """设置处理状态的UI"""
        if processing:
            self.status_label.setText("AI正在思考...")
            self.progress_bar.setVisible(True)
            self.send_button.setEnabled(False)
            self.voice_button.setEnabled(False)
            self.message_input.setEnabled(False)
        else:
            self.status_label.setText("就绪")
            self.progress_bar.setVisible(False)
            self.send_button.setEnabled(True)
            self.voice_button.setEnabled(self.voice_handler is not None)
            self.message_input.setEnabled(True)
    
    def _show_error(self, message: str):
        """显示错误消息"""
        self.status_label.setText(f"错误: {message}")
        UIUtils.show_error_message(self, "错误", message)
    
    def _show_api_unavailable_message(self):
        """显示API不可用消息"""
        self._add_message("系统", "API客户端未初始化，请检查配置", datetime.now(timezone.utc))
    
    # 语音功能方法
    def _toggle_voice_input(self):
        """切换语音输入"""
        if not self.voice_handler:
            UIUtils.show_warning_message(self, "警告", "语音功能不可用")
            self.voice_button.setChecked(False)
            return
        
        if self.voice_button.isChecked():
            self._start_voice_input()
        else:
            self._stop_voice_input()
    
    def _start_voice_input(self):
        """开始语音输入"""
        try:
            self.voice_handler.start_listening()
            self.voice_button.setText("🔴")
            self.voice_button.setToolTip("点击停止语音输入")
            self.status_label.setText("正在监听语音...")
            self.voice_input_started.emit()
            logger.info("开始语音输入")
        except Exception as e:
            logger.error(f"启动语音输入失败: {e}")
            self._show_error(f"启动语音输入失败: {e}")
            self.voice_button.setChecked(False)
    
    def _stop_voice_input(self):
        """停止语音输入"""
        try:
            if self.voice_handler:
                self.voice_handler.stop_listening()
            self.voice_button.setText("🎤")
            self.voice_button.setToolTip("点击开始语音输入")
            self.status_label.setText("就绪")
            self.voice_input_finished.emit()
            logger.info("停止语音输入")
        except Exception as e:
            logger.error(f"停止语音输入失败: {e}")
    
    # 语音事件回调
    def _on_speech_recognized(self, text: str):
        """语音识别回调"""
        logger.info(f"语音识别结果: {text}")
        self.message_input.setText(text)
        self.status_label.setText(f"识别到: {text}")
        
        # 自动发送消息（可选）
        auto_send = self.config.get("audio.auto_send_voice", True)
        if auto_send and text.strip():
            QTimer.singleShot(1000, self._send_message)  # 延迟1秒发送
    
    def _on_speech_error(self, error: str):
        """语音识别错误回调"""
        logger.warning(f"语音识别错误: {error}")
        self.status_label.setText(f"语音识别错误: {error}")
    
    def _on_tts_started(self):
        """TTS开始播放回调"""
        self.status_label.setText("正在播放语音...")
    
    def _on_tts_finished(self):
        """TTS播放完成回调"""
        self.status_label.setText("就绪")
    
    # 存储相关方法
    def _on_message_saved(self, stored_message):
        """消息保存回调"""
        if stored_message:
            logger.debug(f"消息已保存: {stored_message.id}")
    
    def _on_storage_error(self, error: str):
        """存储错误回调"""
        logger.error(f"存储错误: {error}")
        # 存储错误不影响用户体验，只记录日志
    
    def _update_conversation_title(self):
        """更新对话标题"""
        if not self.current_conversation or len(self.conversation_history) < 1:
            return
        
        first_user_message = None
        for msg in self.conversation_history:
            if msg.role == "user":
                first_user_message = msg
                break
        
        if first_user_message:
            new_title = TextProcessor.generate_conversation_title(first_user_message.content)
            self.current_conversation.title = new_title
            
            # 异步更新数据库
            if self.storage_manager:
                UIUtils.run_async_task(
                    self,
                    self.storage_manager.update_conversation,
                    lambda _: self.conversation_updated.emit(self.current_conversation.id),
                    self._on_storage_error,
                    self.current_conversation
                )
    
    # 公共接口方法
    def new_conversation(self):
        """开始新对话"""
        if self.current_conversation and self.storage_manager:
            # 创建新对话
            UIUtils.run_async_task(
                self,
                self.storage_manager.create_conversation,
                self._on_new_conversation_created,
                self._on_storage_error,
                "新对话",
                self.config.get("api.model", "")
            )
        else:
            # 没有存储管理器，只清空界面
            self._clear_conversation_ui()
        
        logger.info("开始新对话")
    
    def _on_new_conversation_created(self, conversation):
        """新对话创建回调"""
        self.current_conversation = conversation
        self._clear_conversation_ui()
        self.conversation_updated.emit(conversation.id)
        logger.info(f"新对话已创建: {conversation.id}")
    
    def _clear_conversation_ui(self):
        """清空对话UI"""
        self.conversation_history.clear()
        self.chat_display.clear()
        self.status_label.setText("新对话已开始")
    
    def clear_conversation(self):
        """清空当前对话"""
        if UIUtils.show_question_dialog(self, "确认清空", "确定要清空当前对话吗？此操作不可恢复。"):
            self._clear_conversation_ui()
            logger.info("对话已清空")
    
    def save_conversation(self) -> bool:
        """保存对话"""
        if not self.current_conversation or not self.storage_manager:
            return False
        
        try:
            # 对话已经在发送消息时自动保存，这里只是更新状态
            self.status_label.setText("对话已保存")
            QTimer.singleShot(2000, lambda: self.status_label.setText("就绪"))
            logger.info(f"对话已保存: {self.current_conversation.id}")
            return True
        except Exception as e:
            logger.error(f"保存对话失败: {e}")
            return False
    
    def load_conversation(self, conversation_id: str):
        """加载对话"""
        if not self.storage_manager:
            logger.warning("存储管理器未初始化")
            return
        
        self._set_processing_ui(True)
        
        # 异步加载对话
        UIUtils.run_async_task(
            self,
            self._load_conversation_async,
            self._on_conversation_loaded,
            self._on_conversation_load_error,
            conversation_id
        )
    
    async def _load_conversation_async(self, conversation_id: str):
        """异步加载对话数据"""
        # 获取对话信息
        conversation = await self.storage_manager.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"对话不存在: {conversation_id}")
        
        # 获取消息历史
        messages = await self.storage_manager.get_messages(conversation_id)
        
        return {
            'conversation': conversation,
            'messages': messages
        }
    
    def _on_conversation_loaded(self, data):
        """对话加载完成回调"""
        try:
            conversation = data['conversation']
            messages = data['messages']
            
            # 设置当前对话
            self.current_conversation = conversation
            
            # 清空界面
            self.chat_display.clear()
            self.conversation_history.clear()
            
            # 加载消息历史
            for stored_msg in messages:
                # 添加到界面显示
                sender = "用户" if stored_msg.role == "user" else "AI助手"
                self._add_message(sender, stored_msg.content, stored_msg.timestamp)
                
                # 添加到对话历史
                chat_msg = ChatMessage(role=stored_msg.role, content=stored_msg.content)
                self.conversation_history.append(chat_msg)
            
            self.status_label.setText(f"已加载对话: {conversation.title}")
            QTimer.singleShot(2000, lambda: self.status_label.setText("就绪"))
            
            logger.info(f"对话加载完成: {conversation.id}, 消息数: {len(messages)}")
            
        except Exception as e:
            logger.error(f"处理加载的对话数据失败: {e}")
            self._show_error("加载对话数据失败")
        finally:
            self._set_processing_ui(False)
    
    def _on_conversation_load_error(self, error: str):
        """对话加载错误回调"""
        logger.error(f"加载对话失败: {error}")
        self._show_error(f"加载对话失败: {error}")
        self._set_processing_ui(False)
    
    def set_voice_mode(self, enabled: bool):
        """设置语音模式"""
        self.voice_mode = enabled
        
        if enabled:
            self.message_input.setPlaceholderText("语音模式 - 点击🎤录音或直接输入...")
            self.mode_label.setText("语音模式")
            self.mode_label.setStyleSheet("color: #4CAF50; font-size: 11px; font-weight: bold;")
        else:
            self.message_input.setPlaceholderText("输入消息... (Enter发送)")
            self.mode_label.setText("文本模式")
            self.mode_label.setStyleSheet("color: #666; font-size: 11px;")
        
        logger.info(f"语音模式: {'启用' if enabled else '禁用'}")
    
    def get_conversation_summary(self) -> dict:
        """获取当前对话摘要"""
        if not self.current_conversation:
            return {}
        
        # 统计信息
        user_messages = sum(1 for msg in self.conversation_history if msg.role == "user")
        ai_messages = sum(1 for msg in self.conversation_history if msg.role == "assistant")
        total_chars = sum(len(msg.content) for msg in self.conversation_history)
        
        return {
            'conversation_id': self.current_conversation.id,
            'title': self.current_conversation.title,
            'message_count': len(self.conversation_history),
            'user_messages': user_messages,
            'ai_messages': ai_messages,
            'total_characters': total_chars,
            'model': self.current_conversation.model
        }
    
    def export_conversation(self) -> dict:
        """导出当前对话"""
        if not self.current_conversation or not self.storage_manager:
            return {}
        
        try:
            # 这里应该异步执行，简化处理
            export_data = {
                'conversation': self.current_conversation.to_dict(),
                'messages': [
                    {
                        'role': msg.role,
                        'content': msg.content,
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                    for msg in self.conversation_history
                ],
                'export_timestamp': datetime.now(timezone.utc).isoformat(),
                'version': '1.0'
            }
            
            logger.info(f"对话导出完成: {self.current_conversation.id}")
            return export_data
            
        except Exception as e:
            logger.error(f"导出对话失败: {e}")
            return {}
    
    def cleanup(self):
        """清理资源"""
        logger.info("正在清理聊天组件资源...")
        
        try:
            # 停止语音功能
            if hasattr(self, 'voice_handler') and self.voice_handler:
                try:
                    self.voice_handler.stop_listening()
                    self.voice_handler.stop_speaking()
                    self.voice_handler.cleanup()
                    logger.debug("语音处理器清理完成")
                except Exception as e:
                    logger.error(f"清理语音处理器时出错: {e}")
            
            # 取消正在进行的API请求
            if hasattr(self, '_current_request_task') and self._current_request_task:
                try:
                    self._current_request_task.cancel()
                    logger.debug("API请求任务已取消")
                except Exception as e:
                    logger.error(f"取消API请求时出错: {e}")
            
            # 清理存储管理器
            if hasattr(self, 'storage_manager') and self.storage_manager:
                try:
                    # 这里不需要调用close，因为它会在主窗口中处理
                    logger.debug("存储管理器引用已清理")
                except Exception as e:
                    logger.error(f"清理存储管理器时出错: {e}")
            
            # 清理UI状态
            try:
                self.send_button.setEnabled(True)
                self.message_input.setEnabled(True)
                if hasattr(self, 'voice_button'):
                    self.voice_button.setEnabled(True)
                logger.debug("UI状态已重置")
            except Exception as e:
                logger.error(f"重置UI状态时出错: {e}")
            
            logger.info("聊天组件资源清理完成")
            
        except Exception as e:
            logger.error(f"聊天组件清理过程中出现错误: {e}") 