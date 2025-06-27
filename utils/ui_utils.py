"""
UI工具模块
提供用户界面相关的辅助功能和工具
"""

import asyncio
from typing import Callable, Any, Optional
from PyQt6.QtCore import QThread, pyqtSignal, QObject, QTimer
from PyQt6.QtWidgets import QMessageBox, QApplication, QWidget
from PyQt6.QtGui import QFont, QIcon
from loguru import logger


class AsyncWorker(QThread):
    """异步工作线程"""
    
    # 信号定义
    finished = pyqtSignal(object)  # 完成信号，携带结果
    error = pyqtSignal(str)       # 错误信号，携带错误信息
    progress = pyqtSignal(int)    # 进度信号，携带进度百分比
    
    def __init__(self, coro_func: Callable, *args, **kwargs):
        """
        初始化异步工作线程
        
        Args:
            coro_func: 异步函数
            *args: 函数位置参数
            **kwargs: 函数关键字参数
        """
        super().__init__()
        self.coro_func = coro_func
        self.args = args
        self.kwargs = kwargs
        self.result = None
        
    def run(self):
        """运行异步任务"""
        try:
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 运行异步函数
            self.result = loop.run_until_complete(
                self.coro_func(*self.args, **self.kwargs)
            )
            
            # 发出完成信号
            self.finished.emit(self.result)
            
        except Exception as e:
            logger.error(f"异步任务执行失败: {e}")
            self.error.emit(str(e))
        finally:
            # 清理事件循环
            try:
                loop.close()
            except:
                pass


