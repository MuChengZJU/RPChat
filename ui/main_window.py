"""
主窗口模块
RPChat应用程序的主用户界面
"""

import sys
import asyncio
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QMenuBar, QStatusBar, QToolBar,
    QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QKeySequence, QAction
from loguru import logger

from ui.chat_widget import ChatWidget
from ui.sidebar_widget import SidebarWidget
from core.api_client import OpenAIAPIClient


class MainWindow(QMainWindow):
    """主窗口类"""
    
    # 信号定义
    config_changed = pyqtSignal()
    
    def __init__(self, config_manager):
        """
        初始化主窗口
        
        Args:
            config_manager: 配置管理器实例
        """
        super().__init__()
        
        self.config = config_manager
        self.api_client = None
        self.chat_widget = None
        self.sidebar_widget = None
        
        # 异步任务管理
        self.async_timer = QTimer()
        self.async_timer.timeout.connect(self._process_async_tasks)
        self.async_timer.start(50)  # 50ms间隔处理异步任务
        
        self._init_ui()
        self._init_menu_bar()
        self._init_tool_bar()
        self._init_status_bar()
        self._apply_config()
        
        # 初始化API客户端
        self._init_api_client()
        
        logger.info("主窗口初始化完成")
    
    def _init_ui(self):
        """初始化用户界面"""
        # 设置窗口属性
        self.setWindowTitle("RPChat - 智能语音对话")
        self.setMinimumSize(QSize(800, 600))
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建分隔器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 创建侧边栏
        self.sidebar_widget = SidebarWidget(self.config)
        splitter.addWidget(self.sidebar_widget)
        
        # 创建聊天区域
        self.chat_widget = ChatWidget(self.config)
        splitter.addWidget(self.chat_widget)
        
        # 设置分隔器比例
        splitter.setSizes([250, 750])  # 侧边栏:聊天区域 = 1:3
        
        # 连接信号
        self._connect_signals()
    
    def _init_menu_bar(self):
        """初始化菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        new_chat_action = QAction("新建对话(&N)", self)
        new_chat_action.setShortcut(QKeySequence("Ctrl+N"))
        new_chat_action.triggered.connect(self._new_chat)
        file_menu.addAction(new_chat_action)
        
        save_chat_action = QAction("保存对话(&S)", self)
        save_chat_action.setShortcut(QKeySequence("Ctrl+S"))
        save_chat_action.triggered.connect(self._save_chat)
        file_menu.addAction(save_chat_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")
        
        clear_chat_action = QAction("清空对话(&C)", self)
        clear_chat_action.setShortcut(QKeySequence("Ctrl+L"))
        clear_chat_action.triggered.connect(self._clear_chat)
        edit_menu.addAction(clear_chat_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")
        
        settings_action = QAction("设置(&S)", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self._show_settings)
        tools_menu.addAction(settings_action)
        
        test_api_action = QAction("测试API连接(&A)", self)
        test_api_action.triggered.connect(self._test_api_connection)
        tools_menu.addAction(test_api_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _init_tool_bar(self):
        """初始化工具栏"""
        toolbar = QToolBar("主工具栏")
        self.addToolBar(toolbar)
        
        # 新建对话按钮
        new_chat_action = QAction("新建对话", self)
        new_chat_action.triggered.connect(self._new_chat)
        toolbar.addAction(new_chat_action)
        
        # 保存对话按钮
        save_chat_action = QAction("保存对话", self)
        save_chat_action.triggered.connect(self._save_chat)
        toolbar.addAction(save_chat_action)
        
        toolbar.addSeparator()
        
        # 语音切换按钮
        voice_toggle_action = QAction("语音模式", self)
        voice_toggle_action.setCheckable(True)
        voice_toggle_action.triggered.connect(self._toggle_voice_mode)
        toolbar.addAction(voice_toggle_action)
        
        toolbar.addSeparator()
        
        # 设置按钮
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self._show_settings)
        toolbar.addAction(settings_action)
    
    def _init_status_bar(self):
        """初始化状态栏"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # 显示应用信息
        app_name = self.config.get("application.name", "RPChat")
        app_version = self.config.get("application.version", "1.0.0")
        status_bar.showMessage(f"{app_name} v{app_version} - 就绪")
    
    def _apply_config(self):
        """应用配置设置"""
        # 窗口大小和位置
        width = self.config.get("ui.window_width", 1000)
        height = self.config.get("ui.window_height", 700)
        self.resize(width, height)
        
        x = self.config.get("ui.window_position_x", 100)
        y = self.config.get("ui.window_position_y", 100)
        self.move(x, y)
        
        # 应用主题
        theme = self.config.get("ui.theme", "dark")
        self._apply_theme(theme)
    
    def _apply_theme(self, theme: str):
        """
        应用主题样式
        
        Args:
            theme: 主题名称 ("dark" 或 "light")
        """
        try:
            if theme == "dark":
                # 简单的深色主题
                dark_style = """
                QMainWindow {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QMenuBar {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #5c5c5c;
                }
                QMenuBar::item {
                    background-color: transparent;
                    padding: 4px 8px;
                }
                QMenuBar::item:selected {
                    background-color: #5c5c5c;
                }
                QMenu {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #5c5c5c;
                }
                QMenu::item:selected {
                    background-color: #5c5c5c;
                }
                QToolBar {
                    background-color: #3c3c3c;
                    border: 1px solid #5c5c5c;
                }
                QStatusBar {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #5c5c5c;
                }
                """
                self.setStyleSheet(dark_style)
            else:
                # 使用默认的亮色主题
                self.setStyleSheet("")
                
            logger.debug(f"已应用主题: {theme}")
            
        except Exception as e:
            logger.error(f"应用主题失败: {e}")
    
    def _connect_signals(self):
        """连接信号和槽"""
        if self.chat_widget:
            # 连接聊天相关信号
            self.chat_widget.message_sent.connect(self._handle_message_sent)
            
        if self.sidebar_widget:
            # 连接侧边栏相关信号
            self.sidebar_widget.conversation_selected.connect(self._handle_conversation_selected)
            self.sidebar_widget.new_conversation.connect(self._new_chat)
    
    def _init_api_client(self):
        """初始化API客户端"""
        try:
            self.api_client = OpenAIAPIClient(self.config)
            logger.info("API客户端初始化成功")
            
            # 将API客户端传递给聊天组件
            if self.chat_widget:
                self.chat_widget.set_api_client(self.api_client)
                
        except Exception as e:
            logger.error(f"API客户端初始化失败: {e}")
            self._show_error_message("API客户端初始化失败", str(e))
    
    def _process_async_tasks(self):
        """处理异步任务（在主线程中调用）"""
        # 这里可以处理需要在主线程中执行的异步任务回调
        pass
    
    # 菜单动作处理
    def _new_chat(self):
        """新建对话"""
        if self.chat_widget:
            self.chat_widget.new_conversation()
        
        if self.sidebar_widget:
            self.sidebar_widget.add_new_conversation()
        
        self.statusBar().showMessage("已创建新对话", 2000)
    
    def _save_chat(self):
        """保存对话"""
        if self.chat_widget:
            success = self.chat_widget.save_conversation()
            if success:
                self.statusBar().showMessage("对话已保存", 2000)
            else:
                self.statusBar().showMessage("保存失败", 2000)
    
    def _clear_chat(self):
        """清空对话"""
        if self.chat_widget:
            reply = QMessageBox.question(
                self, "确认清空", "确定要清空当前对话吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.chat_widget.clear_conversation()
                self.statusBar().showMessage("对话已清空", 2000)
    
    def _toggle_voice_mode(self, checked: bool):
        """切换语音模式"""
        if self.chat_widget:
            self.chat_widget.set_voice_mode(checked)
        
        mode = "语音模式" if checked else "文本模式"
        self.statusBar().showMessage(f"已切换到{mode}", 2000)
    
    def _show_settings(self):
        """显示设置对话框"""
        try:
            from ui.settings_dialog import SettingsDialog
            dialog = SettingsDialog(self.config, self)
            
            if dialog.exec() == dialog.DialogCode.Accepted:
                # 配置已更新，重新应用
                self._apply_config()
                self.config_changed.emit()
                
                # 更新API客户端配置
                if self.api_client:
                    self.api_client.update_config(self.config)
                
                self.statusBar().showMessage("设置已更新", 2000)
                
        except ImportError:
            # 设置对话框还未实现
            QMessageBox.information(self, "提示", "设置功能正在开发中...")
    
    def _test_api_connection(self):
        """测试API连接"""
        if not self.api_client:
            QMessageBox.warning(self, "警告", "API客户端未初始化")
            return
        
        self.statusBar().showMessage("正在测试API连接...")
        
        # 这里应该使用异步方式测试，简化处理先显示消息
        QMessageBox.information(self, "API测试", "API连接测试功能正在开发中...")
        self.statusBar().showMessage("就绪", 2000)
    
    def _show_about(self):
        """显示关于对话框"""
        app_name = self.config.get("application.name", "RPChat")
        app_version = self.config.get("application.version", "1.0.0")
        
        about_text = f"""
        <h3>{app_name}</h3>
        <p>版本: {app_version}</p>
        <p>基于PyQt6的智能语音对话前端</p>
        <p>专为树莓派4B优化</p>
        <p><br/>© 2024 RPChat Team</p>
        """
        
        QMessageBox.about(self, f"关于 {app_name}", about_text)
    
    # 信号处理
    def _handle_message_sent(self, message: str):
        """处理发送的消息"""
        logger.debug(f"用户发送消息: {message}")
        self.statusBar().showMessage("正在处理消息...", 1000)
    
    def _handle_conversation_selected(self, conversation_id: str):
        """处理选择的对话"""
        logger.debug(f"选择对话: {conversation_id}")
        if self.chat_widget:
            self.chat_widget.load_conversation(conversation_id)
    
    def _show_error_message(self, title: str, message: str):
        """显示错误消息"""
        QMessageBox.critical(self, title, message)
    
    # 窗口事件处理
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 保存窗口状态
        self.config.set("ui.window_width", self.width())
        self.config.set("ui.window_height", self.height())
        self.config.set("ui.window_position_x", self.x())
        self.config.set("ui.window_position_y", self.y())
        self.config.save_config()
        
        self.cleanup()
        event.accept()
    
    def cleanup(self):
        """清理资源"""
        logger.info("正在清理主窗口资源...")
        
        # 停止异步任务定时器
        if self.async_timer:
            self.async_timer.stop()
        
        # 清理API客户端
        if self.api_client:
            try:
                # 尝试在现有事件循环中创建任务
                asyncio.create_task(self.api_client.cleanup())
            except RuntimeError:
                # 如果没有运行的事件循环，直接调用清理方法
                asyncio.run(self.api_client.cleanup())
        
        # 清理子组件
        if self.chat_widget:
            self.chat_widget.cleanup()
        
        if self.sidebar_widget:
            self.sidebar_widget.cleanup()
        
        logger.info("主窗口资源清理完成") 