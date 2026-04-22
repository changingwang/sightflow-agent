"""
视觉 Agent 核心 - 协调视觉识别和 IM 操作
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from pathlib import Path

from .scanner import ScreenScanner
from .ocr import OCR
from .drivers.base import BaseDriver


logger = logging.getLogger(__name__)


@dataclass
class Message:
    """消息对象"""
    sender: str
    text: str
    timestamp: Optional[float] = None
    is_unread: bool = False
    raw_data: Optional[Dict] = None


@dataclass
class UnreadNotification:
    """未读消息通知"""
    app: str
    contact: str
    count: int
    position: tuple  # (x, y) 红点位置


class VisionAgent:
    """
    视觉驱动的 IM Agent
    
    通过屏幕识别和模拟输入操作 IM 应用，无需 API。
    """
    
    def __init__(
        self,
        driver: Optional[BaseDriver] = None,
        ocr_enabled: bool = True,
        debug: bool = False,
    ):
        """
        初始化视觉 Agent
        
        Args:
            driver: IM 驱动器（WeChatDriver/WhatsAppDriver 等）
            ocr_enabled: 是否启用 OCR 文字识别
            debug: 调试模式
        """
        self.driver = driver
        self.ocr_enabled = ocr_enabled
        self.debug = debug
        
        # 初始化组件
        self.scanner = ScreenScanner()
        self.ocr = OCR() if ocr_enabled else None
        
        # 回调函数
        self._on_unread: Optional[Callable] = None
        self._on_message: Optional[Callable] = None
        
        # 运行状态
        self._running = False
    
    def attach_driver(self, driver: BaseDriver):
        """附加驱动器"""
        self.driver = driver
        logger.info(f"Attached driver: {driver.name}")
    
    def detect_unread(self) -> List[UnreadNotification]:
        """
        检测未读消息
        
        Returns:
            未读消息列表
        """
        if not self.driver:
            raise RuntimeError("No driver attached")
        
        # 截取屏幕
        screenshot = self.scanner.capture()
        
        # 识别未读红点
        unread_dots = self.scanner.detect_unread_dots(screenshot, app=self.driver.app_name)
        
        notifications = []
        for dot in unread_dots:
            # 提取联系人名称
            contact = self._extract_contact_near_dot(screenshot, dot)
            
            notifications.append(UnreadNotification(
                app=self.driver.app_name,
                contact=contact or "Unknown",
                count=dot.get("count", 1),
                position=dot["position"],
            ))
        
        logger.info(f"Detected {len(notifications)} unread notifications")
        return notifications
    
    def read_chat(self, contact: str, limit: int = 10) -> List[Message]:
        """
        读取聊天消息
        
        Args:
            contact: 联系人名称
            limit: 最多读取的消息数
        
        Returns:
            消息列表
        """
        if not self.driver:
            raise RuntimeError("No driver attached")
        
        # 打开聊天窗口
        self.driver.open_chat(contact)
        
        # 截取聊天区域
        screenshot = self.scanner.capture(region=self.driver.chat_region)
        
        # OCR 识别消息
        if self.ocr_enabled:
            text_regions = self.ocr.extract_text_regions(screenshot)
            
            messages = []
            for region in text_regions[:limit]:
                text = self.ocr.recognize(screenshot, region)
                if text:
                    messages.append(Message(
                        sender=contact,
                        text=text,
                    ))
            
            return messages
        
        return []
    
    def send_message(self, contact: str, text: str):
        """
        发送消息
        
        Args:
            contact: 联系人名称
            text: 消息内容
        """
        if not self.driver:
            raise RuntimeError("No driver attached")
        
        logger.info(f"Sending message to {contact}: {text[:50]}...")
        
        # 打开聊天窗口
        self.driver.open_chat(contact)
        
        # 输入消息
        self.driver.type_message(text)
        
        # 发送
        self.driver.send()
    
    def auto_reply(
        self,
        mode: str = "smart",
        interval: int = 5,
        keywords: Optional[Dict[str, str]] = None,
    ):
        """
        自动回复
        
        Args:
            mode: 回复模式 (smart/keyword/ai)
            interval: 检查间隔（秒）
            keywords: 关键词回复字典（keyword 模式）
        """
        logger.info(f"Starting auto-reply in {mode} mode")
        self._running = True
        
        while self._running:
            try:
                unread = self.detect_unread()
                
                for notification in unread:
                    if self._on_unread:
                        self._on_unread(notification)
                    
                    # 读取消息
                    messages = self.read_chat(notification.contact)
                    
                    if messages:
                        # 生成回复
                        reply = self._generate_reply(messages, mode, keywords)
                        
                        if reply:
                            self.send_message(notification.contact, reply)
                            
                            if self._on_message:
                                self._on_message(messages[-1], reply)
                
                asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Auto-reply error: {e}")
                if self.debug:
                    raise
        
        logger.info("Auto-reply stopped")
    
    def stop(self):
        """停止自动回复"""
        self._running = False
    
    def _extract_contact_near_dot(self, screenshot, dot: Dict) -> Optional[str]:
        """从红点附近提取联系人名称"""
        x, y = dot["position"]
        
        # 在红点左侧区域搜索文字
        region = (x - 150, y - 20, 150, 40)
        
        if self.ocr_enabled:
            return self.ocr.recognize(screenshot, region)
        
        return None
    
    def _generate_reply(
        self,
        messages: List[Message],
        mode: str,
        keywords: Optional[Dict[str, str]],
    ) -> Optional[str]:
        """生成回复"""
        if not messages:
            return None
        
        last_message = messages[-1].text.lower()
        
        if mode == "keyword" and keywords:
            for key, value in keywords.items():
                if key.lower() in last_message:
                    return value
        
        elif mode == "ai":
            # 调用 AI 生成回复
            return self._ai_reply(messages)
        
        elif mode == "smart":
            # 智能模式：简单问题 AI 回复，复杂问题跳过
            if len(last_message) < 50:
                return self._ai_reply(messages)
        
        return None
    
    def _ai_reply(self, messages: List[Message]) -> Optional[str]:
        """AI 生成回复"""
        # TODO: 集成本地 AI 模型
        # 暂时返回 None，表示不回复
        return None
    
    def on_unread(self, callback: Callable):
        """设置未读消息回调"""
        self._on_unread = callback
    
    def on_message(self, callback: Callable):
        """设置消息回调"""
        self._on_message = callback