class UIUtils:
    """UI工具类"""
    
    @staticmethod
    def show_info_message(parent: QWidget, title: str, message: str):
        """
        显示信息消息框
        
        Args:
            parent: 父窗口
            title: 标题
            message: 消息内容
        """
        QMessageBox.information(parent, title, message)
    
    @staticmethod
    def show_warning_message(parent: QWidget, title: str, message: str):
        """
        显示警告消息框
        
        Args:
            parent: 父窗口
            title: 标题
            message: 消息内容
        """
        QMessageBox.warning(parent, title, message)
    
    @staticmethod
    def show_error_message(parent: QWidget, title: str, message: str):
        """
        显示错误消息框
        
        Args:
            parent: 父窗口
            title: 标题
            message: 消息内容
        """
        QMessageBox.critical(parent, title, message)
    
    @staticmethod
    def show_question_dialog(parent: QWidget, title: str, message: str) -> bool:
        """
        显示询问对话框
        
        Args:
            parent: 父窗口
            title: 标题
            message: 消息内容
            
        Returns:
            bool: 用户是否选择了"是"
        """
        reply = QMessageBox.question(
            parent, title, message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        return reply == QMessageBox.StandardButton.Yes
    
    @staticmethod
    def run_async_task(parent: QObject, 
                      coro_func: Callable, 
                      on_finished: Optional[Callable[[Any], None]] = None,
                      on_error: Optional[Callable[[str], None]] = None,
                      *args, **kwargs) -> AsyncWorker:
        """
        运行异步任务, 并将其生命周期附加到父对象上
        
        Args:
            parent: 父QObject, 用于存储worker引用
            coro_func: 异步函数
            on_finished: 完成回调函数
            on_error: 错误回调函数
            *args: 函数位置参数
            **kwargs: 函数关键字参数
            
        Returns:
            AsyncWorker: 工作线程对象
        """
        worker = AsyncWorker(coro_func, *args, **kwargs)

        # 确保父对象有worker列表
        if not hasattr(parent, "_async_workers"):
            parent._async_workers = []
        
        # 添加worker到列表以保持引用
        parent._async_workers.append(worker)
        
        # 任务完成后从列表中移除worker
        def on_worker_done():
            if worker in parent._async_workers:
                parent._async_workers.remove(worker)
            logger.trace(f"Worker {id(worker)} finished and removed. "
                         f"Remaining workers for {parent.__class__.__name__}: {len(parent._async_workers)}")

        worker.finished.connect(on_worker_done)
        worker.error.connect(on_worker_done)
        
        # 连接用户提供的回调
        if on_finished:
            worker.finished.connect(on_finished)
        if on_error:
            worker.error.connect(on_error)
        
        worker.start()
        return worker
    
    @staticmethod
    def set_widget_style(widget: QWidget, style_sheet: str):
        """
        设置组件样式
        
        Args:
            widget: 目标组件
            style_sheet: CSS样式表
        """
        try:
            widget.setStyleSheet(style_sheet)
        except Exception as e:
            logger.error(f"设置组件样式失败: {e}")
    
    @staticmethod
    def set_font(widget: QWidget, family: str = None, size: int = None, 
                bold: bool = None, italic: bool = None):
        """
        设置组件字体
        
        Args:
            widget: 目标组件
            family: 字体族
            size: 字体大小
            bold: 是否加粗
            italic: 是否斜体
        """
        try:
            current_font = widget.font()
            
            if family is not None:
                current_font.setFamily(family)
            if size is not None:
                current_font.setPointSize(size)
            if bold is not None:
                current_font.setBold(bold)
            if italic is not None:
                current_font.setItalic(italic)
            
            widget.setFont(current_font)
            
        except Exception as e:
            logger.error(f"设置字体失败: {e}")
    
    @staticmethod
    def create_icon(icon_path: str) -> Optional[QIcon]:
        """
        创建图标
        
        Args:
            icon_path: 图标文件路径
            
        Returns:
            Optional[QIcon]: 图标对象，失败返回None
        """
        try:
            icon = QIcon(icon_path)
            if not icon.isNull():
                return icon
        except Exception as e:
            logger.error(f"创建图标失败: {e}")
        
        return None
    
    @staticmethod
    def center_widget(widget: QWidget, parent: QWidget = None):
        """
        居中显示组件
        
        Args:
            widget: 要居中的组件
            parent: 父组件，如果为None则相对于屏幕居中
        """
        try:
            if parent:
                # 相对于父组件居中
                parent_geometry = parent.geometry()
                x = parent_geometry.x() + (parent_geometry.width() - widget.width()) // 2
                y = parent_geometry.y() + (parent_geometry.height() - widget.height()) // 2
                widget.move(x, y)
            else:
                # 相对于屏幕居中
                screen = QApplication.primaryScreen()
                screen_geometry = screen.geometry()
                x = (screen_geometry.width() - widget.width()) // 2
                y = (screen_geometry.height() - widget.height()) // 2
                widget.move(x, y)
                
        except Exception as e:
            logger.error(f"居中组件失败: {e}")
    
    @staticmethod
    def apply_dark_theme(widget: QWidget):
        """
        应用深色主题
        
        Args:
            widget: 目标组件
        """
        dark_style = """
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
            font-family: 'Microsoft YaHei', 'Arial', sans-serif;
        }
        
        QTextEdit {
            background-color: #3c3c3c;
            border: 1px solid #5c5c5c;
            border-radius: 5px;
            padding: 8px;
            selection-background-color: #4CAF50;
        }
        
        QLineEdit {
            background-color: #3c3c3c;
            border: 1px solid #5c5c5c;
            border-radius: 5px;
            padding: 8px;
            selection-background-color: #4CAF50;
        }
        
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 16px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #45a049;
        }
        
        QPushButton:pressed {
            background-color: #3d8b40;
        }
        
        QPushButton:disabled {
            background-color: #666666;
            color: #999999;
        }
        
        QMenuBar {
            background-color: #3c3c3c;
            color: #ffffff;
            border-bottom: 1px solid #5c5c5c;
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
            spacing: 2px;
        }
        
        QStatusBar {
            background-color: #3c3c3c;
            color: #ffffff;
            border-top: 1px solid #5c5c5c;
        }
        
        QSplitter::handle {
            background-color: #5c5c5c;
        }
        
        QScrollBar:vertical {
            background-color: #3c3c3c;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #5c5c5c;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #6c6c6c;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            border: none;
            background: none;
        }
        """
        
        UIUtils.set_widget_style(widget, dark_style)
    
    @staticmethod
    def apply_light_theme(widget: QWidget):
        """
        应用亮色主题
        
        Args:
            widget: 目标组件
        """
        light_style = """
        QWidget {
            background-color: #ffffff;
            color: #333333;
            font-family: 'Microsoft YaHei', 'Arial', sans-serif;
        }
        
        QTextEdit {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            border-radius: 5px;
            padding: 8px;
            selection-background-color: #4CAF50;
        }
        
        QLineEdit {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            border-radius: 5px;
            padding: 8px;
            selection-background-color: #4CAF50;
        }
        
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 16px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #45a049;
        }
        
        QPushButton:pressed {
            background-color: #3d8b40;
        }
        
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
        }
        
        QMenuBar {
            background-color: #f5f5f5;
            color: #333333;
            border-bottom: 1px solid #cccccc;
        }
        
        QMenuBar::item {
            background-color: transparent;
            padding: 4px 8px;
        }
        
        QMenuBar::item:selected {
            background-color: #e0e0e0;
        }
        
        QMenu {
            background-color: #ffffff;
            color: #333333;
            border: 1px solid #cccccc;
        }
        
        QMenu::item:selected {
            background-color: #e0e0e0;
        }
        
        QToolBar {
            background-color: #f5f5f5;
            border: 1px solid #cccccc;
            spacing: 2px;
        }
        
        QStatusBar {
            background-color: #f5f5f5;
            color: #333333;
            border-top: 1px solid #cccccc;
        }
        
        QSplitter::handle {
            background-color: #cccccc;
        }
        
        QScrollBar:vertical {
            background-color: #f5f5f5;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #cccccc;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #999999;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            border: none;
            background: none;
        }
        """
        
        UIUtils.set_widget_style(widget, light_style)
    
    @staticmethod
    def create_loading_indicator(parent: QWidget, message: str = "处理中...") -> QTimer:
        """
        创建加载指示器
        
        Args:
            parent: 父组件
            message: 加载消息
            
        Returns:
            QTimer: 定时器对象
        """
        # 这是一个简化的实现，实际应用中可以创建更复杂的加载动画
        timer = QTimer(parent)
        dots = [".", "..", "..."]
        counter = [0]  # 使用列表来避免闭包变量问题
        
        def update_message():
            if hasattr(parent, 'statusBar'):
                status_text = f"{message}{dots[counter[0] % len(dots)]}"
                parent.statusBar().showMessage(status_text)
                counter[0] += 1
        
        timer.timeout.connect(update_message)
        timer.start(500)  # 每500ms更新一次
        
        return timer
    
    @staticmethod
    def stop_loading_indicator(timer: QTimer, parent: QWidget, final_message: str = "完成"):
        """
        停止加载指示器
        
        Args:
            timer: 定时器对象
            parent: 父组件
            final_message: 最终显示的消息
        """
        if timer:
            timer.stop()
        
        if hasattr(parent, 'statusBar'):
            parent.statusBar().showMessage(final_message, 2000)


class CallbackManager(QObject):
    """回调管理器，用于管理异步回调"""
    
    # 信号定义
    callback_triggered = pyqtSignal(str, object)
    
    def __init__(self):
        super().__init__()
        self.callbacks = {}
    
    def register_callback(self, name: str, callback: Callable):
        """
        注册回调函数
        
        Args:
            name: 回调名称
            callback: 回调函数
        """
        self.callbacks[name] = callback
        logger.debug(f"注册回调: {name}")
    
    def trigger_callback(self, name: str, data: Any = None):
        """
        触发回调
        
        Args:
            name: 回调名称
            data: 传递给回调的数据
        """
        if name in self.callbacks:
            try:
                self.callbacks[name](data)
                self.callback_triggered.emit(name, data)
                logger.debug(f"触发回调: {name}")
            except Exception as e:
                logger.error(f"回调执行失败 {name}: {e}")
        else:
            logger.warning(f"未找到回调: {name}")
    
    def remove_callback(self, name: str):
        """
        移除回调
        
        Args:
            name: 回调名称
        """
        if name in self.callbacks:
            del self.callbacks[name]
            logger.debug(f"移除回调: {name}") 