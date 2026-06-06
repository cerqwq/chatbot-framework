# 💬 Chatbot Framework

多渠道聊天机器人框架，支持Web、微信、Telegram、Discord。

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python" />
  <img src="https://img.shields.io/badge/Flask-Web-green?logo=flask" />
  <img src="https://img.shields.io/badge/License-MIT-yellow" />
</p>

## ✨ 特性

- 🌐 多渠道支持（Web、微信、Telegram）
- 🔌 插件系统
- 💾 对话历史管理
- 🤖 LLM集成
- 📊 统计分析

## 🚀 快速开始

```bash
pip install flask openai

python chatbot.py
```

## 📖 使用

```python
from chatbot import create_web_chatbot, Message, Channel

# 创建机器人
bot = create_web_chatbot(name="My Bot", model="mimo-v2.5-pro")

# 设置系统提示
bot.set_system_prompt("你是一个专业的客服助手")

# 添加插件
def keyword_plugin(message):
    if "帮助" in message.content:
        return "请问有什么可以帮助您的？"
    return None

bot.add_plugin(keyword_plugin)

# 启动Web服务
app = bot.create_app()
app.run(port=5000)
```

## 📁 项目结构

```
chatbot-framework/
├── chatbot.py     # 聊天机器人核心
└── README.md
```

## 📄 许可证

MIT License
