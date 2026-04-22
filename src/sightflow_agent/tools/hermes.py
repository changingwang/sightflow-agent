"""
Hermes Agent 工具集成
"""

from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class WeChatTool:
    """
    Hermes Agent 微信工具
    """
    
    name = "wechat_tool"
    description = """
    发送和读取微信消息。
    支持功能：
    - send_message: 发送消息给指定联系人
    - read_messages: 读取聊天记录
    - check_unread: 检查未读消息
    """
    
    parameters = {
        "action": {
            "type": "str",
            "description": "操作类型 (send_message/read_messages/check_unread)"
        },
        "contact": {
            "type": "str",
            "description": "联系人名称",
            "required": False
        },
        "message": {
            "type": "str",
            "description": "消息内容（send_message 时必需）",
            "required": False
        },
        "limit": {
            "type": "int",
            "description": "最多读取条数",
            "required": False,
            "default": 10
        }
    }
    
    def __init__(self):
        self._driver = None
        self._agent = None
    
    def _get_agent(self):
        """懒加载 Agent"""
        if self._agent is None:
            from ..agent import VisionAgent
            from ..drivers import WeChatDriver
            
            self._driver = WeChatDriver()
            self._agent = VisionAgent(driver=self._driver)
        
        return self._agent
    
    def _run(self, **kwargs) -> Any:
        action = kwargs.get("action", "send_message")
        contact = kwargs.get("contact")
        message = kwargs.get("message")
        limit = kwargs.get("limit", 10)
        
        agent = self._get_agent()
        
        if action == "send_message":
            if not contact or not message:
                return {"error": "contact and message required"}
            
            agent.send_message(contact, message)
            return {"success": True}
        
        elif action == "read_messages":
            if not contact:
                return {"error": "contact required"}
            
            messages = agent.read_chat(contact, limit)
            return {
                "messages": [{"sender": m.sender, "text": m.text} for m in messages]
            }
        
        elif action == "check_unread":
            unread = agent.detect_unread()
            return {
                "unread": [{"contact": n.contact, "count": n.count} for n in unread]
            }
        
        else:
            return {"error": f"Unknown action: {action}"}
    
    async def _arun(self, **kwargs) -> Any:
        import asyncio
        return await asyncio.to_thread(self._run, **kwargs)


class WhatsAppTool:
    """Hermes Agent WhatsApp 工具"""
    
    name = "whatsapp_tool"
    description = "发送和读取 WhatsApp 消息"
    
    parameters = {
        "action": {"type": "str", "description": "操作类型"},
        "contact": {"type": "str", "description": "联系人名称", "required": False},
        "message": {"type": "str", "description": "消息内容", "required": False},
    }
    
    def __init__(self):
        self._agent = None
    
    def _get_agent(self):
        if self._agent is None:
            from ..agent import VisionAgent
            from ..drivers import WhatsAppDriver
            
            self._agent = VisionAgent(driver=WhatsAppDriver())
        
        return self._agent
    
    def _run(self, **kwargs) -> Any:
        action = kwargs.get("action", "send_message")
        contact = kwargs.get("contact")
        message = kwargs.get("message")
        
        agent = self._get_agent()
        
        if action == "send_message":
            agent.send_message(contact, message)
            return {"success": True}
        
        elif action == "read_messages":
            messages = agent.read_chat(contact)
            return {"messages": [{"sender": m.sender, "text": m.text} for m in messages]}
        
        return {"error": f"Unknown action: {action}"}
    
    async def _arun(self, **kwargs) -> Any:
        import asyncio
        return await asyncio.to_thread(self._run, **kwargs)


# 导出工具实例
wechat_tool = WeChatTool()
whatsapp_tool = WhatsAppTool()
