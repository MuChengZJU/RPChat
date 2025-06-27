"""
主窗口模块
RPChat应用程序的主用户界面
"""

import sys
import os
import asyncio
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QMenuBar, QStatusBar, QToolBar,
    QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QKeySequence, QAction, QFontDatabase
from loguru import logger

from ui.chat_widget import ChatWidget
from ui.sidebar_widget import SidebarWidget
from core.api_client import OpenAIAPIClient
from core.storage_manager import StorageManager
from core.voice_handler import VoiceHandler
from utils.ui_utils import UIUtils


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
        logger.info("开始初始化主窗口...")
        
        self.config = config_manager
        self.api_client = None
        self.storage_manager = None
        self.voice_handler = None
        self.chat_widget = None
        self.sidebar_widget = None
        
        # 异步任务管理
        self.async_timer = QTimer()
        self.async_timer.timeout.connect(self._process_async_tasks)
        self.async_timer.start(50)  # 50ms间隔处理异步任务
        
        try:
            # 初始化核心组件
            logger.info("初始化核心组件...")
            self._init_core_components()
            
            # 加载自定义字体
            logger.info("加载自定义字体...")
            self._load_custom_font()
            
            # 设置窗口
            logger.info("设置窗口属性...")
            self._setup_window()
            
            # 创建菜单栏
            logger.info("创建菜单栏...")
            self._create_menu_bar()
            
            # 创建主要UI布局
            logger.info("创建主要UI布局...")
            self._setup_ui()
            
            # 连接信号
            logger.info("连接组件信号...")
            self._connect_component_signals()
            
            # 设置异步任务处理
            logger.info("设置异步任务处理...")
            self._setup_async_processing()
            
            # 应用样式
            logger.info("应用窗口样式...")
            self._apply_theme()
            
            logger.info("主窗口初始化完成")
            
        except Exception as e:
            logger.error(f"主窗口初始化失败: {e}")
            import traceback
            logger.error(f"详细错误信息:\n{traceback.format_exc()}")
            raise
    
    def _load_custom_font(self):
        """加载自定义字体"""
        font_path = "assets/MiSans VF.ttf"
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                font_families = QFontDatabase.applicationFontFamilies(font_id)
                if font_families:
                    logger.info(f"成功加载字体: {font_families[0]} from {font_path}")
                else:
                    logger.warning(f"成功加载字体文件 {font_path}, 但未能获取字体家族名称。")
            else:
                logger.error(f"加载字体文件失败: {font_path}")
        else:
            logger.warning(f"字体文件未找到: {font_path}，将使用系统默认字体。")
    
    def _init_core_components(self):
        """初始化核心组件"""
        logger.info("开始初始化核心组件...")
        
        try:
        # 初始化API客户端
            logger.info("正在初始化API客户端...")
            self.api_client = OpenAIAPIClient(self.config)
            logger.info("API客户端初始化成功")
            
            # 初始化存储管理器
            self._init_storage_manager()
            
            # 初始化语音处理器
            self._init_voice_handler()
            
            logger.info("核心组件初始化完成")
            
        except Exception as e:
            logger.error(f"核心组件初始化失败: {e}")
            raise
    
    def _setup_window(self):
        """设置窗口属性"""
        try:
            # 设置窗口属性
            self.setWindowTitle("RPChat - 智能语音对话")
            
            # 设置中央widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # 设置窗口大小和位置
            width = self.config.get("ui.window_width", 1000)
            height = self.config.get("ui.window_height", 700)
            self.resize(width, height)
            
            x = self.config.get("ui.window_position_x", 100)
            y = self.config.get("ui.window_position_y", 100)
            self.move(x, y)
            
            # 设置状态栏
            status_bar = QStatusBar()
            self.setStatusBar(status_bar)
            
            # 显示应用信息
            app_name = self.config.get("application.name", "RPChat")
            app_version = self.config.get("application.version", "1.0.0")
            status_bar.showMessage(f"{app_name} v{app_version} - 就绪")
            
            logger.info("窗口属性设置完成")
            
        except Exception as e:
            logger.error(f"设置窗口属性失败: {e}")
            raise
    
    def _create_menu_bar(self):
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
        
        # 添加语音模式切换选项
        voice_mode_action = QAction("启用语音模式(&V)", self)
        voice_mode_action.setShortcut(QKeySequence("Ctrl+Space"))
        voice_mode_action.setCheckable(True)
        voice_mode_action.setChecked(False)  # 默认关闭
        voice_mode_action.triggered.connect(self._toggle_voice_mode)
        tools_menu.addAction(voice_mode_action)
        
        tools_menu.addSeparator()
        
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
    
    def _setup_ui(self):
        """创建主要UI布局"""
        # 创建主布局
        main_layout = QHBoxLayout(self.centralWidget())
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建分隔器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 创建侧边栏
        self.sidebar_widget = SidebarWidget(self.config)
        splitter.addWidget(self.sidebar_widget)
        
        # 创建聊天区域
        self.chat_widget = ChatWidget(self.config)
        
        # 将API客户端传递给聊天组件
        if self.api_client:
            self.chat_widget.set_api_client(self.api_client)
            logger.debug("API客户端已传递给聊天组件")
        else:
            logger.warning("API客户端未初始化，聊天功能将受限")
            
        splitter.addWidget(self.chat_widget)
        
        # 设置分隔器比例
        splitter.setSizes([250, 750])  # 侧边栏:聊天区域 = 1:3
        
        # 连接信号
        self._connect_signals()
    
    def _connect_signals(self):
        """连接信号和槽"""
        if self.chat_widget:
            # 连接聊天相关信号
            self.chat_widget.message_sent.connect(self._handle_message_sent)
            
        if self.sidebar_widget:
            # 连接侧边栏相关信号
            self.sidebar_widget.conversation_selected.connect(self._handle_conversation_selected)
            self.sidebar_widget.new_conversation.connect(self._new_chat)
    
    def _init_storage_manager(self):
        """初始化存储管理器"""
        try:
            logger.info("正在初始化主窗口存储管理器...")
            self.storage_manager = StorageManager(self.config)
            logger.info("主窗口存储管理器初始化成功")
        except Exception as e:
            logger.error(f"主窗口存储管理器初始化失败: {e}")
            self.storage_manager = None
            UIUtils.show_error_message(self, "存储管理器初始化失败", 
                                     f"数据存储功能将不可用: {e}")
    
    def _init_voice_handler(self):
        """初始化语音处理器"""
        try:
            logger.info("正在初始化主窗口语音处理器...")
            self.voice_handler = VoiceHandler(self.config)
            # 不在这里初始化，让各个组件自己处理
            logger.info("主窗口语音处理器创建成功")
        except Exception as e:
            logger.warning(f"主窗口语音处理器初始化失败: {e}")
            self.voice_handler = None
            # 语音功能失败不应该阻止应用程序启动
    
    def _connect_component_signals(self):
        """连接组件间的信号"""
        try:
            if self.chat_widget and self.sidebar_widget:
                # 侧边栏信号连接
                self.sidebar_widget.conversation_selected.connect(self.chat_widget.load_conversation)
                self.sidebar_widget.new_conversation.connect(self.chat_widget.new_conversation)
                
                # 聊天组件信号连接
                self.chat_widget.conversation_updated.connect(self._on_conversation_updated)
                
                logger.debug("组件间信号连接完成")
        except Exception as e:
            logger.error(f"连接组件信号失败: {e}")
            # 信号连接失败不应该阻止应用程序启动
    
    def _process_async_tasks(self):
        """处理异步任务（在主线程中调用）"""
        # 这里可以处理需要在主线程中执行的异步任务回调
        pass
    
    # 事件处理方法
    def _on_conversation_updated(self, conversation_id: str):
        """对话更新事件处理"""
        if self.sidebar_widget:
            # 通知侧边栏更新对应的对话项
            self.sidebar_widget.update_conversation(conversation_id)
        logger.debug(f"对话已更新: {conversation_id}")
    
    # 菜单动作处理
    def _new_chat(self):
        """新建对话"""
        if self.chat_widget:
            self.chat_widget.new_conversation()
        
        self.statusBar().showMessage("正在创建新对话...", 2000)
    
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
        
        # 更新菜单项文本
        sender = self.sender()
        if sender and hasattr(sender, 'setText'):
            text = "禁用语音模式(&V)" if checked else "启用语音模式(&V)"
            sender.setText(text)
        
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
            UIUtils.show_warning_message(self, "警告", "API客户端未初始化")
            return
        
        self.statusBar().showMessage("正在测试API连接...")
        
        # 使用异步工具测试API连接
        UIUtils.run_async_task(
            self,
            self.api_client.test_connection,
            self._on_api_test_finished,
            self._on_api_test_error
        )
    
    def _on_api_test_finished(self, success: bool):
        """API测试完成回调"""
        if success:
            UIUtils.show_info_message(self, "API测试", "API连接测试成功！")
            self.statusBar().showMessage("API连接正常", 3000)
        else:
            UIUtils.show_error_message(self, "API测试", "API连接测试失败")
            self.statusBar().showMessage("API连接失败", 3000)
    
    def _on_api_test_error(self, error: str):
        """API测试错误回调"""
        UIUtils.show_error_message(self, "API测试失败", f"测试过程中出错：{error}")
        self.statusBar().showMessage("API测试错误", 3000)
    
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
    
    def cleanup(self):
        """清理资源"""
        logger.info("正在清理主窗口资源...")
        
        try:
            # 停止定时器
            if hasattr(self, 'async_timer') and self.async_timer:
                self.async_timer.stop()
                logger.debug("异步定时器已停止")
            
            # 清理聊天组件
            if hasattr(self, 'chat_widget') and self.chat_widget:
                try:
                    self.chat_widget.cleanup()
                    logger.debug("聊天组件清理完成")
                except Exception as e:
                    logger.error(f"清理聊天组件时出错: {e}")
            
            # 清理侧边栏组件
            if hasattr(self, 'sidebar_widget') and self.sidebar_widget:
                try:
                    self.sidebar_widget.cleanup()
                    logger.debug("侧边栏组件清理完成")
                except Exception as e:
                    logger.error(f"清理侧边栏组件时出错: {e}")
            
            # 清理语音处理器
            if hasattr(self, 'voice_handler') and self.voice_handler:
                try:
                    self.voice_handler.cleanup()
                    logger.debug("语音处理器清理完成")
                except Exception as e:
                    logger.error(f"清理语音处理器时出错: {e}")
            
            # 清理存储管理器
            if hasattr(self, 'storage_manager') and self.storage_manager:
                try:
                    asyncio.run(self.storage_manager.cleanup())
                    logger.debug("存储管理器清理完成")
                except Exception as e:
                    logger.error(f"清理存储管理器时出错: {e}")
            
            # 确保所有子组件都被清理
            for child in self.findChildren(QWidget):
                if hasattr(child, 'cleanup'):
                    try:
                        child.cleanup()
                    except Exception as e:
                        logger.error(f"清理子组件 {child.__class__.__name__} 时出错: {e}")
            
            logger.info("主窗口资源清理完成")
            
        except Exception as e:
            logger.error(f"主窗口清理过程中出现错误: {e}")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        logger.info("主窗口正在关闭...")
        try:
            self.cleanup()
            event.accept()
        except Exception as e:
            logger.error(f"窗口关闭过程中出现错误: {e}")
            event.accept()  # 即使清理失败也要关闭窗口

    def _setup_async_processing(self):
        """设置异步任务处理"""
        try:
            logger.info("正在设置异步任务处理...")
            self.async_timer = QTimer(self)
            self.async_timer.timeout.connect(self._process_async_tasks)
            self.async_timer.start(50)  # 50ms间隔处理异步任务
            logger.info("异步任务处理设置完成")
        except Exception as e:
            logger.error(f"设置异步任务处理失败: {e}")
    
    def _apply_theme(self):
        """应用主题样式"""
        try:
            logger.info("正在应用主题样式...")
            theme = self.config.get("ui.theme", "dark")
            
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
                
            logger.info(f"主题样式应用完成: {theme}")
            
        except Exception as e:
            logger.error(f"应用主题失败: {e}")