"""
OpenClaw 技能集成 - 让 OpenClaw 调用 SightFlow
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class OpenClawWeChat:
    """
    OpenClaw 微信技能
    
    用法:
        skill = OpenClawWeChat()
        skill.send_message("豆哥", "任务完成！")
    """
    
    def __init__(self):
        from ..drivers import WeChatDriver
        from ..agent import VisionAgent
        
        self.driver = WeChatDriver()
        self.agent = VisionAgent(driver=self.driver)
        self._attached = False
    
    def _ensure_attached(self):
        """确保已附加到微信"""
        if not self._attached:
            self._attached = self.driver.attach()
            if not self._attached:
                logger.warning("Failed to attach to WeChat")
    
    def send_message(self, contact: str, message: str) -> Dict[str, Any]:
        """
        发送微信消息
        
        Args:
            contact: 联系人名称
            message: 消息内容
        
        Returns:
            {"success": bool, "error": str}
        """
        try:
            self._ensure_attached()
            
            if not self._attached:
                return {"success": False, "error": "无法连接到微信"}
            
            self.agent.send_message(contact, message)
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Send message error: {e}")
            return {"success": False, "error": str(e)}
    
    def read_messages(self, contact: str, limit: int = 10) -> Dict[str, Any]:
        """
        读取微信消息
        
        Args:
            contact: 联系人名称
            limit: 最多读取条数
        
        Returns:
            {"success": bool, "messages": [...], "error": str}
        """
        try:
            self._ensure_attached()
            
            if not self._attached:
                return {"success": False, "error": "无法连接到微信"}
            
            messages = self.agent.read_chat(contact, limit)
            
            return {
                "success": True,
                "messages": [{"sender": m.sender, "text": m.text} for m in messages],
            }
            
        except Exception as e:
            logger.error(f"Read messages error: {e}")
            return {"success": False, "error": str(e)}
    
    def check_unread(self) -> Dict[str, Any]:
        """
        检查未读消息
        
        Returns:
            {"success": bool, "unread": [...], "error": str}
        """
        try:
            self._ensure_attached()
            
            if not self._attached:
                return {"success": False, "error": "无法连接到微信"}
            
            unread = self.agent.detect_unread()
            
            return {
                "success": True,
                "unread": [
                    {"contact": n.contact, "count": n.count}
                    for n in unread
                ],
            }
            
        except Exception as e:
            logger.error(f"Check unread error: {e}")
            return {"success": False, "error": str(e)}


class OpenClawWhatsApp:
    """OpenClaw WhatsApp 技能"""
    
    def __init__(self):
        from ..drivers import WhatsAppDriver
        from ..agent import VisionAgent
        
        self.driver = WhatsAppDriver()
        self.agent = VisionAgent(driver=self.driver)
        self._attached = False
    
    def _ensure_attached(self):
        if not self._attached:
            self._attached = self.driver.attach()
    
    def send_message(self, contact: str, message: str) -> Dict[str, Any]:
        """发送 WhatsApp 消息"""
        try:
            self._ensure_attached()
            
            if not self._attached:
                return {"success": False, "error": "无法连接到 WhatsApp"}
            
            self.agent.send_message(contact, message)
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def read_messages(self, contact: str, limit: int = 10) -> Dict[str, Any]:
        """读取 WhatsApp 消息"""
        try:
            self._ensure_attached()
            
            if not self._attached:
                return {"success": False, "error": "无法连接到 WhatsApp"}
            
            messages = self.agent.read_chat(contact, limit)
            
            return {
                "success": True,
                "messages": [{"sender": m.sender, "text": m.text} for m in messages],
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
