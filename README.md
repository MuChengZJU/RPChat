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

## 🚀 快速开始

### 环境准备
```bash
# 安装uv包管理器
curl -LsSf https://astral.sh/uv/install.sh | sh

# 克隆项目
git clone <repository-url>
cd RPChat

# 创建虚拟环境并安装依赖
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 配置设置
1. 复制配置模板：`cp config/config.template.toml config/config.toml`
2. 编辑配置文件，设置API密钥和端点
3. 配置音频设备（如果使用语音功能）

### 运行应用
```bash
python main.py
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

### 跨平台兼容
- 确保在Mac开发环境和树莓派部署环境的兼容性
- 音频组件的跨平台适配
- 路径处理的操作系统差异

### 用户体验
- 响应式界面设计
- 清晰的错误提示和状态反馈
- 快捷键支持

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🔗 相关链接

- [PyQt6 文档](https://doc.qt.io/qtforpython/)
- [OpenAI API 文档](https://platform.openai.com/docs)
- [uv 包管理器](https://github.com/astral-sh/uv)

---

**注意：** 本项目专门针对树莓派4B进行优化，在其他平台上可能需要调整配置参数。

