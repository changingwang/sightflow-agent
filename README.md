# 👁️ SightFlow Agent

**视觉驱动的通用 IM Agent - 让 AI 像人一样操作微信/WhatsApp**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![OpenClaw Compatible](https://img.shields.io/badge/OpenClaw-compatible-green)](https://github.com/openclaw/openclaw)
[![Hermes Compatible](https://img.shields.io/badge/Hermes-compatible-purple)](https://github.com/NousResearch/Hermes-Agent)

---

## 🎯 项目理念

**See the Workflow, Empower the Agent.**

抛弃危险的 API 和协议，完全基于视觉识别操作 IM 应用。像真人一样点击、输入、阅读聊天记录，零封号风险！

---

## 🌟 核心特性

### 🔒 零封号风险 RPA
- 不使用任何官方 API 或 Webhook
- 完全模拟真人操作：点击、输入、滚动
- 基于视觉识别，不注入任何代码

### 👁️ 先进视觉引擎
- 实时提取未读消息红点位置
- 识别聊天列表和消息气泡文字
- 支持复杂布局的 UI 解析

### 🤖 Agent 工作流
- 将聊天请求转换为可执行的工作流
- 支持本地 AI 编程控制
- 可视化节点编辑器

---

## 🚀 快速开始

### 安装

```bash
# 从 GitHub 安装
pip install git+https://github.com/soad666p/sightflow-agent.git

# 或克隆后本地安装
git clone https://github.com/soad666p/sightflow-agent.git
cd sightflow-agent
pip install -e .
```

### 基础用法

```python
from sightflow_agent import VisionAgent, WeChatDriver

# 创建视觉 Agent
agent = VisionAgent()

# 连接微信 (Windows/macOS)
driver = WeChatDriver()
driver.attach()

# 识别未读消息
unread = driver.detect_unread()
print(f"发现 {unread.count} 条未读消息")

# 读取消息
messages = driver.read_chat("联系人名称")
for msg in messages:
    print(f"{msg.sender}: {msg.text}")

# 发送消息
driver.send_message("联系人名称", "你好！")

# 使用 AI 自动回复
agent.auto_reply(mode="smart")
```

### 命令行使用

```bash
# 检测未读消息
sightflow unread --app wechat

# 读取指定聊天
sightflow read --app wechat --contact "豆哥"

# 发送消息
sightflow send --app wechat --contact "豆哥" --message "你好！"

# 启动自动回复
sightflow auto-reply --app wechat --mode smart

# 运行工作流
sightflow run --workflow my_workflow.yaml
```

---

## 📦 支持的 IM 应用

| 应用 | 平台 | 状态 | 功能 |
|------|------|------|------|
| 微信 (WeChat) | Windows/macOS | ✅ 支持 | 消息收发、未读检测、朋友圈 |
| WhatsApp | Windows/macOS | ✅ 支持 | 消息收发、群组管理 |
| Telegram Desktop | Windows/macOS/Linux | 🔄 测试中 | 消息收发 |
| QQ | Windows | 🔄 测试中 | 消息收发 |
| Discord | 全平台 | 📋 计划中 | 消息收发 |

---

## 🔧 核心模块

### 1. 视觉识别引擎

```python
from sightflow_agent.vision import ScreenScanner, UIElement

scanner = ScreenScanner()

# 截取屏幕
screenshot = scanner.capture()

# 识别 UI 元素
elements = scanner.detect_elements(screenshot, target="wechat_unread_dot")

# 提取文字
text = scanner.extract_text(screenshot, region=(x, y, w, h))
```

### 2. IM 驱动器

```python
from sightflow_agent.drivers import WeChatDriver, WhatsAppDriver

# 微信驱动
wechat = WeChatDriver()
wechat.attach()  # 附加到运行中的微信窗口
wechat.click_unread()  # 点击未读消息
wechat.get_chat_list()  # 获取聊天列表
```

### 3. 工作流引擎

```yaml
# workflows/auto_reply.yaml
name: 自动回复工作流
trigger:
  - type: unread_message
  - contact: "*"

actions:
  - action: read_message
    save_as: msg
  
  - action: ai_analyze
    input: "{{msg.text}}"
    save_as: response
  
  - action: send_reply
    text: "{{response}}"
```

### 4. Agent 集成

```python
# OpenClaw Skill
from sightflow_agent.skills import OpenClawWeChat

skill = OpenClawWeChat()
skill.send_message("豆哥", "任务已完成！")

# Hermes Agent Tool
from sightflow_agent.tools import WhatsAppTool

tool = WhatsAppTool()
tool.send_message(contact="Boss", message="Report ready!")
```

---

## 📁 项目结构

```
sightflow-agent/
├── src/
│   └── sightflow_agent/
│       ├── __init__.py
│       ├── agent.py           # 视觉 Agent 核心
│       ├── scanner.py         # 屏幕扫描器
│       ├── ocr.py             # OCR 文字识别
│       ├── drivers/
│       │   ├── base.py        # 基础驱动器
│       │   ├── wechat.py      # 微信驱动
│       │   └── whatsapp.py    # WhatsApp 驱动
│       ├── skills/
│       │   ├── openclaw.py    # OpenClaw 技能
│       │   └── hermes.py      # Hermes 工具
│       └── workflows/         # 工作流定义
├── tests/
├── examples/
├── workflows/
├── config/
└── docs/
```

---

## 🛠️ CLI 工具

```bash
# 初始化配置
sightflow init

# 检测未读消息
sightflow unread [--app wechat|whatsapp] [--count]

# 读取聊天
sightflow read --contact "名称" [--limit 10]

# 发送消息
sightflow send --contact "名称" --message "内容"

# 启动自动回复
sightflow auto-reply [--mode smart|keyword|ai]

# 运行工作流
sightflow run --workflow <file.yaml>

# 截图测试
sightflow screenshot [--region x,y,w,h]

# 校准视觉模型
sightflow calibrate --app wechat
```

---

## 🔐 安全说明

**为什么零封号风险？**

1. **无 API 调用** - 不请求任何官方接口
2. **无注入** - 不修改应用内存或代码
3. **纯视觉** - 只"看"屏幕，像真人一样
4. **模拟操作** - 使用系统级输入模拟

**注意事项：**
- 不要设置过快的回复频率
- 避免 24 小时不间断运行
- 敏感操作建议人工确认

---

## 🤝 与 Agent 框架集成

### OpenClaw

```python
# 安装技能
cp -r sightflow_agent/skills/openclaw ~/.openclaw/workspace/skills/

# 在 OpenClaw 中使用
from sightflow_wechat import send_message
send_message(contact="豆哥", message="报告完成！")
```

### Hermes Agent

```python
from sightflow_agent.tools import WeChatTool

tool = WeChatTool()
agent.add_tool(tool)
```

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## 🙏 致谢

- 灵感来自 [SightFlow](https://sightflow.dev/)
- [OpenClaw](https://github.com/openclaw/openclaw) - 本地 AI 自动化平台
- [Hermes Agent](https://github.com/NousResearch/Hermes-Agent) - Nous Research 的开源 Agent 框架

---

**用视觉赋能 Agent，让自动化更安全！** 👁️🤖
