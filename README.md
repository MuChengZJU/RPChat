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
- [x] 基本的PyQt6应用框架
- [x] OpenAI API客户端实现
- [x] 简单的文本对话界面
- [x] 基础配置管理系统

### Phase 2: 核心功能（2-3周）✅
- [x] 完整的对话界面设计
- [x] 语音输入集成
- [x] TTS语音输出实现
- [x] 本地对话历史存储
- [x] 会话管理功能

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

## 🚀 快速启动

```bash
# 使用便捷启动脚本（推荐）
./start_rpchat.sh

# 或者手动启动
source .venv/bin/activate

# 本地显示器运行
export DISPLAY=:0 && python main.py

# 虚拟显示运行（无头模式）
Xvfb :99 -screen 0 1024x768x24 & 
export DISPLAY=:99 && python main.py

# SSH X11转发运行
# 从客户端连接: ssh -X user@树莓派IP
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

---

## 🎉 Phase 2 核心功能已完成

### ✅ 新增实现功能

1. **完整的对话界面设计**
   - 现代化聊天界面，支持富文本消息显示
   - 实时消息状态指示器和进度条
   - 语音模式和文本模式切换
   - 响应式设计，适配不同屏幕尺寸

2. **语音输入集成**
   - Google语音识别API集成
   - 本地语音识别备用支持
   - 环境噪音自动校准
   - 实时语音状态反馈
   - 语音识别错误处理

3. **TTS语音输出实现**
   - 多引擎TTS支持（espeak、系统TTS）
   - 中文语音自动检测和配置
   - 异步语音播放，不阻塞界面
   - 语音播放状态管理
   - TTS参数可配置（语速、音量）

4. **本地对话历史存储**
   - SQLite数据库存储
   - 完整的对话和消息管理
   - 异步数据库操作
   - 数据自动备份和恢复
   - 对话搜索和过滤

5. **会话管理功能**
   - 对话列表展示和管理
   - 对话创建、删除、重命名
   - 对话搜索和排序
   - 右键菜单快捷操作
   - 对话统计信息显示

6. **工具函数模块**
   - 文本处理工具（清理、格式化、关键词提取）
   - 音频处理工具（格式转换、降噪、分割）
   - UI工具（异步任务管理、主题切换、消息框）

### 🔧 技术架构优化

- **异步编程模式**：全面采用异步处理，避免界面阻塞
- **模块化设计**：清晰的模块分离，易于维护和扩展
- **错误处理机制**：完善的异常处理和用户反馈
- **资源管理**：自动资源清理，防止内存泄漏
- **配置热更新**：支持运行时配置更新

### 🚀 快速启动

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行应用程序（现已支持完整功能）
python main.py
```

### 📝 使用说明

1. **基本对话**
   - 在文本框中输入消息，按Enter或点击"发送"
   - AI回复将自动显示在聊天区域
   - 支持多轮对话上下文保持

2. **语音功能**
   - 点击🎤按钮开始语音输入
   - 说话完成后自动识别并填入文本框
   - 启用语音模式后AI回复将自动播放

3. **会话管理**
   - 侧边栏显示所有历史对话
   - 点击对话标题切换到该对话
   - 右键对话可进行重命名、删除等操作
   - 使用搜索框快速查找对话

4. **设置配置**
   - 通过菜单"工具 > 设置"调整各项参数
   - 支持API配置、音频设置、界面主题等
   - 配置实时生效，无需重启

---

## 🎉 Phase 3 优化完善 (进行中)

### ✅ 用户体验改进

1. **优化语音聊天流程**
   - 新增语音打断功能，可随时点击"停止"按钮中断AI的语音播报。
   - 实现语音播放与录音的自动衔接，AI语音结束后会自动进入录音状态，无需手动点击。
   - 修复了语音播放和录音可能同时进行的冲突问题。

---

## 🎉 Phase 1 基础架构已完成

### ✅ 已实现功能

1. **应用程序框架**
   - 完整的PyQt6应用程序架构
   - 主窗口、菜单栏、工具栏、状态栏
   - 响应式布局和现代化界面设计
   - 深色主题支持

2. **配置管理系统**
   - TOML格式配置文件
   - 支持嵌套配置键访问
   - 配置模板和默认值管理
   - 运行时配置更新支持

3. **OpenAI API客户端**
   - 异步HTTP请求处理
   - 完整的OpenAI API兼容
   - 支持流式和非流式响应
   - 错误处理和连接测试
   - 本地API服务支持

4. **用户界面组件**
   - 聊天组件：消息显示和输入
   - 侧边栏组件：对话历史管理
   - 信号槽机制实现组件间通信
   - 基础的语音模式切换接口

5. **项目结构**
   - 清晰的模块化架构
   - 核心业务逻辑与界面分离
   - 完整的包管理和依赖配置
   - 日志系统集成

### 🚀 快速启动

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行应用程序
python main.py
```

### 📝 使用说明

1. **配置API密钥**：编辑 `config/config.toml` 文件，设置您的OpenAI API密钥
2. **GUI运行环境**：
   - 本地显示器：直接运行 `python main.py`
   - SSH环境：需要配置X11转发或使用本地显示
   - 虚拟显示：可使用Xvfb进行无头运行测试

### 🔄 下一步开发 (Phase 2)

接下来将实现：
- 真实的API调用集成
- 语音输入和TTS输出
- 对话历史的持久化存储
- 更丰富的用户界面功能

---

