#!/bin/bash
# RPChat 启动脚本
# 提供多种运行方式选择

echo "🚀 RPChat 智能语音对话应用启动脚本"
echo "======================================"

# 检查虚拟环境
if [[ "$VIRTUAL_ENV" != *"RPChat"* ]]; then
    echo "📂 激活虚拟环境..."
    source .venv/bin/activate
fi

echo "📋 请选择运行方式:"
echo "1. 本地显示器运行 (推荐，如果树莓派连接了显示器)"
echo "2. 虚拟显示运行 (适合无头运行和测试)"
echo "3. SSH X11转发运行 (适合远程使用)"
echo "4. 仅运行功能测试"
echo "5. 退出"

read -p "请输入选择 (1-5): " choice

case $choice in
    1)
        echo "🖥️  使用本地显示器运行..."
        export DISPLAY=:0
        python main.py
        ;;
    2)
        echo "🖥️  启动虚拟显示..."
        # 检查是否已有Xvfb运行
        if pgrep Xvfb > /dev/null; then
            echo "Xvfb 已在运行"
        else
            Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
            sleep 2
            echo "虚拟显示已启动"
        fi
        export DISPLAY=:99
        python main.py
        ;;
    3)
        echo "🌐 SSH X11转发模式..."
        echo "请确保您的SSH连接使用了 -X 或 -Y 参数"
        echo "例如: ssh -X user@$(hostname -I | awk '{print $1}')"
        if [ -z "$DISPLAY" ]; then
            echo "警告: DISPLAY 环境变量未设置"
            echo "如果您使用的是SSH X11转发，请检查SSH配置"
        fi
        python main.py
        ;;
    4)
        echo "🧪 运行功能测试..."
        echo "使用offscreen模式测试应用程序功能..."
        QT_QPA_PLATFORM=offscreen python -c "
from core.config_manager import ConfigManager
from ui.main_window import MainWindow
from PyQt6.QtWidgets import QApplication
import sys
app = QApplication(sys.argv)
config = ConfigManager()
config.load_config()
window = MainWindow(config)
print(f'✓ 应用程序测试成功: {config.get(\"application.name\")} v{config.get(\"application.version\")}')
print(f'✓ API配置: {config.get(\"api.model\")} @ {config.get(\"api.base_url\")}')
print(f'✓ 主题设置: {config.get(\"ui.theme\")}')
window.cleanup()
app.quit()
"
        ;;
    5)
        echo "👋 退出"
        exit 0
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo "🔄 应用程序已退出" 