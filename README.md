# RPChat - 基于PyQt的智能语音对话前端

一个专为树莓派4B优化的LLM对话前端应用，支持语音和文本双模式交互，提供类ChatGPT的用户体验。

## 📋 项目概述

**部署平台：** 树莓派4B Ubuntu  
**开发平台：** M4 Mac  
**包管理：** uv  
**界面框架：** PyQt6  
**设计风格：** 现代化、响应式，兼容多种分辨率

## ✨ 核心功能

### 🎯 已规划功能
- **智能对话**
  - 文本对话：实时文字交互
  - 语音对话：语音输入 + TTS语音输出
  - 多轮对话上下文保持
  
- **本地存储**
  - 对话历史本地保存
  - 会话管理（新建、删除、重命名）
  - 数据导入导出功能

- **API集成**
  - 完全兼容OpenAI API标准
  - 支持云服务器和局域网LLM服务
  - 可配置API端点和认证

- **用户界面**
  - 响应式设计，适配不同屏幕尺寸
  - 暗色/亮色主题切换
  - 可自定义字体大小和颜色

### 🚀 扩展功能（后期版本）
- 插件系统支持
- 多语言界面
- 语音情感识别
- 对话数据分析和可视化

## 🏗️ 技术架构

### 核心模块设计
```
RPChat/
├── core/                   # 核心业务逻辑
│   ├── api_client.py      # LLM API客户端
│   ├── voice_handler.py   # 语音处理模块
│   ├── storage_manager.py # 数据存储管理
│   └── config_manager.py  # 配置管理
├── ui/                    # 用户界面
│   ├── main_window.py     # 主窗口
│   ├── chat_widget.py     # 对话组件
│   ├── settings_dialog.py # 设置界面
│   └── components/        # UI组件
├── utils/                 # 工具函数
│   ├── audio_utils.py     # 音频处理工具
│   ├── text_utils.py      # 文本处理工具
│   └── system_utils.py    # 系统工具
├── resources/             # 资源文件
│   ├── themes/           # 主题样式
│   ├── icons/            # 图标资源
│   └── sounds/           # 音效文件
└── tests/                # 测试代码
```

### 技术栈选择
- **界面框架：** PyQt6 - 跨平台、性能优秀
- **语音识别：** OpenAI Whisper API / 本地语音识别
- **语音合成：** 本地TTS引擎（考虑树莓派性能）
- **数据存储：** SQLite - 轻量级本地数据库
- **HTTP客户端：** aiohttp - 异步网络请求
- **配置管理：** TOML格式配置文件

## 📅 开发计划

### Phase 1: 基础架构（1-2周）
- [x] 项目初始化和环境配置
- [ ] 基本的PyQt6应用框架
- [ ] OpenAI API客户端实现
- [ ] 简单的文本对话界面
- [ ] 基础配置管理系统

### Phase 2: 核心功能（2-3周）
- [ ] 完整的对话界面设计
- [ ] 语音输入集成
- [ ] TTS语音输出实现
- [ ] 本地对话历史存储
- [ ] 会话管理功能

### Phase 3: 优化完善（1-2周）
- [ ] 界面美化和响应式适配
- [ ] 性能优化（特别针对树莓派）
- [ ] 错误处理和用户体验改进
- [ ] 设置界面和个性化选项

### Phase 4: 扩展功能（2-3周）
- [ ] 主题系统
- [ ] 数据导入导出
- [ ] 高级设置选项
- [ ] 日志和调试功能

## 🔧 系统要求

### 最低要求
- **硬件：** 树莓派4B (4GB RAM推荐)
- **系统：** Ubuntu 20.04 LTS 或更高版本
- **Python：** 3.9+
- **存储：** 至少1GB可用空间

### 推荐配置
- **硬件：** 树莓派4B (8GB RAM)
- **存储：** 高速SD卡或SSD
- **网络：** 稳定的网络连接（用于API调用）
- **音频：** USB麦克风和扬声器

## 📦 项目依赖

