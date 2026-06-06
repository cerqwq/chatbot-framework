"""
Chatbot Framework - 多渠道聊天机器人框架
支持：Web、微信、Telegram、Discord
"""

import json
import os
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class Channel(Enum):
    """渠道"""
    WEB = "web"
    WECHAT = "wechat"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    API = "api"


@dataclass
class Message:
    """消息"""
    id: str
    channel: Channel
    user_id: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


@dataclass
class Response:
    """响应"""
    content: str
    channel: Channel
    metadata: Dict = field(default_factory=dict)


class ChatbotEngine:
    """
    聊天机器人引擎
    支持：多渠道、插件系统、上下文管理
    """

    def __init__(self, name: str = "ChatBot", model: str = "mimo-v2.5-pro", api_key: str = None, base_url: str = None):
        self.name = name
        self.model = model
        self.conversations: Dict[str, List[Message]] = {}
        self.plugins: List[Callable] = []
        self.system_prompt: str = "你是一个智能助手，友好、专业、有帮助。"

        if OPENAI_AVAILABLE:
            self.client = OpenAI(
                api_key=api_key or os.environ.get('OPENAI_API_KEY', ''),
                base_url=base_url or os.environ.get('OPENAI_BASE_URL', 'https://api.xiaomimimo.com/v1')
            )
        else:
            self.client = None

    def set_system_prompt(self, prompt: str):
        """设置系统提示"""
        self.system_prompt = prompt

    def add_plugin(self, plugin: Callable):
        """添加插件"""
        self.plugins.append(plugin)

    def process(self, message: Message) -> Response:
        """处理消息"""
        # 存储消息
        if message.user_id not in self.conversations:
            self.conversations[message.user_id] = []
        self.conversations[message.user_id].append(message)

        # 执行插件
        for plugin in self.plugins:
            try:
                result = plugin(message)
                if result:
                    return Response(
                        content=result,
                        channel=message.channel,
                        metadata={"source": "plugin"}
                    )
            except Exception as e:
                print(f"Plugin error: {e}")

        # LLM响应
        if self.client:
            response_content = self._generate_response(message)
        else:
            response_content = f"收到: {message.content}"

        return Response(
            content=response_content,
            channel=message.channel,
            metadata={"source": "llm"}
        )

    def _generate_response(self, message: Message) -> str:
        """生成LLM响应"""
        # 构建消息历史
        messages = [{"role": "system", "content": self.system_prompt}]

        # 添加对话历史
        history = self.conversations.get(message.user_id, [])[-10:]
        for msg in history:
            role = "user" if msg.channel != Channel.API else "assistant"
            messages.append({"role": role, "content": msg.content})

        messages.append({"role": "user", "content": message.content})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"抱歉，处理出错了: {e}"

    def get_history(self, user_id: str, limit: int = 20) -> List[Dict]:
        """获取对话历史"""
        history = self.conversations.get(user_id, [])[-limit:]
        return [
            {
                "id": msg.id,
                "content": msg.content,
                "channel": msg.channel.value,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in history
        ]

    def clear_history(self, user_id: str):
        """清空对话历史"""
        self.conversations[user_id] = []

    def get_stats(self) -> Dict:
        """获取统计"""
        total_users = len(self.conversations)
        total_messages = sum(len(msgs) for msgs in self.conversations.values())
        return {
            "name": self.name,
            "model": self.model,
            "total_users": total_users,
            "total_messages": total_messages,
            "plugins_count": len(self.plugins)
        }


class WebChatbot(ChatbotEngine):
    """Web聊天机器人"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.channel = Channel.WEB

    def create_app(self):
        """创建Flask应用"""
        try:
            from flask import Flask, request, jsonify, render_template_string

            app = Flask(__name__)

            HTML_TEMPLATE = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>{{ name }}</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                    .chat-box { height: 400px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; }
                    .message { margin: 10px 0; padding: 8px; border-radius: 5px; }
                    .user { background: #e3f2fd; text-align: right; }
                    .bot { background: #f5f5f5; }
                    input[type=text] { width: 80%; padding: 10px; }
                    button { padding: 10px 20px; }
                </style>
            </head>
            <body>
                <h1>{{ name }}</h1>
                <div class="chat-box" id="chatBox"></div>
                <input type="text" id="userInput" placeholder="输入消息..." onkeypress="if(event.key==='Enter')sendMessage()">
                <button onclick="sendMessage()">发送</button>
                <script>
                    function sendMessage() {
                        const input = document.getElementById('userInput');
                        const message = input.value.trim();
                        if (!message) return;

                        addMessage('user', message);
                        input.value = '';

                        fetch('/api/chat', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({message: message, user_id: 'web_user'})
                        })
                        .then(r => r.json())
                        .then(data => addMessage('bot', data.response));
                    }

                    function addMessage(role, content) {
                        const chatBox = document.getElementById('chatBox');
                        const div = document.createElement('div');
                        div.className = 'message ' + role;
                        div.textContent = content;
                        chatBox.appendChild(div);
                        chatBox.scrollTop = chatBox.scrollHeight;
                    }
                </script>
            </body>
            </html>
            """

            @app.route('/')
            def index():
                return render_template_string(HTML_TEMPLATE, name=self.name)

            @app.route('/api/chat', methods=['POST'])
            def chat():
                data = request.json
                message = Message(
                    id=f"msg_{int(datetime.now().timestamp() * 1000)}",
                    channel=Channel.WEB,
                    user_id=data.get('user_id', 'anonymous'),
                    content=data.get('message', '')
                )
                response = self.process(message)
                return jsonify({"response": response.content})

            return app
        except ImportError:
            return None


def create_chatbot(**kwargs) -> ChatbotEngine:
    """创建聊天机器人"""
    return ChatbotEngine(**kwargs)


def create_web_chatbot(**kwargs) -> WebChatbot:
    """创建Web聊天机器人"""
    return WebChatbot(**kwargs)


if __name__ == "__main__":
    bot = create_web_chatbot(name="My ChatBot")

    print("Chatbot Framework")
    print(f"Stats: {bot.get_stats()}")
    print()

    app = bot.create_app()
    if app:
        print("Starting web server on http://localhost:5000")
        app.run(host='0.0.0.0', port=5000)
    else:
        print("Flask not installed")
