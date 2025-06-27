"""
侧边栏组件模块
显示对话列表和会话管理功能，支持搜索、删除、重命名等操作
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
    QListWidgetItem, QPushButton, QLabel, QLineEdit,
    QMenu, QInputDialog, QMessageBox, QProgressBar,
    QSplitter, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt6.QtGui import QFont, QAction, QCursor
from datetime import datetime, timezone
from loguru import logger

from core.storage_manager import StorageManager, Conversation
from utils.text_utils import TextProcessor
from utils.ui_utils import UIUtils


class ConversationListItem(QListWidgetItem):
    """自定义对话列表项"""
    
    def __init__(self, conversation: Conversation):
        super().__init__()
        
        self.conversation = conversation
        self.update_display()
    
    def update_display(self):
        """更新显示内容"""
        # 格式化时间
        time_str = TextProcessor.format_timestamp(
            self.conversation.updated_at, "%m-%d %H:%M"
        )
        
        # 设置显示文本
        display_text = f"{self.conversation.title}"
        if self.conversation.message_count > 0:
            display_text += f" ({self.conversation.message_count})"
        
        self.setText(display_text)
        self.setToolTip(
            f"标题: {self.conversation.title}\n"
            f"消息数: {self.conversation.message_count}\n"
            f"最后更新: {time_str}\n"
            f"模型: {self.conversation.model}"
        )
        
        # 存储对话ID
        self.setData(Qt.ItemDataRole.UserRole, self.conversation.id)


class SidebarWidget(QWidget):
    """侧边栏组件类"""
    
    # 信号定义
    conversation_selected = pyqtSignal(str)
    new_conversation = pyqtSignal()
    conversation_deleted = pyqtSignal(str)
    conversation_renamed = pyqtSignal(str, str)  # conversation_id, new_title
    
    def __init__(self, config_manager):
        """
        初始化侧边栏组件
        
        Args:
            config_manager: 配置管理器实例
        """
        super().__init__()
        
        self.config = config_manager
        self.storage_manager = None
        self.conversations = []
        self.current_conversation_id = None
        self.search_timer = QTimer()
        
        self._init_storage()
        self._init_ui()
        self._apply_config()
        self._setup_connections()
        
        # 初始加载对话列表
        self._load_conversations()
        
        logger.info("侧边栏组件初始化完成")
    
    def _init_storage(self):
        """初始化存储管理器"""
        try:
            self.storage_manager = StorageManager(self.config)
            logger.info("侧边栏存储管理器初始化完成")
        except Exception as e:
            logger.error(f"侧边栏存储管理器初始化失败: {e}")
            UIUtils.show_error_message(self, "错误", f"数据存储初始化失败: {e}")

    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 标题和新建按钮
        header_layout = QHBoxLayout()
        
        title_label = QLabel("对话历史")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.new_chat_button = QPushButton("＋")
        self.new_chat_button.setFixedSize(30, 30)
        self.new_chat_button.setToolTip("新建对话")
        self.new_chat_button.clicked.connect(self._create_new_conversation)
        header_layout.addWidget(self.new_chat_button)
        
        layout.addLayout(header_layout)
        
        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索对话...")
        self.search_input.textChanged.connect(self._on_search_text_changed)
        layout.addWidget(self.search_input)
        
        # 对话列表
        self.conversation_list = QListWidget()
        self.conversation_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.conversation_list.customContextMenuRequested.connect(self._show_context_menu)
        self.conversation_list.itemClicked.connect(self._on_conversation_selected)
        self.conversation_list.itemDoubleClicked.connect(self._on_conversation_double_clicked)
        layout.addWidget(self.conversation_list)
        
        # 加载指示器
        self.loading_label = QLabel("正在加载对话...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setVisible(False)
        layout.addWidget(self.loading_label)
        
        # 统计信息
        self.stats_label = QLabel("总计: 0 个对话")
        self.stats_label.setStyleSheet("color: #666; font-size: 11px;")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.stats_label)
    
    def _apply_config(self):
        """应用配置设置"""
        # 字体设置
        font_family = self.config.get("ui.font_family", "Microsoft YaHei")
        font_size = self.config.get("ui.font_size", 12)
        
        font = QFont(font_family, font_size)
        self.conversation_list.setFont(font)
        self.search_input.setFont(font)
        
        # 应用主题
        theme = self.config.get("ui.theme", "light")
        if theme == "dark":
            UIUtils.apply_dark_theme(self)
        else:
            UIUtils.apply_light_theme(self)
    
    def _setup_connections(self):
        """设置信号连接"""
        # 搜索防抖动
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)
    
    def _load_conversations(self):
        """加载对话列表"""
        if not self.storage_manager:
            return
        
        self.loading_label.setVisible(True)
        self.conversation_list.setVisible(False)
        
        # 异步加载对话
        UIUtils.run_async_task(
            self.storage_manager.get_conversations,
            self._on_conversations_loaded,
            self._on_conversations_load_error,
            50  # 最多加载50个对话
        )
    
    def _on_conversations_loaded(self, conversations):
        """对话加载完成回调"""
        try:
            self.conversations = conversations
            self._update_conversation_list(conversations)
            
            # 更新统计信息
            self._update_stats_label(len(conversations))
            
            logger.info(f"加载了 {len(conversations)} 个对话")
            
        except Exception as e:
            logger.error(f"处理加载的对话失败: {e}")
        finally:
            self.loading_label.setVisible(False)
            self.conversation_list.setVisible(True)
    
    def _on_conversations_load_error(self, error: str):
        """对话加载错误回调"""
        logger.error(f"加载对话失败: {error}")
        self.loading_label.setText(f"加载失败: {error}")
        QTimer.singleShot(3000, lambda: self.loading_label.setVisible(False))
    
    def _update_conversation_list(self, conversations):
        """更新对话列表显示"""
        self.conversation_list.clear()
        
        for conversation in conversations:
            item = ConversationListItem(conversation)
            self.conversation_list.addItem(item)
        
        # 如果有对话且没有选中的，选中第一个
        if self.conversation_list.count() > 0 and not self.current_conversation_id:
            first_item = self.conversation_list.item(0)
            self.conversation_list.setCurrentItem(first_item)
            self.current_conversation_id = first_item.data(Qt.ItemDataRole.UserRole)
    
    def _update_stats_label(self, count: int):
        """更新统计标签"""
        if count == 0:
            self.stats_label.setText("暂无对话")
        else:
            self.stats_label.setText(f"总计: {count} 个对话")
    
    # 搜索功能
    def _on_search_text_changed(self, text: str):
        """搜索文本变化处理"""
        # 使用定时器防抖动
        self.search_timer.stop()
        self.search_timer.start(300)  # 300ms延迟
    
    def _perform_search(self):
        """执行搜索"""
        query = self.search_input.text().strip()
        
        if not query:
            # 空搜索，显示所有对话
            self._update_conversation_list(self.conversations)
            self._update_stats_label(len(self.conversations))
            return
        
        if not self.storage_manager:
            return
        
        # 异步搜索
        UIUtils.run_async_task(
            self.storage_manager.search_conversations,
            self._on_search_results,
            self._on_search_error,
            query,
            20  # 最多返回20个结果
        )
    
    def _on_search_results(self, conversations):
        """搜索结果回调"""
        self._update_conversation_list(conversations)
        self._update_stats_label(len(conversations))
        
        logger.debug(f"搜索到 {len(conversations)} 个匹配的对话")
    
    def _on_search_error(self, error: str):
        """搜索错误回调"""
        logger.error(f"搜索对话失败: {error}")
    
    # 对话管理功能
    def _create_new_conversation(self):
        """创建新对话"""
        # 发送信号让主应用程序处理
        self.new_conversation.emit()
        logger.info("请求创建新对话")
    
    def _on_conversation_selected(self, item: QListWidgetItem):
        """处理对话选择"""
        if not isinstance(item, ConversationListItem):
            return
        
        conv_id = item.data(Qt.ItemDataRole.UserRole)
        self.current_conversation_id = conv_id
        
        # 发送信号
        self.conversation_selected.emit(conv_id)
        
        logger.debug(f"选择对话: {item.conversation.title} (ID: {conv_id})")
    
    def _on_conversation_double_clicked(self, item: QListWidgetItem):
        """对话双击处理 - 重命名"""
        if isinstance(item, ConversationListItem):
            self._rename_conversation(item)
    
    def _show_context_menu(self, position):
        """显示右键菜单"""
        item = self.conversation_list.itemAt(position)
        if not isinstance(item, ConversationListItem):
            return
        
        menu = QMenu(self)
        
        # 重命名
        rename_action = QAction("重命名", self)
        rename_action.triggered.connect(lambda: self._rename_conversation(item))
        menu.addAction(rename_action)
        
        # 删除
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self._delete_conversation(item))
        menu.addAction(delete_action)
        
        menu.addSeparator()
        
        # 导出
        export_action = QAction("导出对话", self)
        export_action.triggered.connect(lambda: self._export_conversation(item))
        menu.addAction(export_action)
        
        # 显示菜单
        menu.exec(self.conversation_list.mapToGlobal(position))
    
    def _rename_conversation(self, item: ConversationListItem):
        """重命名对话"""
        current_title = item.conversation.title
        
        new_title, ok = QInputDialog.getText(
            self, 
            "重命名对话", 
            "请输入新的对话标题:",
            QLineEdit.EchoMode.Normal,
            current_title
        )
        
        if ok and new_title.strip() and new_title.strip() != current_title:
            new_title = new_title.strip()
            
            # 更新对话标题
            item.conversation.title = new_title
            
            # 异步更新数据库
            if self.storage_manager:
                UIUtils.run_async_task(
                    self.storage_manager.update_conversation,
                    lambda _: self._on_conversation_renamed(item.conversation.id, new_title),
                    lambda error: logger.error(f"重命名对话失败: {error}"),
                    item.conversation
                )
            
            # 更新显示
            item.update_display()
    
    def _on_conversation_renamed(self, conversation_id: str, new_title: str):
        """对话重命名成功回调"""
        self.conversation_renamed.emit(conversation_id, new_title)
        logger.info(f"对话重命名成功: {new_title}")
    
    def _delete_conversation(self, item: ConversationListItem):
        """删除对话"""
        title = item.conversation.title
        
        reply = UIUtils.show_question_dialog(
            self,
            "确认删除",
            f"确定要删除对话 '{title}' 吗？\n\n此操作不可恢复。"
        )
        
        if reply:
            conv_id = item.conversation.id
            
            # 从列表中移除
            row = self.conversation_list.row(item)
            self.conversation_list.takeItem(row)
            
            # 从本地列表中移除
            self.conversations = [c for c in self.conversations if c.id != conv_id]
            self._update_stats_label(len(self.conversations))
            
            # 异步删除数据库记录
            if self.storage_manager:
                UIUtils.run_async_task(
                    self.storage_manager.delete_conversation,
                    lambda _: self._on_conversation_deleted(conv_id),
                    lambda error: logger.error(f"删除对话失败: {error}"),
                    conv_id
                )
            
            # 如果删除的是当前选中的对话，选择下一个
            if conv_id == self.current_conversation_id:
                if self.conversation_list.count() > 0:
                    next_item = self.conversation_list.item(0)
                    self.conversation_list.setCurrentItem(next_item)
                    self._on_conversation_selected(next_item)
                else:
                    self.current_conversation_id = None
                    self.new_conversation.emit()  # 创建新对话
    
    def _on_conversation_deleted(self, conversation_id: str):
        """对话删除成功回调"""
        self.conversation_deleted.emit(conversation_id)
        logger.info(f"对话删除成功: {conversation_id}")
    
    def _export_conversation(self, item: ConversationListItem):
        """导出对话"""
        # 这里可以实现导出功能，现在只是占位符
        UIUtils.show_info_message(
            self, 
            "导出对话", 
            f"导出功能正在开发中\n对话: {item.conversation.title}"
        )
    
    # 公共接口方法
    def add_new_conversation(self, conversation: Conversation):
        """添加新对话到列表"""
        self.conversations.insert(0, conversation)  # 添加到开头
        
        # 创建新的列表项
        item = ConversationListItem(conversation)
        self.conversation_list.insertItem(0, item)
        
        # 选中新对话
        self.conversation_list.setCurrentItem(item)
        self.current_conversation_id = conversation.id
        
        # 更新统计
        self._update_stats_label(len(self.conversations))
        
        logger.info(f"添加新对话到列表: {conversation.title}")
    
    def update_conversation(self, conversation_id: str, new_title: str = None):
        """更新对话信息"""
        # 更新本地列表
        for conv in self.conversations:
            if conv.id == conversation_id:
                if new_title:
                    conv.title = new_title
                conv.updated_at = datetime.now(timezone.utc)
                break
        
        # 更新UI显示
        for i in range(self.conversation_list.count()):
            item = self.conversation_list.item(i)
            if isinstance(item, ConversationListItem) and item.conversation.id == conversation_id:
                if new_title:
                    item.conversation.title = new_title
                item.conversation.updated_at = datetime.now(timezone.utc)
                item.update_display()
                break
    
    def refresh_conversations(self):
        """刷新对话列表"""
        self._load_conversations()
    
    def cleanup(self):
        """清理资源"""
        logger.info("正在清理侧边栏组件资源...")
        
        # 清理存储管理器
        if self.storage_manager:
            try:
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(self.storage_manager.cleanup())
                    else:
                        loop.run_until_complete(self.storage_manager.cleanup())
                except RuntimeError:
                    asyncio.run(self.storage_manager.cleanup())
            except Exception as e:
                logger.error(f"清理存储管理器失败: {e}")
        
        # 停止定时器
        if self.search_timer:
            self.search_timer.stop()
        
        logger.info("侧边栏组件资源清理完成") 