### 核心依赖
- **PyQt6** (>=6.5.0) - 跨平台GUI框架
- **aiohttp** (>=3.8.0) - 异步HTTP客户端
- **openai** (>=1.0.0) - OpenAI API官方客户端
- **pyttsx3** (>=2.90) - 文本转语音引擎
- **SpeechRecognition** (>=3.10.0) - 语音识别库
- **aiosqlite** (>=0.19.0) - 异步SQLite数据库

### 音频处理
- **pyaudio** (>=0.2.11) - 音频I/O处理
- **soundfile** (>=0.12.1) - 音频文件格式支持
- **numpy** (>=1.24.0) - 数值计算支持

### 系统工具
- **toml** (>=0.10.2) - 配置文件解析
- **loguru** (>=0.7.0) - 现代化日志系统
- **psutil** (>=5.9.0) - 系统资源监控
- **qdarkstyle** (>=3.2.0) - 深色主题样式

### 开发工具（可选）
- **pytest** (>=7.4.0) - 单元测试框架
- **pytest-qt** (>=4.2.0) - PyQt测试支持
- **black** (>=23.0.0) - 代码格式化
- **flake8** (>=6.0.0) - 代码质量检查

## 🚀 快速开始

### 系统依赖安装（Ubuntu/树莓派）
```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 安装音频系统依赖
sudo apt install -y portaudio19-dev python3-pyaudio
sudo apt install -y espeak espeak-data libespeak1 libespeak-dev
sudo apt install -y flac libasound2-dev

# 安装Qt6依赖和开发工具
sudo apt install -y python3-pyqt6 python3-pyqt6.qtmultimedia
sudo apt install -y qt6-tools-dev qt6-tools-dev-tools qtcreator

# 安装构建工具（如果需要编译某些包）
sudo apt install -y build-essential python3-dev
```

### Python环境准备
```bash
# 安装uv包管理器
curl -LsSf https://astral.sh/uv/install.sh | sh

# 克隆项目
git clone <repository-url>
cd RPChat

# 创建虚拟环境并安装依赖
uv venv
source .venv/bin/activate

# 生产环境安装
uv pip install -r requirements.txt

# 开发环境安装（包含测试、调试工具）
uv pip install -r requirements-dev.txt
```

### 开发环境配置
```bash
# 安装pre-commit钩子（推荐）
pre-commit install

# 代码格式化
black .
isort .

# 代码质量检查
flake8 .
mypy .

# 运行测试
pytest tests/

# 生成测试覆盖率报告
pytest --cov=. --cov-report=html
```

### 树莓派特殊配置
```bash
# 树莓派音频配置
sudo raspi-config  # 启用音频接口

# 配置音频权限
sudo usermod -a -G audio $USER

# 重启后生效
sudo reboot
```

### 配置设置
1. 复制配置模板：`cp config/config.template.toml config/config.toml`
2. 编辑配置文件，设置API密钥和端点
3. 配置音频设备（如果使用语音功能）

### 运行应用
```bash
python main.py
```

## 🔧 依赖管理

### 安装策略
- **生产环境：** 使用 `requirements.txt` 仅安装核心运行依赖
- **开发环境：** 使用 `requirements-dev.txt` 安装完整开发工具链
- **最小化安装：** 针对树莓派可选择性安装部分功能依赖

### 版本管理
```bash
# 更新所有依赖到最新版本
uv pip install --upgrade -r requirements.txt

# 生成当前环境的精确版本锁定文件
uv pip freeze > requirements.lock

# 检查依赖安全漏洞
safety check

# 清理未使用的依赖
pip-autoremove -y
```

### 树莓派优化安装
```bash
# 最小化安装（仅文本对话功能）
uv pip install PyQt6 aiohttp openai toml aiosqlite loguru

# 添加语音功能
uv pip install pyttsx3 SpeechRecognition pyaudio

# 完整功能安装
uv pip install -r requirements.txt
```

### 依赖问题排查
```bash
# 检查依赖冲突
pip check

# 查看依赖树
pipdeptree

# 重新安装损坏的包
uv pip install --force-reinstall package_name
```

