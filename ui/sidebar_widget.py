"""
侧边栏组件模块
显示对话列表和会话管理功能
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
    QListWidgetItem, QPushButton, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from loguru import logger


class SidebarWidget(QWidget):
    """侧边栏组件类"""
    
    # 信号定义
    conversation_selected = pyqtSignal(str)
    new_conversation = pyqtSignal()
    
    def __init__(self, config_manager):
        """
        初始化侧边栏组件
        
        Args:
            config_manager: 配置管理器实例
        """
        super().__init__()
        
        self.config = config_manager
        self.conversations = []
        
        self._init_ui()
        self._apply_config()
        
        logger.info("侧边栏组件初始化完成")
    
    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("对话历史")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 新建对话按钮
        new_chat_button = QPushButton("新建对话")
        new_chat_button.clicked.connect(self._create_new_conversation)
        layout.addWidget(new_chat_button)
        
        # 对话列表
        self.conversation_list = QListWidget()
        self.conversation_list.itemClicked.connect(self._on_conversation_selected)
        layout.addWidget(self.conversation_list)
        
        # 添加一些示例对话
        self._add_sample_conversations()
    
    def _apply_config(self):
        """应用配置设置"""
        # 字体设置
        font_family = self.config.get("ui.font_family", "Microsoft YaHei")
        font_size = self.config.get("ui.font_size", 12)
        
        font = QFont(font_family, font_size)
        self.conversation_list.setFont(font)
    
    def _add_sample_conversations(self):
        """添加示例对话"""
        sample_conversations = [
            "默认对话",
            "关于Python编程",
            "树莓派项目讨论"
        ]
        
        for i, title in enumerate(sample_conversations):
            self._add_conversation_item(f"conv_{i}", title)
    
    def _add_conversation_item(self, conv_id: str, title: str):
        """
        添加对话项目
        
        Args:
            conv_id: 对话ID
            title: 对话标题
        """
        item = QListWidgetItem(title)
        item.setData(Qt.ItemDataRole.UserRole, conv_id)
        self.conversation_list.addItem(item)
        
        # 如果是第一个项目，设为选中状态
        if self.conversation_list.count() == 1:
            self.conversation_list.setCurrentItem(item)
    
    def _create_new_conversation(self):
        """创建新对话"""
        conv_count = self.conversation_list.count()
        conv_id = f"conv_{conv_count}"
        title = f"新对话 {conv_count + 1}"
        
        self._add_conversation_item(conv_id, title)
        
        # 选中新创建的对话
        new_item = self.conversation_list.item(self.conversation_list.count() - 1)
        self.conversation_list.setCurrentItem(new_item)
        
        # 发送信号
        self.new_conversation.emit()
        
        logger.info(f"创建新对话: {title}")
    
    def _on_conversation_selected(self, item: QListWidgetItem):
        """
        处理对话选择
        
        Args:
            item: 选中的列表项
        """
        conv_id = item.data(Qt.ItemDataRole.UserRole)
        title = item.text()
        
        # 发送信号
        self.conversation_selected.emit(conv_id)
        
        logger.debug(f"选择对话: {title} (ID: {conv_id})")
    
    def add_new_conversation(self):
        """添加新对话（外部调用）"""
        self._create_new_conversation()
    
    def cleanup(self):
        """清理资源"""
        logger.info("正在清理侧边栏组件资源...")
        # 清理相关资源 