## 📁 配置文件

### API配置
- 支持OpenAI官方API
- 支持本地部署的兼容API（如Ollama、vLLM等）
- 可配置模型名称、温度、最大tokens等参数

### 音频配置
- 语音识别语言设置
- TTS语音选择和语速
- 音频设备选择

## 🤝 贡献指南

1. Fork项目仓库
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -am 'Add some feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 提交Pull Request

## 📝 开发注意事项

### 性能优化
- 针对树莓派的内存和CPU限制进行优化
- 使用异步编程避免界面卡顿
- 合理使用缓存减少API调用

### 开发环境适配
- **直接在树莓派开发：** 通过SSH连接进行远程开发
- **ARM64架构限制：** 某些包（如PyQt6-tools）需要使用系统包替代
- **性能考量：** 开发时注意树莓派的内存和CPU限制
- **音频组件：** 确保音频设备在SSH会话中正确配置

### 用户体验
- 响应式界面设计
- 清晰的错误提示和状态反馈
- 快捷键支持

## ❓ 常见问题

### 依赖安装问题

**Q: PyAudio安装失败怎么办？**
```bash
# Ubuntu/树莓派解决方案
sudo apt install portaudio19-dev python3-pyaudio
uv pip install --global-option="build_ext" --global-option="-I/usr/local/include" --global-option="-L/usr/local/lib" pyaudio
```

**Q: 树莓派上PyQt6安装很慢？**
```bash
# 使用系统包代替pip安装
sudo apt install python3-pyqt6 python3-pyqt6.qtmultimedia
# 然后在虚拟环境中创建符号链接
```

**Q: 音频设备识别不到？**
```bash
# 检查音频设备
arecord -l
aplay -l

# 测试音频录制
arecord -d 5 test.wav
aplay test.wav
```

### 性能优化问题

**Q: 树莓派运行卡顿？**
- 增加虚拟内存：`sudo dphys-swapfile swapoff && sudo dphys-swapfile swapon`
- 关闭不必要的后台服务
- 使用轻量级TTS引擎
- 减少并发请求数量

**Q: 语音识别延迟高？**
- 优先使用本地语音识别
- 调整音频采样率和缓冲区大小
- 使用更快的网络连接

### 开发环境问题

**Q: 通过SSH在树莓派上开发GUI应用？**
```bash
# 启用X11转发（在Mac终端中连接）
ssh -X user@raspberry_pi_ip

# 或者在树莓派上使用虚拟显示
sudo apt install xvfb
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 &
python main.py

# 如果有物理显示器连接到树莓派
export DISPLAY=:0
python main.py
```

**Q: PyQt6-tools安装失败怎么办？**
```bash
# 在ARM64架构（树莓派）上使用系统包
sudo apt install qt6-tools-dev qt6-tools-dev-tools qtcreator

# 验证Qt Designer是否可用
which designer-qt6
```

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🔗 相关链接

- [PyQt6 文档](https://doc.qt.io/qtforpython/)
- [OpenAI API 文档](https://platform.openai.com/docs)
- [uv 包管理器](https://github.com/astral-sh/uv)

---

## 📂 项目文件结构

```
RPChat/
├── README.md              # 项目说明文档
├── requirements.txt       # 生产环境依赖
├── requirements-dev.txt   # 开发环境依赖
├── LICENSE               # 开源许可证
├── .gitignore           # Git忽略文件
├── main.py              # 应用程序入口（待创建）
├── config/              # 配置文件目录（待创建）
│   ├── config.template.toml
│   └── config.toml
├── core/                # 核心业务逻辑（待创建）
├── ui/                  # 用户界面（待创建）
├── utils/               # 工具函数（待创建）
├── resources/           # 资源文件（待创建）
├── tests/               # 测试代码（待创建）
└── docs/                # 文档（待创建）
```

**注意：** 本项目专门针对树莓派4B进行优化，在其他平台上可能需要调整配置参数。

